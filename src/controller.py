from typing import Literal, NamedTuple

from anki.cards import Card
from aqt import gui_hooks, mw
from aqt.qt import QMenu, QTimer

from .config import Config, UpdateMode
from .overlay import ProgressOverlay


class DeckProgress(NamedTuple):
    done: int
    total: int
    percent: float


class AddonController:
    def __init__(self, package_name: str) -> None:
        self._package_name = package_name
        self._overlay: ProgressOverlay | None = None
        self._mode: Literal["review", "timer"] = "review"

        self._deck_goal: dict[int, int] = {}
        self._deck_done: dict[int, int] = {}

        self._reviews_since_update: int = 0
        self._last_render_done: int | None = None
        self._last_render_total: int | None = None

        self._timer: QTimer | None = None

    def load_config(self) -> Config:
        return Config.from_dict(mw.addonManager.getConfig(self._package_name))

    def save_config(self, config: Config) -> None:
        mw.addonManager.writeConfig(self._package_name, config.to_dict())

    def load_defaults(self) -> Config | None:
        raw = mw.addonManager.addonConfigDefaults(self._package_name)
        return Config.from_dict(raw) if raw else None

    def get_current_progress(self) -> DeckProgress:
        if not mw.col:
            return DeckProgress(0, 0, 0.0)

        deck_id = mw.col.decks.get_current_id()
        queued = mw.col.sched.get_queued_cards(fetch_limit=1)
        remaining = queued.new_count + queued.learning_count + queued.review_count

        if deck_id not in self._deck_goal:
            self._deck_goal[deck_id] = remaining
            self._deck_done[deck_id] = 0
        else:
            self._deck_done[deck_id] = self._deck_goal[deck_id] - remaining

            # New cards were added mid-session; reset the baseline.
            if remaining > self._deck_goal[deck_id]:
                self._deck_goal[deck_id] = remaining
                self._deck_done[deck_id] = 0

        total = self._deck_goal[deck_id]
        done = self._deck_done[deck_id]
        percent = (done / total * 100) if total > 0 else 0.0

        return DeckProgress(done, total, percent)

    def _mark_rendered(self, done: int, total: int) -> None:
        self._reviews_since_update = 0
        self._last_render_done = done
        self._last_render_total = total

    def _update_overlay(self) -> None:
        if self._overlay is None or not self._overlay.isVisible():
            return
        done, total, percent = self.get_current_progress()
        self._overlay.update_progress(self.load_config(), percent)
        self._mark_rendered(done, total)

    def _full_redraw_overlay(self) -> None:
        if self._overlay is None or not self._overlay.isVisible():
            return
        done, total, percent = self.get_current_progress()
        self._overlay.render(self.load_config(), percent)
        self._mark_rendered(done, total)

    def toggle_overlay(self) -> None:
        if self._overlay is None:
            self._overlay = ProgressOverlay(None)

        if self._overlay.isVisible():
            self._overlay.close()
        else:
            config = self.load_config()
            done, total, percent = self.get_current_progress()
            self._overlay.render(config, percent)
            self._mark_rendered(done, total)
            self._overlay.showMaximized()

    def _ensure_overlay_visible(self) -> None:
        if self._overlay is None:
            self._overlay = ProgressOverlay(None)
        if not self._overlay.isVisible():
            config = self.load_config()
            done, total, percent = self.get_current_progress()
            self._overlay.render(config, percent)
            self._mark_rendered(done, total)
            self._overlay.showMaximized()

    def _should_force_update(self, config: Config, done: int, total: int) -> bool:
        if self._last_render_done is None or self._last_render_total is None:
            return True
        if not config.force_update_on_decrease:
            return False
        # Cross-multiply to compare fractions without floating-point error.
        if self._last_render_total > 0 and total > 0:
            return (self._last_render_done * total) > (done * self._last_render_total)
        if self._last_render_total > 0 and total == 0:
            return self._last_render_done != 0
        return False

    def _compute_update_interval(self, config: Config, total: int) -> int:
        if config.update_every_mode == UpdateMode.PERCENT:
            pct = max(1, min(100, config.update_every_percent_total))
            return max(1, int(round(total * (pct / 100.0)))) if total > 0 else 1
        return max(1, config.update_every_n_reviews)

    # hooks

    def on_state_change(self, state: str, old_state: str) -> None:
        if self._mode == "timer":
            return
        if state in ("deckBrowser", "overview", "review"):
            self._update_overlay()

    def on_review_shown(self, card: Card) -> None:
        if self._mode == "timer":
            return
        if self._overlay is None or not self._overlay.isVisible():
            return

        done, total, percent = self.get_current_progress()
        config = self.load_config()

        update_interval = self._compute_update_interval(config, total)
        force = self._should_force_update(config, done, total)

        self._reviews_since_update += 1
        if force or self._reviews_since_update >= update_interval:
            self._overlay.update_progress(config, percent)
            self._mark_rendered(done, total)

    # Timer

    def start_timer(self) -> None:
        config = self.load_config()
        duration_seconds = max(1, config.timer_duration_minutes) * 60

        self._ensure_overlay_visible()
        self._mode = "timer"
        self._overlay.start_timer(config, duration_seconds)

        if self._timer is not None:
            self._timer.stop()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer_finished)
        self._timer.start(duration_seconds * 1000)

    def stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        if self._overlay is not None:
            self._overlay.stop_timer()
        self._mode = "review"
        self._update_overlay()

    def _on_timer_finished(self) -> None:
        self._timer = None
        self._mode = "review"
        self._update_overlay()

    # Menu / settings

    def _add_menu(self) -> None:
        menu = QMenu("Circular progress ⭕", mw)
        mw.form.menuTools.addMenu(menu)

        menu.addAction("Toggle circular progress").triggered.connect(self.toggle_overlay)
        menu.addSeparator()
        menu.addAction("Start timer").triggered.connect(self.start_timer)
        menu.addAction("Stop timer").triggered.connect(self.stop_timer)
        menu.addSeparator()
        menu.addAction("Circle settings...").triggered.connect(self._open_settings)

    def _open_settings(self) -> None:
        from .settings_gui import SettingsDialog

        config = self.load_config()
        defaults = self.load_defaults()

        def on_save(new_config: Config) -> None:
            self.save_config(new_config)
            self._full_redraw_overlay()

        dialog = SettingsDialog(config, defaults, on_save)
        dialog.exec()

    def _open_on_startup(self) -> None:
        if self.load_config().open_on_startup:
            self.toggle_overlay()

    def register_hooks(self) -> None:
        mw.addonManager.setConfigAction(self._package_name, self._open_settings)
        gui_hooks.state_did_change.append(self.on_state_change)
        gui_hooks.reviewer_did_show_question.append(self.on_review_shown)
        gui_hooks.main_window_did_init.append(self._add_menu)
        gui_hooks.main_window_did_init.append(self._open_on_startup)
