from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, Slot


from controllers.race_controller import RaceController
from utils.time_utils import ordinal


class StintWidget(QWidget):
    """Widget for managing race stints."""

    def __init__(self, controller: RaceController):
        """
        Initialize stint widget.

        Args:
            controller: Race controller instance
        """
        super().__init__()

        self._controller = controller
        self._stint_combos = []
        self._setup_ui()
        self._connect_signals()
        self._update_stints()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Status info
        self._status_label = QLabel()
        layout.addWidget(self._status_label)

        # Stint list (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)

        self._stint_container = QWidget()
        self._stint_layout = QVBoxLayout(self._stint_container)
        scroll.setWidget(self._stint_container)

        layout.addWidget(scroll)

        # Add/Randomize controls
        controls_group = QGroupBox("Add / Randomize Stints")
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Number of stints:"))

        self._num_stints_spin = QSpinBox()
        self._num_stints_spin.setRange(1, 50)
        self._num_stints_spin.setValue(1)
        controls_layout.addWidget(self._num_stints_spin)

        self._add_btn = QPushButton("Add Stints")
        self._randomize_btn = QPushButton("Randomize Stints")

        controls_layout.addWidget(self._add_btn)
        controls_layout.addWidget(self._randomize_btn)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        # Pit stop button
        self._pit_stop_btn = QPushButton("🏁 Pit Stop")
        self._pit_stop_btn.setMinimumHeight(50)
        layout.addWidget(self._pit_stop_btn)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._add_btn.clicked.connect(self._on_add_stints)
        self._randomize_btn.clicked.connect(self._on_randomize_stints)
        self._pit_stop_btn.clicked.connect(self._on_pit_stop)

        self._controller.state_changed.connect(self._update_stints)
        self._controller.drivers_changed.connect(self._update_stints)

    @Slot()
    def _on_add_stints(self) -> None:
        """Handle add stints button click."""
        count = self._num_stints_spin.value()
        self._controller.add_stints(count)

    @Slot()
    def _on_randomize_stints(self) -> None:
        """Handle randomize stints button click."""
        self._controller.randomize_stints()

    @Slot()
    def _on_pit_stop(self) -> None:
        """Handle pit stop button click."""
        self._controller.pit_stop()

    @Slot(int)
    def _on_stint_changed(self, combo_index: int) -> None:
        """
        Handle stint driver selection change.

        Args:
            combo_index: Index of the combo box that changed
        """
        combo = self.sender()
        if not isinstance(combo, QComboBox):
            return

        driver_name = combo.currentText()
        if driver_name == "None":
            driver_name = None

        # Find stint index
        stint_index = self._stint_combos.index(combo)
        self._controller.update_stint(stint_index, driver_name)

    @Slot()
    def _update_stints(self) -> None:
        """Update stint display."""
        # Clear existing stint widgets
        while self._stint_layout.count():
            item = self._stint_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._stint_combos.clear()

        # Update status
        completed = self._controller.state.current_stint_idx
        total = len(self._controller.state.stints)
        remaining = total - completed

        status_text = f"🟢 Stints completed: {completed} | 🟡 Stints remaining: {remaining}"
        self._status_label.setText(status_text)

        # Create stint selection widgets
        driver_names = ["None"] + self._controller.get_driver_names()

        for i, driver in enumerate(self._controller.state.stints):
            stint_layout = QHBoxLayout()

            label = QLabel(f"{ordinal(i + 1)} Stint:")
            label.setMinimumWidth(80)
            stint_layout.addWidget(label)

            combo = QComboBox()
            combo.addItems(driver_names)

            if driver:
                index = combo.findText(driver)
                if index >= 0:
                    combo.setCurrentIndex(index)

            # Highlight current stint
            if i == self._controller.state.current_stint_idx:
                combo.setStyleSheet(
                    "background-color: rgb(58, 58, 58);"
                    "color: rgb(230, 230, 230);"
                )

            combo.currentIndexChanged.connect(
                lambda idx, c=i: self._on_stint_changed(c)
            )

            stint_layout.addWidget(combo)
            self._stint_combos.append(combo)

            self._stint_layout.addLayout(stint_layout)

        self._stint_layout.addStretch()
