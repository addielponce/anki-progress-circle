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


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__(mw)
        self.setWindowTitle("Circle settings")
        self.config = mw.addonManager.getConfig(__name__)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()  #
        form = QHBoxLayout()

        # ================================================
        #                     Widgets
        # ================================================

        self.color_edit = QLineEdit(self.config.get("color", ""))

        color_btn = QPushButton("Pick Color")
        color_btn.clicked.connect(pick_color)

        def pick_color():
            color = QColorDialog.getColor(
                QColor(self.color_edit.text()),
                self,
                "Main circle color properties",
                QColorDialog.ColorDialogOption.ShowAlphaChannel,
            )

            if color.isValid():
                # TODO: Set config values using color.alpha() etc
                self.color_edit.setText(color.name(QColor.NameFormat.HexArgb))

        form.addWidget(self.color_edit)
        form.addWidget(color_btn)

        main_layout.addLayout(form)

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

        self.setLayout(main_layout)

    def _save(self):
        mw.addonManager.writeConfig(__name__, self.config)
        self.accept()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(__name__)
        if defaults:
            self.config = defaults

            # TODO: update widgets


def open_settings():
    dialog = SettingsDialog()
    dialog.exec()
