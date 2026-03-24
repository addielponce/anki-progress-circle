import math
from pathlib import Path
from string import Template

from aqt.qt import QDialog, Qt, QVBoxLayout, QWebEngineView, QWidget

from .config import Config

_HTML_TEMPLATE = Template((Path(__file__).parent / "html_circle.html").read_text())


class ProgressOverlay(QDialog):
    _VIEWBOX_SIZE = 100
    _VIEWBOX_CENTER = _VIEWBOX_SIZE / 2
    _RADIUS_PADDING = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Progress circle")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowTransparentForInput
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._web = QWebEngineView()
        self._web.page().setBackgroundColor(Qt.GlobalColor.transparent)
        layout.addWidget(self._web)
        self.setLayout(layout)

        self._page_loaded = False
        self._web.page().loadFinished.connect(self._on_page_loaded)
        self._pending_js: list[str] = []

    def _on_page_loaded(self, ok: bool) -> None:
        self._page_loaded = True
        for js in self._pending_js:
            self._web.page().runJavaScript(js)
        self._pending_js.clear()

    def _run_js(self, js: str) -> None:
        if self._page_loaded:
            self._web.page().runJavaScript(js)
        else:
            self._pending_js.append(js)

    def _compute_geometry(self, config: Config) -> tuple[float, float]:
        max_stroke = max(config.main_circle_stroke_width, config.back_circle_stroke_width)
        radius = max(1, self._VIEWBOX_CENTER - (max_stroke / 2) - self._RADIUS_PADDING)
        return radius, 2 * math.pi * radius

    def _resolve_appearance(self, config: Config, percent: float) -> tuple[float, str]:
        hidden = percent == 0 and config.hide_main_circle_at_zero
        opacity = 0.0 if hidden else config.main_color_opacity / 100
        mask = "url(#mask)" if config.mask_circles and opacity != 0 else ""
        return opacity, mask

    def render(self, config: Config, percent: float) -> None:
        radius, circumference = self._compute_geometry(config)
        dash_length = circumference * (percent / 100)
        opacity, mask = self._resolve_appearance(config, percent)

        self._page_loaded = False
        self._pending_js.clear()
        self._web.setHtml(
            _HTML_TEMPLATE.safe_substitute(
                radius=radius,
                circumference=circumference,
                dash_length=dash_length,
                main_color=config.main_color,
                back_color=config.back_color,
                main_color_opacity=opacity,
                back_color_opacity=config.back_color_opacity / 100,
                main_stroke_width=config.main_circle_stroke_width,
                back_stroke_width=config.back_circle_stroke_width,
                stroke_linecap=config.stroke_linecap,
                mask=mask,
            )
        )

        def update_progress(self, config: Config, percent: float) -> None:
            _, circumference = self._compute_geometry(config)
            dash_length = circumference * (percent / 100)
            opacity, mask = self._resolve_appearance(config, percent)
            self._run_js(f"updateCircle({dash_length}, {circumference}, {opacity}, '{mask}')")

        def start_timer(self, config: Config, duration_seconds: int) -> None:
            # Force the progress circle visible even when hide_main_circle_at_zero
            # has set its opacity to 0.
            opacity = config.main_color_opacity / 100
            mask = "url(#mask)" if config.mask_circles else ""
            self._run_js(
                f"document.getElementById('progress-circle').setAttribute('stroke-opacity', {opacity})"
            )
            self._run_js(f"document.getElementById('back-circle').setAttribute('mask', '{mask}')")
            self._run_js(
                f"startTimer({duration_seconds * 1000}, "
                f"'{config.timer_direction}', {config.timer_interval_ms})"
            )

        def stop_timer(self) -> None:
            self._run_js("stopTimer()")
