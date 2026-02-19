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

# TODO: Add color picker
COLOR = "LimeGreen"

# Circle properties
RADIUS = 45
CIRCUMFERENCE = 2 * 3.1416 * RADIUS

# HTML template for the circle
HTML = (Path(__file__).parent / "html_circle.html").read_text()


class ProgressWindow(QDialog):
    def __init__(self, parent=None):

        super().__init__(parent)
        self.setWindowTitle("Progress circle")

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint  # No titlebar for maximum immersion
            | Qt.WindowType.WindowTransparentForInput
        )

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create widget for HTML content
        self.web = QWebEngineView()
        self.web.page().setBackgroundColor(Qt.GlobalColor.transparent)
        # Add widget and layout
        layout.addWidget(self.web)
        self.setLayout(layout)

        # Start from zero
        self.update_progress(0, 0, 0)

    def update_progress(self, done, total, percent):
        """Update the progress circle using SVG"""

        # Green progress circle
        dash_offset = CIRCUMFERENCE * (1 - percent / 100)

        # Replace fields in "html_circle.html"
        html_content = HTML.format(
            radius=RADIUS,
            circumference=CIRCUMFERENCE,
            dash_offset=dash_offset,  # Progress ⭕
            color=COLOR,
            # done=done,
            # total=total,
            # percent=percent,
        )

        self.web.setHtml(html_content)


# Main window
progress_window = None

# Track progress per deck
deck_goal = {}
deck_done = {}


def get_current_progress():
    global deck_goal, deck_done

    if not mw.col:
        return 0, 0, 0.0

    id = mw.col.decks.get_current_id()

    queued = mw.col.sched.get_queued_cards(fetch_limit=1)
    remaining = queued.new_count + queued.learning_count + queued.review_count

    if id not in deck_goal:
        deck_goal[id] = remaining
        deck_done[id] = 0
    else:
        deck_done[id] = deck_goal[id] - remaining

        if remaining > deck_goal[id]:
            deck_goal[id] = remaining
            deck_done[id] = 0

    total = deck_goal[id]
    done = deck_done[id]
    percent = (done / total * 100) if total > 0 else 0.0

    return done, total, percent


def toggle_progress_window():
    """Show or hide the progress window"""

    global progress_window

    # Check if the circle exists
    if progress_window is None:
        progress_window = ProgressWindow(None)

    done, total, percent = get_current_progress()

    progress_window.update_progress(done, total, percent)

    if not progress_window.isVisible():
        progress_window.showMaximized()
    else:
        progress_window.close()


def update_progress():
    """Update progress if window is open"""
    if progress_window is not None and progress_window.isVisible():
        done, total, percent = get_current_progress()
        progress_window.update_progress(done, total, percent)


# Hook functions
def on_state_change(state, oldState):
    if state in ("deckBrowser", "overview", "review"):
        update_progress()


def on_show_question(*args, **kwargs):
    update_progress()


def add_menu_entry():
    """Add menu item in Tools"""
    menu = QMenu("Circular progress ⭕", mw)
    mw.form.menuTools.addMenu(menu)
    action = menu.addAction("Toggle circular progress")
    action.triggered.connect(toggle_progress_window)


# Hooks
gui_hooks.state_did_change.append(on_state_change)
gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.main_window_did_init.append(add_menu_entry)
