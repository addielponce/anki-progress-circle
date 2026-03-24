import enum
from dataclasses import dataclass
from typing import Any


class UpdateMode(enum.StrEnum):
    CARDS = "cards"
    PERCENT = "percent"


class TimerDirection(enum.StrEnum):
    COUNTDOWN = "countdown"
    COUNTUP = "countup"


class StrokeLinecap(enum.StrEnum):
    BUTT = "butt"
    ROUND = "round"


@dataclass
class Config:
    main_color: str = "#32cd32"
    main_color_opacity: int = 100
    main_circle_stroke_width: int = 8
    back_color: str = "#000000"
    back_color_opacity: int = 30
    back_circle_stroke_width: int = 8
    mask_circles: bool = True
    hide_main_circle_at_zero: bool = True
    open_on_startup: bool = False
    force_update_on_decrease: bool = True
    update_every_mode: UpdateMode = UpdateMode.CARDS
    update_every_n_reviews: int = 1
    update_every_percent_total: int = 1
    stroke_linecap: StrokeLinecap = StrokeLinecap.BUTT
    timer_duration_minutes: int = 25
    timer_direction: TimerDirection = TimerDirection.COUNTDOWN
    timer_interval_ms: int = 250

    def __post_init__(self) -> None:
        self.update_every_mode = UpdateMode(self.update_every_mode)
        self.timer_direction = TimerDirection(self.timer_direction)
        self.stroke_linecap = StrokeLinecap(self.stroke_linecap)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        known = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
