from collections.abc import Callable

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

from .config import Config, StrokeLinecap, TimerDirection, UpdateMode


class ColorPickerRow(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor("#000000")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._button = QPushButton("Choose color")
        self._button.setMinimumWidth(120)
        self._button.clicked.connect(self._pick_color)

        self._hex_label = QLabel()
        self._hex_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._opacity_label = QLabel("Opacity")
        self._opacity_spin = QSpinBox()
        self._opacity_spin.setRange(0, 100)
        self._opacity_spin.setSingleStep(5)
        self._opacity_spin.setSuffix("%")
        self._opacity_spin.setValue(100)
        self._opacity_spin.valueChanged.connect(self._refresh_button)
        self._opacity_label.setBuddy(self._opacity_spin)

        layout.addWidget(self._button)
        layout.addWidget(self._hex_label, 1)
        layout.addWidget(self._opacity_label)
        layout.addWidget(self._opacity_spin)
        self.setLayout(layout)

        self._refresh_button()

    def _refresh_button(self) -> None:
        color_name = self._color.name(QColor.NameFormat.HexRgb)
        preview = QColor(self._color)
        preview.setAlpha(round(self._opacity_spin.value() * 2.55))
        self._button.setStyleSheet(
            "QPushButton {"
            f"background-color: {preview.name(QColor.NameFormat.HexArgb)};"
            "border: 1px solid palette(mid);"
            "border-radius: 6px;"
            "padding: 4px 10px;"
            "}"
        )
        self._hex_label.setText(color_name)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Pick color")
        if color.isValid():
            self._color = color
            self._refresh_button()

    @property
    def color(self) -> str:
        return self._color.name(QColor.NameFormat.HexRgb)

    @property
    def opacity(self) -> int:
        return self._opacity_spin.value()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self._refresh_button()

    def set_opacity(self, opacity: int) -> None:
        self._opacity_spin.setValue(opacity)


class SettingsDialog(QDialog):
    _STROKE_LINECAP_OPTIONS = [
        ("Flat ends", StrokeLinecap.BUTT),
        ("Rounded ends", StrokeLinecap.ROUND),
    ]
    _TIMER_DIRECTION_OPTIONS = [
        ("Countdown", TimerDirection.COUNTDOWN),
        ("Count up", TimerDirection.COUNTUP),
    ]

    def __init__(
        self,
        config: Config,
        defaults: Config | None,
        on_save: Callable[[Config], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Circle settings")
        self._defaults = defaults
        self._on_save = on_save
        self._build_ui()
        self._apply_config_to_widgets(config)

    def _apply_config_to_widgets(self, config: Config) -> None:
        self._main_color_picker.set_color(config.main_color)
        self._main_color_picker.set_opacity(config.main_color_opacity)
        self._back_color_picker.set_color(config.back_color)
        self._back_color_picker.set_opacity(config.back_color_opacity)

        self._main_stroke_spin.setValue(config.main_circle_stroke_width)
        self._back_stroke_spin.setValue(config.back_circle_stroke_width)
        linecap_idx = self._linecap_combo.findData(config.stroke_linecap)
        if linecap_idx >= 0:
            self._linecap_combo.setCurrentIndex(linecap_idx)

        self._mask_check.setChecked(config.mask_circles)
        self._hide_at_zero_check.setChecked(config.hide_main_circle_at_zero)
        self._open_startup_check.setChecked(config.open_on_startup)
        self._force_decrease_check.setChecked(config.force_update_on_decrease)

        if config.update_every_mode == UpdateMode.PERCENT:
            self._refresh_percent_radio.setChecked(True)
        else:
            self._refresh_cards_radio.setChecked(True)
        self._update_n_reviews_spin.setValue(config.update_every_n_reviews)
        self._update_percent_spin.setValue(config.update_every_percent_total)
        self._sync_refresh_mode_ui()

        self._timer_duration_spin.setValue(config.timer_duration_minutes)
        direction_idx = self._timer_direction_combo.findData(config.timer_direction)
        if direction_idx >= 0:
            self._timer_direction_combo.setCurrentIndex(direction_idx)
        self._timer_interval_spin.setValue(config.timer_interval_ms)

    def _build_config_from_widgets(self) -> Config:
        mode = UpdateMode.PERCENT if self._refresh_percent_radio.isChecked() else UpdateMode.CARDS
        return Config(
            main_color=self._main_color_picker.color,
            main_color_opacity=self._main_color_picker.opacity,
            back_color=self._back_color_picker.color,
            back_color_opacity=self._back_color_picker.opacity,
            main_circle_stroke_width=self._main_stroke_spin.value(),
            back_circle_stroke_width=self._back_stroke_spin.value(),
            stroke_linecap=StrokeLinecap(self._linecap_combo.currentData()),
            mask_circles=self._mask_check.isChecked(),
            hide_main_circle_at_zero=self._hide_at_zero_check.isChecked(),
            open_on_startup=self._open_startup_check.isChecked(),
            force_update_on_decrease=self._force_decrease_check.isChecked(),
            update_every_mode=mode,
            update_every_n_reviews=self._update_n_reviews_spin.value(),
            update_every_percent_total=self._update_percent_spin.value(),
            timer_duration_minutes=self._timer_duration_spin.value(),
            timer_direction=TimerDirection(self._timer_direction_combo.currentData()),
            timer_interval_ms=self._timer_interval_spin.value(),
        )

    def _build_ui(self) -> None:
        self.setMinimumWidth(520)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        main_layout.addWidget(self._build_appearance_group())
        main_layout.addWidget(self._build_stroke_group())
        main_layout.addWidget(self._build_behavior_group())
        main_layout.addWidget(self._build_timer_group())

        button_box = QDialogButtonBox()
        button_box.addButton(
            "Restore Defaults", QDialogButtonBox.ButtonRole.ResetRole
        ).clicked.connect(self._restore_defaults)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        button_box.addButton(QDialogButtonBox.StandardButton.Save)
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def _aligned_form_layout(self) -> QFormLayout:
        layout = QFormLayout()
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        layout.setSpacing(10)
        return layout

    def _build_appearance_group(self) -> QGroupBox:
        group = QGroupBox("Appearance")
        layout = self._aligned_form_layout()

        self._main_color_picker = ColorPickerRow()
        self._back_color_picker = ColorPickerRow()

        layout.addRow("Progress circle", self._main_color_picker)
        layout.addRow("Background circle", self._back_color_picker)
        group.setLayout(layout)
        return group

    def _build_stroke_group(self) -> QGroupBox:
        group = QGroupBox("Stroke")
        layout = self._aligned_form_layout()

        self._main_stroke_spin = QSpinBox()
        self._main_stroke_spin.setRange(1, 50)
        self._main_stroke_spin.setSuffix(" px")

        self._back_stroke_spin = QSpinBox()
        self._back_stroke_spin.setRange(1, 50)
        self._back_stroke_spin.setSuffix(" px")

        self._linecap_combo = QComboBox()
        for label, value in self._STROKE_LINECAP_OPTIONS:
            self._linecap_combo.addItem(label, value)

        layout.addRow("Progress width", self._main_stroke_spin)
        layout.addRow("Background width", self._back_stroke_spin)
        layout.addRow("Stroke end style", self._linecap_combo)
        group.setLayout(layout)
        return group

    def _build_behavior_group(self) -> QGroupBox:
        group = QGroupBox("Behavior")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        self._mask_check = QCheckBox("Prevent circles from blending together")
        self._hide_at_zero_check = QCheckBox("Hide the progress stroke when progress is 0%")
        self._open_startup_check = QCheckBox("Open the progress circle on startup")

        self._refresh_button_group = QButtonGroup(self)
        self._refresh_cards_radio = QRadioButton("Refresh every")
        self._refresh_percent_radio = QRadioButton("Refresh every")
        self._refresh_button_group.addButton(self._refresh_cards_radio)
        self._refresh_button_group.addButton(self._refresh_percent_radio)

        self._update_n_reviews_spin = QSpinBox()
        self._update_n_reviews_spin.setRange(1, 100)
        self._update_n_reviews_spin.setSuffix(" cards")
        self._update_n_reviews_spin.valueChanged.connect(self._refresh_update_preview)

        self._update_cards_preview = QLabel()
        self._update_cards_preview.setStyleSheet("color: palette(mid);")

        self._update_percent_spin = QSpinBox()
        self._update_percent_spin.setRange(1, 100)
        self._update_percent_spin.setSuffix("%")
        self._update_percent_spin.valueChanged.connect(self._refresh_update_preview)

        self._update_percent_preview = QLabel()
        self._update_percent_preview.setStyleSheet("color: palette(mid);")

        self._force_decrease_check = QCheckBox("Refresh immediately if progress decreases")
        self._force_decrease_check.setToolTip(
            "If enabled, the circle refreshes right away when the percentage drops."
        )

        cards_row = QWidget()
        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(8)
        cards_layout.addWidget(self._refresh_cards_radio)
        cards_layout.addWidget(self._update_n_reviews_spin)
        cards_layout.addWidget(self._update_cards_preview)
        cards_layout.addStretch(1)
        cards_row.setLayout(cards_layout)

        percent_row = QWidget()
        percent_layout = QHBoxLayout()
        percent_layout.setContentsMargins(0, 0, 0, 0)
        percent_layout.setSpacing(8)
        percent_layout.addWidget(self._refresh_percent_radio)
        percent_layout.addWidget(self._update_percent_spin)
        percent_layout.addWidget(QLabel("of total"))
        percent_layout.addWidget(self._update_percent_preview)
        percent_layout.addStretch(1)
        percent_row.setLayout(percent_layout)

        update_container = QWidget()
        update_layout = QVBoxLayout()
        update_layout.setContentsMargins(0, 0, 0, 0)
        update_layout.setSpacing(6)
        update_layout.addWidget(cards_row)
        update_layout.addWidget(percent_row)
        update_container.setLayout(update_layout)

        self._refresh_cards_radio.toggled.connect(self._sync_refresh_mode_ui)
        self._refresh_percent_radio.toggled.connect(self._sync_refresh_mode_ui)

        layout.addWidget(self._mask_check)
        layout.addWidget(self._hide_at_zero_check)
        layout.addWidget(self._open_startup_check)
        layout.addWidget(update_container)
        layout.addWidget(self._force_decrease_check)
        group.setLayout(layout)
        return group

    def _build_timer_group(self) -> QGroupBox:
        group = QGroupBox("Timer")
        layout = self._aligned_form_layout()

        self._timer_duration_spin = QSpinBox()
        self._timer_duration_spin.setRange(1, 120)
        self._timer_duration_spin.setSuffix(" min")

        self._timer_direction_combo = QComboBox()
        for label, value in self._TIMER_DIRECTION_OPTIONS:
            self._timer_direction_combo.addItem(label, value)

        self._timer_interval_spin = QSpinBox()
        self._timer_interval_spin.setRange(5, 5000)
        self._timer_interval_spin.setSuffix(" ms")

        self._timer_interval_warning = QLabel(
            "Your CPU won't be happy, but at least the room will be warm."
        )
        self._timer_interval_warning.setStyleSheet("color: palette(mid);")
        self._timer_interval_warning.setWordWrap(True)
        self._timer_interval_warning.setVisible(False)
        self._timer_interval_spin.valueChanged.connect(
            lambda v: self._timer_interval_warning.setVisible(v < 50)
        )

        layout.addRow("Duration", self._timer_duration_spin)
        layout.addRow("Direction", self._timer_direction_combo)
        layout.addRow("Update interval", self._timer_interval_spin)
        layout.addRow("", self._timer_interval_warning)
        group.setLayout(layout)
        return group

    def _get_current_queue_total(self) -> int | None:
        if not mw.col:
            return None
        queued = mw.col.sched.get_queued_cards(fetch_limit=1)
        return int(queued.new_count + queued.learning_count + queued.review_count)

    def _sync_refresh_mode_ui(self) -> None:
        cards_mode = self._refresh_cards_radio.isChecked()
        self._update_n_reviews_spin.setEnabled(cards_mode)
        self._update_percent_spin.setEnabled(not cards_mode)
        self._refresh_update_preview()

    def _refresh_update_preview(self) -> None:
        total = self._get_current_queue_total()
        cards = self._update_n_reviews_spin.value()

        if total is None or total <= 0:
            self._update_cards_preview.setText("≈ ?% of current queue")
        else:
            pct = int(round((cards / float(total)) * 100))
            self._update_cards_preview.setText(
                f"≈ {'>' if pct > 100 else ''}{min(pct, 100)}% of current queue"
            )

        pct_of_total = self._update_percent_spin.value()
        if total is None or total <= 0:
            self._update_percent_preview.setText("≈ ? cards")
        else:
            n_cards = max(1, int(round(total * (pct_of_total / 100.0))))
            self._update_percent_preview.setText(f"≈ {n_cards} cards")

    def _save(self) -> None:
        self._on_save(self._build_config_from_widgets())
        self.accept()

    def _restore_defaults(self) -> None:
        if self._defaults is not None:
            self._apply_config_to_widgets(self._defaults)
