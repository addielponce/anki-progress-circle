# Anki Progress Circle
# A simple Anki add-on that displays a circular progress overlay

# Copyright (C) 2026 Addiel Ponce

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import math
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, Optional

from aqt import gui_hooks, mw
from aqt.qt import QDialog, QMenu, Qt, QVBoxLayout, QWebEngineView

from . import settings_gui

mw.addonManager.setConfigAction(__name__, lambda: settings_gui.open_settings(__name__))


def get_config() -> dict[str, Any]:
    return mw.addonManager.getConfig(__name__)


HTML = Template((Path(__file__).parent / "html_circle.html").read_text())


class ProgressWindow(QDialog):
    VIEWBOX_SIZE = 100
    VIEWBOX_CENTER = VIEWBOX_SIZE / 2
    RADIUS_PADDING = 1

    def __init__(self, parent: Optional[object] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Progress circle")

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.web = QWebEngineView()
        self.web.page().setBackgroundColor(Qt.GlobalColor.transparent)
        layout.addWidget(self.web)
        self.setLayout(layout)

        self._page_loaded = False
        self.web.page().loadFinished.connect(self._on_page_loaded)
        self._pending_js: list[str] = []

        self._initial_render(0)

    def _on_page_loaded(self, ok: bool) -> None:
        self._page_loaded = True
        for js in self._pending_js:
            self.web.page().runJavaScript(js)
        self._pending_js.clear()

    def _run_js(self, js: str) -> None:
        if self._page_loaded:
            self.web.page().runJavaScript(js)
        else:
            self._pending_js.append(js)

    def _compute_svg_params(self, config: dict[str, Any]) -> tuple[float, float]:
        main_stroke_width = config.get("main_circle_stroke_width", 8)
        back_stroke_width = config.get("back_circle_stroke_width", 8)
        max_stroke_width = max(main_stroke_width, back_stroke_width)
        radius = max(
            1,
            self.VIEWBOX_CENTER - (max_stroke_width / 2) - self.RADIUS_PADDING,
        )
        circumference = 2 * math.pi * radius
        return radius, circumference

    def _initial_render(self, percent: float) -> None:
        config = get_config()
        radius, circumference = self._compute_svg_params(config)
        dash_length = circumference * (percent / 100)

        main_stroke_width = config.get("main_circle_stroke_width", 8)
        back_stroke_width = config.get("back_circle_stroke_width", 8)

        is_empty = percent == 0 and config["hide_main_circle_at_zero"]
        main_color_opacity = 0 if is_empty else (config["main_color_opacity"] / 100)

        mask = (
            "url(#mask)" if (config["mask_circles"] and main_color_opacity != 0) else ""
        )

        self._page_loaded = False
        self._pending_js.clear()
        self.web.setHtml(
            HTML.safe_substitute(
                radius=radius,
                circumference=circumference,
                dash_length=dash_length,
                main_color=config["main_color"],
                back_color=config["back_color"],
                main_color_opacity=main_color_opacity,
                back_color_opacity=config["back_color_opacity"] / 100,
                main_stroke_width=main_stroke_width,
                back_stroke_width=back_stroke_width,
                stroke_linecap=config["stroke_linecap"],
                mask=mask,
            )
        )

    def update_progress(self, percent: float) -> None:
        config = get_config()
        _, circumference = self._compute_svg_params(config)
        dash_length = circumference * (percent / 100)

        is_empty = percent == 0 and config["hide_main_circle_at_zero"]
        main_color_opacity = 0 if is_empty else (config["main_color_opacity"] / 100)

        mask = (
            "url(#mask)" if (config["mask_circles"] and main_color_opacity != 0) else ""
        )

        self._run_js(
            f"updateCircle({dash_length}, {circumference}, {main_color_opacity}, '{mask}')"
        )

    def full_redraw(self, percent: float) -> None:
        self._initial_render(percent)


@dataclass
class ProgressState:
    progress_window: Optional[ProgressWindow] = None

    # Tracks the starting card count and completed count per deck for the current session.
    deck_goal: dict[int, int] = field(default_factory=dict)
    deck_done: dict[int, int] = field(default_factory=dict)

    reviews_since_update: int = 0
    last_render_done: Optional[int] = None
    last_render_total: Optional[int] = None


_state = ProgressState()


def get_current_progress() -> tuple[int, int, float]:
    if not mw.col:
        return 0, 0, 0.0

    deck_id = mw.col.decks.get_current_id()

    queued = mw.col.sched.get_queued_cards(fetch_limit=1)
    remaining = queued.new_count + queued.learning_count + queued.review_count

    if deck_id not in _state.deck_goal:
        _state.deck_goal[deck_id] = remaining
        _state.deck_done[deck_id] = 0
    else:
        _state.deck_done[deck_id] = _state.deck_goal[deck_id] - remaining

        # If remaining exceeds the recorded goal, new cards were added mid-session.
        if remaining > _state.deck_goal[deck_id]:
            _state.deck_goal[deck_id] = remaining
            _state.deck_done[deck_id] = 0

    total = _state.deck_goal[deck_id]
    done = _state.deck_done[deck_id]
    percent = (done / total * 100) if total > 0 else 0.0

    return done, total, percent


def toggle_progress_window() -> None:
    if _state.progress_window is None:
        _state.progress_window = ProgressWindow(None)

    done, total, percent = get_current_progress()
    _state.progress_window.update_progress(percent)
    _mark_rendered_progress(done, total)

    if not _state.progress_window.isVisible():
        _state.progress_window.showMaximized()
    else:
        _state.progress_window.close()


def _mark_rendered_progress(done: int, total: int) -> None:
    _state.reviews_since_update = 0
    _state.last_render_done = done
    _state.last_render_total = total


def refresh_overlay() -> None:
    if _state.progress_window is not None and _state.progress_window.isVisible():
        done, total, percent = get_current_progress()
        _state.progress_window.update_progress(percent)
        _mark_rendered_progress(done, total)


def full_redraw_overlay() -> None:
    """Re-render the overlay from scratch (needed after appearance config changes)."""
    if _state.progress_window is not None and _state.progress_window.isVisible():
        done, total, percent = get_current_progress()
        _state.progress_window.full_redraw(percent)
        _mark_rendered_progress(done, total)


def on_state_change(state: str, old_state: str) -> None:
    if state in ("deckBrowser", "overview", "review"):
        refresh_overlay()


def on_review_question_shown(card: Any) -> None:
    if _state.progress_window is None or not _state.progress_window.isVisible():
        return

    done, total, percent = get_current_progress()

    config = get_config()
    update_mode = (config.get("update_every_mode", "cards") or "cards").strip().lower()
    if update_mode == "percent":
        percent_of_total = int(config.get("update_every_percent_total", 1) or 1)
        percent_of_total = max(1, min(100, percent_of_total))
        update_every = (
            max(1, int(round(total * (percent_of_total / 100.0)))) if total > 0 else 1
        )
    else:
        update_every = int(config.get("update_every_n_reviews", 1) or 1)
        if update_every < 1:
            update_every = 1

    # Force an immediate update only if the last-rendered percent would otherwise
    # be higher than the true percent (avoids misleading UI when progress drops).
    force = False
    if _state.last_render_done is None or _state.last_render_total is None:
        force = True
    else:
        force_enabled = bool(config.get("force_update_on_decrease", True))
        if force_enabled:
            if _state.last_render_total > 0 and total > 0:
                force = (_state.last_render_done * total) > (
                    done * _state.last_render_total
                )
            elif _state.last_render_total > 0 and total == 0:
                force = _state.last_render_done != 0

    _state.reviews_since_update += 1
    if force or _state.reviews_since_update >= update_every:
        _state.progress_window.update_progress(percent)
        _mark_rendered_progress(done, total)


def add_menu_entry() -> None:
    menu = QMenu("Circular progress ⭕", mw)
    mw.form.menuTools.addMenu(menu)
    toggle_action = menu.addAction("Toggle circular progress")
    toggle_action.triggered.connect(toggle_progress_window)

    menu.addSeparator()
    settings_action = menu.addAction("Circle settings...")
    settings_action.triggered.connect(lambda: settings_gui.open_settings(__name__))


def open_on_startup() -> None:
    if get_config().get("open_on_startup", False):
        toggle_progress_window()


gui_hooks.state_did_change.append(on_state_change)
gui_hooks.reviewer_did_show_question.append(on_review_question_shown)
gui_hooks.main_window_did_init.append(add_menu_entry)
gui_hooks.main_window_did_init.append(open_on_startup)
