import enum
from dataclasses import asdict, dataclass, fields
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
    main_color: str
    main_color_opacity: int
    main_circle_stroke_width: int
    back_color: str
    back_color_opacity: int
    back_circle_stroke_width: int
    mask_circles: bool
    hide_main_circle_at_zero: bool
    open_on_startup: bool
    force_update_on_decrease: bool
    update_every_mode: UpdateMode
    update_every_n_reviews: int
    update_every_percent_total: int
    stroke_linecap: StrokeLinecap
    timer_duration_minutes: int
    timer_direction: TimerDirection
    timer_interval_ms: int

    def __post_init__(self) -> None:
        self.update_every_mode = UpdateMode(self.update_every_mode)
        self.timer_direction = TimerDirection(self.timer_direction)
        self.stroke_linecap = StrokeLinecap(self.stroke_linecap)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
