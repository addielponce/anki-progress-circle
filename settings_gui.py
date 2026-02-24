from aqt import mw
from aqt.qt import (
    QColor,
    QColorDialog,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PACKAGE_NAME = "anki-progress-circle"


class ColorPickerRow(QWidget):
    def __init__(self, label_text, initial_color, initial_opacity, parent=None):
        super().__init__(parent)
        self._color = QColor(initial_color)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        self._button = QPushButton()
        self._button.setFixedHeight(self._button.sizeHint().height() - 6)
        self._button.clicked.connect(self._pick_color)

        alpha_label = QLabel("Opacity:")
        self._opacity_spin = QSpinBox()
        self._opacity_spin.setRange(0, 100)
        self._opacity_spin.setSingleStep(5)
        self._opacity_spin.setSuffix("%")
        self._opacity_spin.setValue(initial_opacity)
        self._opacity_spin.valueChanged.connect(self._refresh_button)

        layout.addWidget(label)
        layout.addWidget(self._button)
        layout.addWidget(alpha_label)
        layout.addWidget(self._opacity_spin)
        self.setLayout(layout)

        self._refresh_button()

    def _refresh_button(self):
        opacity = self._opacity_spin.value() / 100
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        self._button.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {opacity});")

    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self, "Pick color")
        if color.isValid():
            self._color = color
            self._refresh_button()

    @property
    def color(self):
        return self._color.name(QColor.NameFormat.HexRgb)

    @property
    def opacity(self):
        return self._opacity_spin.value()

    def set_color(self, color):
        self._color = QColor(color)
        self._refresh_button()

    def set_opacity(self, opacity):
        self._opacity_spin.setValue(opacity)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Circle settings")
        self.config = mw.addonManager.getConfig(PACKAGE_NAME)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()

        # ================================================
        #                     Widgets
        # ================================================
        self.main_color_picker = ColorPickerRow(
            "Pick main color:",
            self.config["main_color"],
            self.config.get("main_color_opacity", 100),
        )
        self.back_color_picker = ColorPickerRow(
            "Pick back color:",
            self.config["back_color"],
            self.config.get("back_color_opacity", 100),
        )
        main_layout.addWidget(self.main_color_picker)
        main_layout.addWidget(self.back_color_picker)

        # =============================================
        #                   Buttons
        # =============================================
        buttons = QHBoxLayout()
        save = QPushButton("Save")
        cancel = QPushButton("Cancel")
        defaults = QPushButton("Restore Defaults")

        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        defaults.clicked.connect(self._restore_defaults)

        # Add all widgets

        buttons.addWidget(defaults)
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        # Add layouts
        main_layout.addLayout(buttons)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def _save(self):
        self.config["main_color"] = self.main_color_picker.color
        self.config["main_color_opacity"] = self.main_color_picker.opacity
        mw.addonManager.writeConfig(PACKAGE_NAME, self.config)
        self.accept()
        from . import update_progress

        update_progress()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(PACKAGE_NAME)
        if defaults:
            self.config = defaults
            self.main_color_picker.set_color(defaults["main_color"])
            self.main_color_picker.set_opacity(defaults.get("main_color_opacity", 100))


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()
