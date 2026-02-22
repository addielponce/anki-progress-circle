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
)

PACKAGE_NAME = "anki-progress-circle"


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

        # Create widgets ==>

        first_row_layout = QHBoxLayout()

        # Label
        color_label = QLabel("Pick main color:")
        self.main_color_button = QPushButton()
        self.main_color_button.setFixedHeight(
            self.main_color_button.sizeHint().height() - 6  # make it small
        )
        self._update_color_button(self.config["main_color"])
        self.main_color_button.clicked.connect(self._pick_color)

        alpha_label = QLabel("Opacity:")
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setSingleStep(5)
        self.opacity_spin.setSuffix("%")
        self.opacity_spin.setValue(self.config.get("main_color_opacity", 100))
        self.opacity_spin.valueChanged.connect(self._refresh_button)

        first_row_layout.addWidget(color_label)
        first_row_layout.addWidget(self.main_color_button)
        first_row_layout.addWidget(alpha_label)
        first_row_layout.addWidget(self.opacity_spin)
        main_layout.addLayout(first_row_layout)

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

    def _update_color_button(self, hex_color):
        self.main_color_button.setStyleSheet(f"background-color: {hex_color};")
        self.config["main_color"] = hex_color

    def _refresh_button(self):
        opacity = self.opacity_spin.value() / 100
        color = QColor(self.config["main_color"])
        self.main_color_button.setStyleSheet(
            f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {opacity});"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(
            QColor(self.config["main_color"]), self, "Main circle color properties"
        )
        if color.isValid():
            self._update_color_button(color.name(QColor.NameFormat.HexRgb))

    def _save(self):
        alpha = int(self.opacity_spin.value() / 100 * 255)
        color = QColor(self.config["main_color"])
        color.setAlpha(alpha)
        self.config["main_color"] = (
            f"rgba({color.red()}, {color.green()}, {color.blue()}, {self.opacity_spin.value() / 100})"
        )
        self.config["main_color_opacity"] = self.opacity_spin.value()
        mw.addonManager.writeConfig(PACKAGE_NAME, self.config)
        self.accept()
        from . import update_progress

        update_progress()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(PACKAGE_NAME)
        if defaults:
            self.config = defaults
            self._update_color_button(defaults["main_color"])
            self.opacity_spin.setValue(defaults.get("main_color_opacity", 100))


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()
