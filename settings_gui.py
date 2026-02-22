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

        alpha_label = QLabel("Transparency:")
        self.transparency_spin = QSpinBox()
        self.transparency_spin.setRange(0, 100)
        self.transparency_spin.setSingleStep(5)
        self.transparency_spin.setSuffix("%")
        self.transparency_spin.setValue(self.config.get("main_color_transparency", 100))

        first_row_layout.addWidget(color_label)
        first_row_layout.addWidget(self.main_color_button)
        first_row_layout.addWidget(alpha_label)
        first_row_layout.addWidget(self.transparency_spin)
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

    def _pick_color(self):
        color = QColorDialog.getColor(
            QColor(self.config["main_color"]), self, "Main circle color properties"
        )
        if color.isValid():
            self._update_color_button(color.name(QColor.NameFormat.HexRgb))

    def _save(self):
        self.config["main_color_transparency"] = self.transparency_spin.value()
        mw.addonManager.writeConfig(PACKAGE_NAME, self.config)
        self.accept()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(PACKAGE_NAME)
        if defaults:
            self.config = defaults
            self._update_color_button(defaults["main_color"])


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()
