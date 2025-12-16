from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QGroupBox, QRadioButton
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from controllers.race_controller import RaceController
from utils.time_utils import format_time


class TimerWidget(QWidget):
    """Widget for displaying and controlling race timer."""

    def __init__(self, controller: RaceController):
        """
        Initialize timer widget.

        Args:
            controller: Race controller instance
        """
        super().__init__()

        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self._update_display()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Timer display
        self._time_label = QLabel("00:00:00 / 12:00:00")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self._time_label.setFont(font)
        self._time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._time_label)

        # Timer mode selection
        mode_group = QGroupBox("Timer Mode")
        mode_layout = QHBoxLayout()

        self._elapsed_radio = QRadioButton("Elapsed Time")
        self._remaining_radio = QRadioButton("Time Remaining")
        self._elapsed_radio.setChecked(True)

        mode_layout.addWidget(self._elapsed_radio)
        mode_layout.addWidget(self._remaining_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self._start_btn = QPushButton("▶️ Start")
        self._pause_btn = QPushButton("⏸️ Pause")
        self._reset_btn = QPushButton("⏹️ Reset")

        button_layout.addWidget(self._start_btn)
        button_layout.addWidget(self._pause_btn)
        button_layout.addWidget(self._reset_btn)

        layout.addLayout(button_layout)

        # Manual time setting
        manual_group = QGroupBox("Set Timer Manually")
        manual_layout = QHBoxLayout()

        manual_layout.addWidget(QLabel("Hours:"))
        self._hours_spin = QSpinBox()
        self._hours_spin.setRange(0, 24)
        manual_layout.addWidget(self._hours_spin)

        manual_layout.addWidget(QLabel("Minutes:"))
        self._minutes_spin = QSpinBox()
        self._minutes_spin.setRange(0, 59)
        manual_layout.addWidget(self._minutes_spin)

        self._set_time_btn = QPushButton("Set Timer")
        manual_layout.addWidget(self._set_time_btn)

        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._start_btn.clicked.connect(self._on_start_clicked)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._reset_btn.clicked.connect(self._on_reset_clicked)
        self._set_time_btn.clicked.connect(self._on_set_time_clicked)

        self._elapsed_radio.toggled.connect(self._on_timer_mode_changed)

        self._controller.timer_updated.connect(self._update_display)
        self._controller.state_changed.connect(self._update_display)

    @Slot()
    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        self._controller.start_race()

    @Slot()
    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        self._controller.pause_race()

    @Slot()
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        self._controller.reset_race()

    @Slot()
    def _on_set_time_clicked(self) -> None:
        """Handle set time button click."""
        hours = self._hours_spin.value()
        minutes = self._minutes_spin.value()
        self._controller.set_manual_time(hours, minutes)

    @Slot(bool)
    def _on_timer_mode_changed(self, checked: bool) -> None:
        """Handle timer mode change."""
        if checked:
            self._controller.state.timer_mode = "elapsed"
        else:
            self._controller.state.timer_mode = "remaining"
        self._update_display()

    @Slot()
    def _update_display(self) -> None:
        """Update timer display."""
        current_time = self._controller.get_race_time()
        total_time = self._controller.state.total_race_seconds

        if self._controller.state.timer_mode == "elapsed":
            display_time = current_time
        else:
            display_time = max(total_time - current_time, 0)

        time_str = f"{format_time(display_time)} / {format_time(total_time)}"
        self._time_label.setText(time_str)
