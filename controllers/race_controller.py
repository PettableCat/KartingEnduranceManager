import json
import random
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, QTimer

from models.race_state import RaceState, Penalty
from models.driver import Driver


class RaceController(QObject):
    """
    Controller for race management.

    Signals:
        state_changed: Emitted when race state changes
        drivers_changed: Emitted when driver list changes
        timer_updated: Emitted every second when race is running
    """

    state_changed = Signal()
    drivers_changed = Signal()
    timer_updated = Signal(float)  # current time in seconds

    def __init__(self, base_dir: Path):
        """
        Initialize race controller.

        Args:
            base_dir: Base directory for data files
        """
        super().__init__()

        self._base_dir = base_dir
        self._drivers_file = base_dir / "drivers.json"
        self._autosave_file = base_dir / "autosave.json"

        self._state = RaceState()
        self._drivers: List[Driver] = []

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(1000)  # 1 second

        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self.save_state)
        self._autosave_timer.setInterval(300000)  # 5 minutes
        self._autosave_timer.start()

        self._load_drivers()

    @property
    def state(self) -> RaceState:
        """Get current race state."""
        return self._state

    @property
    def drivers(self) -> List[Driver]:
        """Get list of drivers."""
        return self._drivers

    def get_driver_names(self) -> List[str]:
        """Get list of driver names."""
        return [driver.name for driver in self._drivers]

    def get_race_time(self) -> float:
        """
        Calculate current race time in seconds.

        Returns:
            Current race time in seconds
        """
        if self._state.race_running:
            return time.time() - self._state.start_time
        return self._state.paused_time

    def start_race(self) -> None:
        """Start the race timer."""
        if not self._state.race_running:
            self._state.race_running = True
            self._state.start_time = time.time() - self._state.paused_time
            self._timer.start()
            self.state_changed.emit()

    def pause_race(self) -> None:
        """Pause the race timer."""
        if self._state.race_running:
            self._state.paused_time = self.get_race_time()
            self._state.race_running = False
            self._timer.stop()
            self.state_changed.emit()

    def reset_race(self) -> None:
        """Reset race to initial state."""
        self._timer.stop()

        driver_names = self.get_driver_names()
        self._state = RaceState()
        self._state.driver_times = {name: 0.0 for name in driver_names}

        self.state_changed.emit()

    def set_manual_time(self, hours: int, minutes: int) -> None:
        """
        Set race time manually.

        Args:
            hours: Hours to set
            minutes: Minutes to set
        """
        total_seconds = hours * 3600 + minutes * 60
        self._state.start_time = time.time() - total_seconds
        self._state.paused_time = total_seconds
        self._state.race_running = True

        if not self._timer.isActive():
            self._timer.start()

        self.state_changed.emit()

    def pit_stop(self) -> None:
        """Execute a pit stop, advancing to next stint."""
        if self._state.current_stint_idx >= len(self._state.stints):
            return

        current_driver = self._state.current_driver
        if current_driver:
            current_time = self.get_race_time()
            stint_time = current_time - self._state.last_pit_time

            self._state.driver_times[current_driver] = (
                    self._state.driver_times.get(current_driver, 0.0) + stint_time
            )

            self._state.current_stint_idx += 1
            self._state.last_pit_time = current_time

            self.state_changed.emit()

    def add_stints(self, count: int) -> None:
        """
        Add empty stints to the race.

        Args:
            count: Number of stints to add
        """
        self._state.stints.extend([None] * count)
        self._state.planned_stints = list(self._state.stints)
        self.state_changed.emit()

    def randomize_stints(self) -> None:
        """Randomly assign drivers to all stints."""
        driver_names = self.get_driver_names()
        if not driver_names:
            return

        total_stints = len(self._state.stints)
        base_count = total_stints // len(driver_names)
        remainder = total_stints % len(driver_names)

        stints_list = []
        for driver in driver_names:
            stints_list.extend([driver] * base_count)

        stints_list.extend(random.sample(driver_names, remainder))
        random.shuffle(stints_list)

        self._state.stints = stints_list
        self._state.planned_stints = list(stints_list)
        self.state_changed.emit()

    def update_stint(self, index: int, driver_name: Optional[str]) -> None:
        """
        Update driver assignment for a specific stint.

        Args:
            index: Stint index
            driver_name: Driver name or None
        """
        if 0 <= index < len(self._state.stints):
            self._state.stints[index] = driver_name
            self._state.planned_stints = list(self._state.stints)
            self.state_changed.emit()

    def add_penalty(self, reason: str, unit: str, value: int) -> None:
        """
        Add a penalty to the race.

        Args:
            reason: Penalty reason
            unit: "Laps" or "Time"
            value: Penalty value
        """
        from utils.time_utils import format_time

        penalty = Penalty(
            time=format_time(self.get_race_time()),
            reason=reason,
            unit=unit,
            value=value
        )
        self._state.penalties.append(penalty)
        self.state_changed.emit()

    def remove_penalty(self, index: int) -> None:
        """
        Remove penalty at given index.

        Args:
            index: Penalty index to remove
        """
        if 0 <= index < len(self._state.penalties):
            self._state.penalties.pop(index)
            self.state_changed.emit()

    def clear_penalties(self) -> None:
        """Clear all penalties."""
        self._state.penalties.clear()
        self.state_changed.emit()

    def add_driver(self, name: str) -> bool:
        """
        Add a new driver.

        Args:
            name: Driver name

        Returns:
            True if driver was added, False if already exists
        """
        if name in self.get_driver_names():
            return False

        self._drivers.append(Driver(name=name))
        self._state.driver_times[name] = 0.0
        self._save_drivers()
        self.drivers_changed.emit()
        return True

    def remove_driver(self, name: str) -> bool:
        """
        Remove a driver.

        Args:
            name: Driver name

        Returns:
            True if driver was removed, False if not found
        """
        for i, driver in enumerate(self._drivers):
            if driver.name == name:
                self._drivers.pop(i)
                self._state.driver_times.pop(name, None)
                self._save_drivers()
                self.drivers_changed.emit()
                return True
        return False

    def save_state(self) -> None:
        """Save current race state to autosave file."""
        try:
            with open(self._autosave_file, 'w', encoding='utf-8') as file:
                json.dump(self._state.to_dict(), file, indent=2)
        except Exception:
            pass

    def load_state(self) -> bool:
        """
        Load race state from autosave file.

        Returns:
            True if state was loaded successfully
        """
        if not self._autosave_file.exists():
            return False

        try:
            with open(self._autosave_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self._state = RaceState.from_dict(data)

            # Ensure all current drivers have entries in driver_times
            for driver_name in self.get_driver_names():
                if driver_name not in self._state.driver_times:
                    self._state.driver_times[driver_name] = 0.0

            self.state_changed.emit()
            return True
        except Exception:
            return False

    def _load_drivers(self) -> None:
        """Load drivers from JSON file."""
        if not self._drivers_file.exists():
            self._drivers = []
            return

        try:
            with open(self._drivers_file, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self._drivers = [Driver.from_dict(d) for d in data]

            # Initialize driver times
            for driver in self._drivers:
                if driver.name not in self._state.driver_times:
                    self._state.driver_times[driver.name] = 0.0
        except Exception:
            self._drivers = []

    def _save_drivers(self) -> None:
        """Save drivers to JSON file."""
        try:
            with open(self._drivers_file, 'w', encoding='utf-8') as file:
                data = [driver.to_dict() for driver in self._drivers]
                json.dump(data, file, indent=2)
        except Exception:
            pass

    def _on_timer_tick(self) -> None:
        """Handle timer tick event."""
        current_time = self.get_race_time()

        # Update current driver time
        current_driver = self._state.current_driver
        if current_driver:
            elapsed = current_time - self._state.last_pit_time
            self._state.driver_times[current_driver] = (
                    self._state.driver_times.get(current_driver, 0.0) + 1.0
            )

        self.timer_updated.emit(current_time)
