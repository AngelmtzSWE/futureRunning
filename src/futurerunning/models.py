from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Optional
from uuid import uuid4


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("date must use YYYY-MM-DD format") from error


@dataclass(frozen=True)
class Run:
    distance_miles: float
    duration_seconds: int
    run_date: str
    notes: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        if self.distance_miles <= 0:
            raise ValueError("distance must be greater than zero")
        if self.duration_seconds <= 0:
            raise ValueError("duration must be greater than zero")
        if _parse_date(self.run_date) > date.today():
            raise ValueError("run date cannot be in the future")
        if not self.id:
            object.__setattr__(self, "id", uuid4().hex[:8])

    @property
    def pace_seconds_per_mile(self) -> float:
        return self.duration_seconds / self.distance_miles

    @property
    def pace_display(self) -> str:
        total_seconds = round(self.pace_seconds_per_mile)
        return f"{total_seconds // 60}:{total_seconds % 60:02d} /mi"

    @property
    def duration_display(self) -> str:
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        return f"{minutes}m {seconds:02d}s"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Run":
        return cls(float(data["distance_miles"]), int(data["duration_seconds"]), str(data["run_date"]), str(data.get("notes", "")), str(data.get("id", "")))


@dataclass
class Goal:
    target_miles: float
    start_date: str
    end_date: str

    def __post_init__(self) -> None:
        if self.target_miles <= 0:
            raise ValueError("goal target must be greater than zero")
        if _parse_date(self.end_date) < _parse_date(self.start_date):
            raise ValueError("goal end date must be on or after start date")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Goal":
        return cls(float(data["target_miles"]), str(data["start_date"]), str(data["end_date"]))


@dataclass(frozen=True)
class Summary:
    run_count: int
    total_miles: float
    total_seconds: int
    average_pace_seconds: Optional[float]
    longest_run_miles: float

    @property
    def average_pace_display(self) -> str:
        if self.average_pace_seconds is None:
            return "--"
        total_seconds = round(self.average_pace_seconds)
        return f"{total_seconds // 60}:{total_seconds % 60:02d} /mi"
