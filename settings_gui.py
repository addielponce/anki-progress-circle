from aqt import mw
from aqt.qt import (
    QButtonGroup,
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
    QRadioButton,
    QSpinBox,
    Qt,
    QVBoxLayout,
    QWidget,
)


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

    def _get_current_queue_total(self):
        """Best-effort estimate for the current deck queue size, for UI preview."""
        try:
            if not mw.col:
                return None
            queued = mw.col.sched.get_queued_cards(fetch_limit=1)
            return int(queued.new_count + queued.learning_count + queued.review_count)
        except Exception:
            return None

    def _sync_refresh_mode_ui(self):
        cards = self.refresh_cards_radio.isChecked()
        self.update_every_n_reviews_spin.setEnabled(cards)
        self.update_every_percent_spin.setEnabled(not cards)
        self._refresh_update_every_preview()

    def _refresh_update_every_preview(self):
        total = self._get_current_queue_total()
        cards = self.update_every_n_reviews_spin.value()
        if total is None or total <= 0:
            self.update_every_cards_preview.setText("≈ ?% of current queue")
        else:
            percent_of_total_rounded = int(round((cards / float(total)) * 100))
            if percent_of_total_rounded > 100:
                self.update_every_cards_preview.setText("≈ >100% of current queue")
            else:
                self.update_every_cards_preview.setText(
                    f"≈ {percent_of_total_rounded}% of current queue"
                )

        percent_of_total = self.update_every_percent_spin.value()
        if total is None or total <= 0:
            self.update_every_percent_preview.setText("≈ ? cards")
        else:
            n_cards = max(1, int(round(total * (percent_of_total / 100.0))))
            self.update_every_percent_preview.setText(f"≈ {n_cards} cards")

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

        self.open_on_startup_checkbox = QCheckBox("Open the progress circle on startup")
        self.open_on_startup_checkbox.setChecked(
            self.config.get("open_on_startup", False)
        )

        self.refresh_button_group = QButtonGroup(self)
        self.refresh_cards_radio = QRadioButton("Refresh every")
        self.refresh_percent_radio = QRadioButton("Refresh every")
        self.refresh_button_group.addButton(self.refresh_cards_radio)
        self.refresh_button_group.addButton(self.refresh_percent_radio)

        update_mode = (self.config.get("update_every_mode", "cards") or "cards").strip()
        if update_mode.lower() == "percent":
            self.refresh_percent_radio.setChecked(True)
        else:
            self.refresh_cards_radio.setChecked(True)

        self.update_every_n_reviews_spin = QSpinBox()
        self.update_every_n_reviews_spin.setRange(1, 100)
        self.update_every_n_reviews_spin.setValue(
            int(self.config.get("update_every_n_reviews", 1) or 1)
        )
        self.update_every_n_reviews_spin.setSuffix(" cards")
        self.update_every_n_reviews_spin.valueChanged.connect(
            self._refresh_update_every_preview
        )

        self.update_every_cards_preview = QLabel()
        self.update_every_cards_preview.setStyleSheet("color: palette(mid);")

        self.update_every_percent_spin = QSpinBox()
        self.update_every_percent_spin.setRange(1, 100)
        self.update_every_percent_spin.setValue(
            int(self.config.get("update_every_percent_total", 1) or 1)
        )
        self.update_every_percent_spin.setSuffix("%")
        self.update_every_percent_spin.valueChanged.connect(
            self._refresh_update_every_preview
        )

        self.update_every_percent_preview = QLabel()
        self.update_every_percent_preview.setStyleSheet("color: palette(mid);")

        self.force_update_on_decrease_checkbox = QCheckBox(
            "Refresh immediately if progress decreases"
        )
        self.force_update_on_decrease_checkbox.setChecked(
            self.config.get("force_update_on_decrease", True)
        )
        self.force_update_on_decrease_checkbox.setToolTip(
            "If enabled, the circle refreshes right away when the percentage drops."
        )

        update_every_row = QWidget()
        update_every_row_layout = QVBoxLayout()
        update_every_row_layout.setContentsMargins(0, 0, 0, 0)
        update_every_row_layout.setSpacing(6)

        cards_row = QWidget()
        cards_row_layout = QHBoxLayout()
        cards_row_layout.setContentsMargins(0, 0, 0, 0)
        cards_row_layout.setSpacing(8)
        cards_row_layout.addWidget(self.refresh_cards_radio)
        cards_row_layout.addWidget(self.update_every_n_reviews_spin)
        cards_row_layout.addWidget(self.update_every_cards_preview)
        cards_row_layout.addStretch(1)
        cards_row.setLayout(cards_row_layout)

        percent_row = QWidget()
        percent_row_layout = QHBoxLayout()
        percent_row_layout.setContentsMargins(0, 0, 0, 0)
        percent_row_layout.setSpacing(8)
        percent_row_layout.addWidget(self.refresh_percent_radio)
        percent_row_layout.addWidget(self.update_every_percent_spin)
        percent_row_layout.addWidget(QLabel("of total"))
        percent_row_layout.addWidget(self.update_every_percent_preview)
        percent_row_layout.addStretch(1)
        percent_row.setLayout(percent_row_layout)

        update_every_row_layout.addWidget(cards_row)
        update_every_row_layout.addWidget(percent_row)
        update_every_row.setLayout(update_every_row_layout)

        self.refresh_cards_radio.toggled.connect(self._sync_refresh_mode_ui)
        self.refresh_percent_radio.toggled.connect(self._sync_refresh_mode_ui)

        behavior_layout.addWidget(self.mask_checkbox)
        behavior_layout.addWidget(self.hide_at_zero_checkbox)
        behavior_layout.addWidget(self.open_on_startup_checkbox)
        behavior_layout.addWidget(update_every_row)
        behavior_layout.addWidget(self.force_update_on_decrease_checkbox)
        behavior_group.setLayout(behavior_layout)

        self._sync_refresh_mode_ui()

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
        config = self.config
        config.update(
            {
                "main_color": self.main_color_picker.color,
                "main_color_opacity": self.main_color_picker.opacity,
                "main_circle_stroke_width": self.main_stroke_width_spin.value(),
                "back_color": self.back_color_picker.color,
                "back_color_opacity": self.back_color_picker.opacity,
                "back_circle_stroke_width": self.back_stroke_width_spin.value(),
                "mask_circles": self.mask_checkbox.isChecked(),
                "stroke_linecap": self.stroke_linecap_combo.currentData(),
                "hide_main_circle_at_zero": self.hide_at_zero_checkbox.isChecked(),
                "open_on_startup": self.open_on_startup_checkbox.isChecked(),
                "force_update_on_decrease": self.force_update_on_decrease_checkbox.isChecked(),
            }
        )

        if self.refresh_percent_radio.isChecked():
            config.update(
                {
                    "update_every_mode": "percent",
                    "update_every_n_reviews": self.update_every_n_reviews_spin.value(),
                    "update_every_percent_total": self.update_every_percent_spin.value(),
                }
            )
        else:
            config.update(
                {
                    "update_every_mode": "cards",
                    "update_every_n_reviews": self.update_every_n_reviews_spin.value(),
                    "update_every_percent_total": self.update_every_percent_spin.value(),
                }
            )

        mw.addonManager.writeConfig(self.package_name, self.config)
        self.accept()
        from . import refresh_overlay

        refresh_overlay()

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
        self.open_on_startup_checkbox.setChecked(defaults.get("open_on_startup", False))
        self.force_update_on_decrease_checkbox.setChecked(
            defaults.get("force_update_on_decrease", True)
        )
        mode = (defaults.get("update_every_mode", "cards") or "cards").strip().lower()
        if mode == "percent":
            self.refresh_percent_radio.setChecked(True)
        else:
            self.refresh_cards_radio.setChecked(True)
        self.update_every_n_reviews_spin.setValue(
            defaults.get("update_every_n_reviews", 1)
        )
        self.update_every_percent_spin.setValue(
            defaults.get("update_every_percent_total", 1)
        )
        self._sync_refresh_mode_ui()

        linecap = defaults.get("stroke_linecap", "butt")
        linecap_index = self.stroke_linecap_combo.findData(linecap)
        if linecap_index >= 0:
            self.stroke_linecap_combo.setCurrentIndex(linecap_index)


def open_settings(package_name):
    dialog = SettingsDialog(package_name)
    dialog.exec()
