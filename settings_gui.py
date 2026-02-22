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

PACKAGE_NAME = "anki-progress-circle"  # hardcoded for now


def get_config():
    package = PACKAGE_NAME  # "anki-progress-circle"
    return mw.addonManager.getConfig(package)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(mw)
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
        self.color_label = QLabel("Pick main color:")

        main_color_button = QPushButton()
        main_color_button.setFixedHeight(  # make it small
            main_color_button.sizeHint().height() - 6,
        )

        main_color_button.setStyleSheet(
            f"background-color: {self.config['main_color']};"
        )

        alpha_label = QLabel("Transparency:")

        transparency_spin = QSpinBox()
        transparency_spin.setMinimum(0)
        transparency_spin.setMaximum(100)
        transparency_spin.setValue(100)
        transparency_spin.setSingleStep(5)
        transparency_spin.setSuffix("%")

        def pick_color():
            color = QColorDialog.getColor(
                QColor(self.config["main_color"]), self, "Main circle color properties"
            )
            if color.isValid():
                main_color_button.setStyleSheet(
                    f"background-color: {color.name(QColor.NameFormat.HexRgb)};"
                )
                main_color_button.update()

        main_color_button.clicked.connect(pick_color)

        # Add widgets ==>

        first_row_layout.addWidget(color_label)
        first_row_layout.addWidget(main_color_button)
        first_row_layout.addWidget(alpha_label)
        first_row_layout.addWidget(transparency_spin)

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

    def _save(self):
        mw.addonManager.writeConfig(PACKAGE_NAME, self.config)
        self.accept()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(PACKAGE_NAME)
        if defaults:
            self.config = defaults

            # TODO: update widgets


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()
