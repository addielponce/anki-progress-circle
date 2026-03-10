from aqt import mw
from aqt.qt import (
    QCheckBox,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
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
        layout.setSpacing(8)

        self._button = QPushButton("Choose color")
        self._button.setMinimumWidth(120)
        self._button.clicked.connect(self._pick_color)

        self._hex_label = QLabel()
        self._hex_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self._opacity_label = QLabel("Opacity")
        self._opacity_spin = QSpinBox()
        self._opacity_spin.setRange(0, 100)
        self._opacity_spin.setSingleStep(5)
        self._opacity_spin.setSuffix("%")
        self._opacity_spin.setValue(initial_opacity)
        self._opacity_spin.valueChanged.connect(self._refresh_button)
        self._opacity_label.setBuddy(self._opacity_spin)

        layout.addWidget(self._button)
        layout.addWidget(self._hex_label, 1)
        layout.addWidget(self._opacity_label)
        layout.addWidget(self._opacity_spin)
        self.setLayout(layout)

        self._refresh_button()

    def _refresh_button(self):
        color_name = self._color.name(QColor.NameFormat.HexRgb)
        preview_color = QColor(self._color)
        preview_color.setAlpha(round(self._opacity_spin.value() * 2.55))
        self._button.setStyleSheet(
            "QPushButton {{"
            "background-color: {color};"
            "border: 1px solid palette(mid);"
            "border-radius: 6px;"
            "padding: 4px 10px;"
            "}}".format(color=preview_color.name(QColor.NameFormat.HexArgb))
        )
        self._hex_label.setText(color_name)

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
    STROKE_LINECAP_OPTIONS = [
        ("Flat ends", "butt"),
        ("Rounded ends", "round"),
    ]

    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Circle settings")
        self.package_name = package_name
        self.config = mw.addonManager.getConfig(package_name)
        self._build_ui()

    def _build_ui(self):
        self.setMinimumWidth(520)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()
        appearance_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        appearance_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        appearance_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        appearance_layout.setSpacing(10)

        self.main_color_picker = ColorPickerRow(
            "Progress circle",
            self.config["main_color"],
            self.config.get("main_color_opacity", 100),
        )
        self.back_color_picker = ColorPickerRow(
            "Back circle",
            self.config["back_color"],
            self.config.get("back_color_opacity", 100),
        )

        appearance_layout.addRow("Progress circle", self.main_color_picker)
        appearance_layout.addRow("Background circle", self.back_color_picker)
        appearance_group.setLayout(appearance_layout)

        stroke_group = QGroupBox("Stroke")
        stroke_layout = QFormLayout()
        stroke_layout.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        stroke_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        stroke_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        stroke_layout.setSpacing(10)

        self.main_stroke_width_spin = QSpinBox()
        self.main_stroke_width_spin.setRange(1, 50)
        self.main_stroke_width_spin.setSuffix(" px")
        self.main_stroke_width_spin.setValue(
            self.config.get("main_circle_stroke_width", 8)
        )

        self.back_stroke_width_spin = QSpinBox()
        self.back_stroke_width_spin.setRange(1, 50)
        self.back_stroke_width_spin.setSuffix(" px")
        self.back_stroke_width_spin.setValue(
            self.config.get("back_circle_stroke_width", 8)
        )

        self.stroke_linecap_combo = QComboBox()
        for label, value in self.STROKE_LINECAP_OPTIONS:
            self.stroke_linecap_combo.addItem(label, value)

        current_linecap = self.config.get("stroke_linecap", "butt")
        current_linecap_index = self.stroke_linecap_combo.findData(current_linecap)
        if current_linecap_index >= 0:
            self.stroke_linecap_combo.setCurrentIndex(current_linecap_index)

        stroke_layout.addRow("Progress width", self.main_stroke_width_spin)
        stroke_layout.addRow("Background width", self.back_stroke_width_spin)
        stroke_layout.addRow("Stroke end style", self.stroke_linecap_combo)
        stroke_group.setLayout(stroke_layout)

        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        behavior_layout.setSpacing(8)

        self.mask_checkbox = QCheckBox("Prevent circles from blending together")
        self.mask_checkbox.setChecked(self.config["mask_circles"])

        self.hide_at_zero_checkbox = QCheckBox(
            "Hide the progress stroke when progress is 0%"
        )
        self.hide_at_zero_checkbox.setChecked(self.config["hide_main_circle_at_zero"])

        behavior_layout.addWidget(self.mask_checkbox)
        behavior_layout.addWidget(self.hide_at_zero_checkbox)
        behavior_group.setLayout(behavior_layout)

        button_box = QDialogButtonBox()
        self.restore_defaults_button = button_box.addButton(
            "Restore Defaults", QDialogButtonBox.ButtonRole.ResetRole
        )
        self.cancel_button = button_box.addButton(
            QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = button_box.addButton(QDialogButtonBox.StandardButton.Save)

        self.restore_defaults_button.clicked.connect(self._restore_defaults)
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(appearance_group)
        main_layout.addWidget(stroke_group)
        main_layout.addWidget(behavior_group)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def _save(self):
        self.config["main_color"] = self.main_color_picker.color
        self.config["main_color_opacity"] = self.main_color_picker.opacity
        self.config["main_circle_stroke_width"] = self.main_stroke_width_spin.value()
        self.config["back_color"] = self.back_color_picker.color
        self.config["back_color_opacity"] = self.back_color_picker.opacity
        self.config["back_circle_stroke_width"] = self.back_stroke_width_spin.value()
        self.config["mask_circles"] = self.mask_checkbox.isChecked()
        self.config["stroke_linecap"] = self.stroke_linecap_combo.currentData()
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
        self.main_stroke_width_spin.setValue(
            defaults.get("main_circle_stroke_width", 8)
        )
        self.back_color_picker.set_color(defaults["back_color"])
        self.back_color_picker.set_opacity(defaults.get("back_color_opacity", 100))
        self.back_stroke_width_spin.setValue(
            defaults.get("back_circle_stroke_width", 8)
        )
        self.mask_checkbox.setChecked(defaults["mask_circles"])
        self.hide_at_zero_checkbox.setChecked(defaults["hide_main_circle_at_zero"])

        linecap = defaults.get("stroke_linecap", "butt")
        linecap_index = self.stroke_linecap_combo.findData(linecap)
        if linecap_index >= 0:
            self.stroke_linecap_combo.setCurrentIndex(linecap_index)


def open_settings(package_name):
    dialog = SettingsDialog(package_name)
    dialog.exec()
