from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta


@dataclass
class Penalty:
    """Represents a race penalty."""

    time: str
    reason: str
    unit: str  # "Laps" or "Time"
    value: int

    def to_dict(self) -> dict:
        """Convert penalty to dictionary for JSON serialization."""
        return {
            "time": self.time,
            "reason": self.reason,
            "unit": self.unit,
            "value": self.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Penalty':
        """Create penalty from dictionary."""
        return cls(
            time=data["time"],
            reason=data["reason"],
            unit=data["unit"],
            value=data["value"]
        )


@dataclass
class RaceState:
    """
    Central race state management.

    Attributes:
        race_running: Whether the race timer is currently running
        start_time: Unix timestamp when race started
        paused_time: Accumulated time when paused
        race_duration_hours: Total race duration in hours
        race_duration_minutes: Additional minutes for race duration
        current_stint_idx: Index of current stint
        last_pit_time: Time of last pit stop
        stints: List of driver names for each stint
        planned_stints: Planned stint assignments
        driver_times: Dictionary mapping driver names to accumulated time
        penalties: List of race penalties
        latitude: Current location latitude
        longitude: Current location longitude
        last_address: Last geocoded address
        timer_mode: "elapsed" or "remaining"
    """

    race_running: bool = False
    start_time: float = 0.0
    paused_time: float = 0.0
    race_duration_hours: int = 12
    race_duration_minutes: int = 0
    current_stint_idx: int = 0
    last_pit_time: float = 0.0
    stints: list[Optional[str]] = field(default_factory=lambda: [None])
    planned_stints: list[Optional[str]] = field(default_factory=lambda: [None])
    driver_times: dict[str, float] = field(default_factory=dict)
    penalties: list[Penalty] = field(default_factory=list)
    latitude: float = 48.2541
    longitude: float = 12.4270
    last_address: str = ""
    timer_mode: str = "elapsed"

    @property
    def total_race_seconds(self) -> float:
        """Calculate total race duration in seconds."""
        return self.race_duration_hours * 3600 + self.race_duration_minutes * 60

    @property
    def current_driver(self) -> Optional[str]:
        """Get the currently active driver."""
        if self.current_stint_idx < len(self.stints):
            return self.stints[self.current_stint_idx]
        return None

    def to_dict(self) -> dict:
        """Convert state to dictionary for JSON serialization."""
        return {
            "race_running": self.race_running,
            "start_time": self.start_time,
            "paused_time": self.paused_time,
            "race_duration_hours": self.race_duration_hours,
            "race_duration_minutes": self.race_duration_minutes,
            "current_stint_idx": self.current_stint_idx,
            "last_pit_time": self.last_pit_time,
            "stints": self.stints,
            "planned_stints": self.planned_stints,
            "driver_times": self.driver_times,
            "penalties": [p.to_dict() for p in self.penalties],
            "latitude": self.latitude,
            "longitude": self.longitude,
            "last_address": self.last_address,
            "timer_mode": self.timer_mode
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RaceState':
        """Create race state from dictionary."""
        penalties = [Penalty.from_dict(p) for p in data.get("penalties", [])]
        return cls(
            race_running=data.get("race_running", False),
            start_time=data.get("start_time", 0.0),
            paused_time=data.get("paused_time", 0.0),
            race_duration_hours=data.get("race_duration_hours", 12),
            race_duration_minutes=data.get("race_duration_minutes", 0),
            current_stint_idx=data.get("current_stint_idx", 0),
            last_pit_time=data.get("last_pit_time", 0.0),
            stints=data.get("stints", [None]),
            planned_stints=data.get("planned_stints", [None]),
            driver_times=data.get("driver_times", {}),
            penalties=penalties,
            latitude=data.get("latitude", 48.2541),
            longitude=data.get("longitude", 12.4270),
            last_address=data.get("last_address", ""),
            timer_mode=data.get("timer_mode", "elapsed")
        )
