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


from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import QDialog, QMenu, Qt, QVBoxLayout, QWebEngineView

from . import settings_gui

mw.addonManager.setConfigAction(__name__, lambda: settings_gui.open_settings(__name__))


def get_config():
    return mw.addonManager.getConfig(__name__)


HTML = (Path(__file__).parent / "html_circle.html").read_text()

RADIUS = 45
CIRCUMFERENCE = 2 * 3.1416 * RADIUS


class ProgressWindow(QDialog):
    def __init__(self, parent=None):
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

        self.update_progress(0, 0, 0)

    def update_progress(self, done, total, percent):
        config = get_config()

        dash_length = CIRCUMFERENCE * (percent / 100)

        is_empty = percent == 0 and config["hide_main_circle_at_zero"]
        main_color_opacity = 0 if is_empty else (config["main_color_opacity"] / 100)

        # The mask prevents the two circles from alpha-compositing where they overlap.
        # It must be disabled when the main circle is invisible to avoid a rendering artifact.
        mask = (
            "url(#mask)" if (config["mask_circles"] and main_color_opacity != 0) else ""
        )

        self.web.setHtml(
            HTML.format(
                radius=RADIUS,
                circumference=CIRCUMFERENCE,
                dash_length=dash_length,
                main_color=config["main_color"],
                back_color=config["back_color"],
                main_color_opacity=main_color_opacity,
                back_color_opacity=config["back_color_opacity"] / 100,
                stroke_linecap=config["stroke_linecap"],
                mask=mask,
            )
        )


progress_window = None

# Tracks the starting card count and completed count per deck for the current session.
deck_goal: dict = {}
deck_done: dict = {}


def get_current_progress():
    if not mw.col:
        return 0, 0, 0.0

    deck_id = mw.col.decks.get_current_id()

    queued = mw.col.sched.get_queued_cards(fetch_limit=1)
    remaining = queued.new_count + queued.learning_count + queued.review_count

    if deck_id not in deck_goal:
        deck_goal[deck_id] = remaining
        deck_done[deck_id] = 0
    else:
        deck_done[deck_id] = deck_goal[deck_id] - remaining

        # If remaining exceeds the recorded goal, new cards were added mid-session.
        if remaining > deck_goal[deck_id]:
            deck_goal[deck_id] = remaining
            deck_done[deck_id] = 0

    total = deck_goal[deck_id]
    done = deck_done[deck_id]
    percent = (done / total * 100) if total > 0 else 0.0

    return done, total, percent


def toggle_progress_window():
    global progress_window

    if progress_window is None:
        progress_window = ProgressWindow(None)

    done, total, percent = get_current_progress()
    progress_window.update_progress(done, total, percent)

    if not progress_window.isVisible():
        progress_window.showMaximized()
    else:
        progress_window.close()


def update_progress():
    if progress_window is not None and progress_window.isVisible():
        done, total, percent = get_current_progress()
        progress_window.update_progress(done, total, percent)

        # TODO: Update every X number of cards.


def on_state_change(state, old_state):
    if state in ("deckBrowser", "overview", "review"):
        update_progress()


def add_menu_entry():
    menu = QMenu("Circular progress ⭕", mw)
    mw.form.menuTools.addMenu(menu)
    action = menu.addAction("Toggle circular progress")
    action.triggered.connect(toggle_progress_window)


gui_hooks.state_did_change.append(on_state_change)
gui_hooks.reviewer_did_show_question.append(lambda card: update_progress())
gui_hooks.main_window_did_init.append(add_menu_entry)
