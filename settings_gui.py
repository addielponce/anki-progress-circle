from aqt import mw
from aqt.qt import (
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from aqt.qt.qt6 import Qt


class ColorPickerRow(QWidget):
    def __init__(self, label_text, initial_color, initial_opacity, parent=None):
        super().__init__(parent)
        self._color = QColor(initial_color)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._button = QPushButton()
        # Slightly shorter than the default height to align with adjacent spin boxes.
        self._button.setFixedHeight(self._button.sizeHint().height() - 6)
        self._button.clicked.connect(self._pick_color)

        self._opacity_spin = QSpinBox()
        self._opacity_spin.setRange(0, 100)
        self._opacity_spin.setSingleStep(5)
        self._opacity_spin.setSuffix("%")
        self._opacity_spin.setValue(initial_opacity)
        self._opacity_spin.valueChanged.connect(self._refresh_button)

        layout.addWidget(QLabel(label_text))
        layout.addWidget(self._button)
        layout.addWidget(QLabel("Opacity:"))
        layout.addWidget(self._opacity_spin)
        self.setLayout(layout)

        self._refresh_button()

    def _refresh_button(self):
        opacity = self._opacity_spin.value() / 100
        red, green, blue = self._color.red(), self._color.green(), self._color.blue()
        self._button.setStyleSheet(
            f"background-color: rgba({red}, {green}, {blue}, {opacity});"
        )

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
    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Circle settings")
        self.package_name = package_name
        self.config = mw.addonManager.getConfig(package_name)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()

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

        self.mask_checkbox = QCheckBox("Prevent circles from blending together")
        self.mask_checkbox.setCheckState(
            Qt.CheckState.Checked
            if self.config["mask_circles"]
            else Qt.CheckState.Unchecked
        )

        self.hide_at_zero_checkbox = QCheckBox(
            "Hide round stroke linecap if progress is 0"
        )
        self.hide_at_zero_checkbox.setCheckState(
            Qt.CheckState.Checked
            if self.config["hide_main_circle_at_zero"]
            else Qt.CheckState.Unchecked
        )

        self.stroke_linecap_values = ["butt", "round"]
        self.stroke_linecap_combo = QComboBox()
        self.stroke_linecap_combo.addItems(self.stroke_linecap_values)
        self.stroke_linecap_combo.setCurrentIndex(
            self.stroke_linecap_values.index(self.config["stroke_linecap"])
        )

        main_layout.addWidget(self.main_color_picker)
        main_layout.addWidget(self.back_color_picker)
        main_layout.addWidget(self.mask_checkbox)
        main_layout.addWidget(self.hide_at_zero_checkbox)
        main_layout.addWidget(self.stroke_linecap_combo)

        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        defaults_button = QPushButton("Restore Defaults")

        save_button.clicked.connect(self._save)
        cancel_button.clicked.connect(self.reject)
        defaults_button.clicked.connect(self._restore_defaults)

        button_row = QHBoxLayout()
        button_row.addWidget(defaults_button)
        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)

        main_layout.addLayout(button_row)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def _save(self):
        self.config["main_color"] = self.main_color_picker.color
        self.config["main_color_opacity"] = self.main_color_picker.opacity
        self.config["back_color"] = self.back_color_picker.color
        self.config["back_color_opacity"] = self.back_color_picker.opacity
        self.config["mask_circles"] = self.mask_checkbox.isChecked()
        self.config["stroke_linecap"] = self.stroke_linecap_combo.currentText()
        self.config["hide_main_circle_at_zero"] = self.hide_at_zero_checkbox.isChecked()

        mw.addonManager.writeConfig(self.package_name, self.config)
        self.accept()
        from . import update_progress

        update_progress()

    def _restore_defaults(self):
        defaults = mw.addonManager.addonConfigDefaults(self.package_name)
        if not defaults:
            return

        self.config = defaults
        self.main_color_picker.set_color(defaults["main_color"])
        self.main_color_picker.set_opacity(defaults.get("main_color_opacity", 100))
        self.back_color_picker.set_color(defaults["back_color"])
        self.back_color_picker.set_opacity(defaults.get("back_color_opacity", 100))
        self.mask_checkbox.setCheckState(
            Qt.CheckState.Checked
            if defaults["mask_circles"]
            else Qt.CheckState.Unchecked
        )
        self.hide_at_zero_checkbox.setCheckState(
            Qt.CheckState.Checked
            if defaults["hide_main_circle_at_zero"]
            else Qt.CheckState.Unchecked
        )
        linecap = defaults.get("stroke_linecap")
        if linecap in self.stroke_linecap_values:
            self.stroke_linecap_combo.setCurrentIndex(
                self.stroke_linecap_values.index(linecap)
            )


def open_settings(package_name):
    dialog = SettingsDialog(package_name)
    dialog.exec()
