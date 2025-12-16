import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QListWidget, QMessageBox,
    QHeaderView
)
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QColor

from controllers.race_controller import RaceController
from views.timer_widget import TimerWidget
from views.stint_widget import StintWidget
from views.settings_dialog import SettingsDialog
from utils.time_utils import format_time


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, controller: RaceController):
        """
        Initialize main window.

        Args:
            controller: Race controller instance
        """
        super().__init__()

        self._controller = controller

        self.setWindowTitle("Kart Endurance Manager")
        self.setMinimumSize(1200, 800)

        self._setup_ui()
        self._connect_signals()
        self._update_all()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("Kart Endurance Manager")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Settings button
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        self._settings_btn = QPushButton("⚙️ Settings")
        settings_layout.addWidget(self._settings_btn)
        main_layout.addLayout(settings_layout)

        # Tab widget for main content
        tabs = QTabWidget()

        # Race tab
        race_tab = self._create_race_tab()
        tabs.addTab(race_tab, "🏁 Race")

        # Statistics tab
        stats_tab = self._create_stats_tab()
        tabs.addTab(stats_tab, "📊 Statistics")

        # Penalties tab
        penalties_tab = self._create_penalties_tab()
        tabs.addTab(penalties_tab, "⚠️ Penalties")

        # Weather tab
        weather_tab = self._create_weather_tab()
        tabs.addTab(weather_tab, "🌦️ Weather")

        main_layout.addWidget(tabs)

    def _create_race_tab(self) -> QWidget:
        """
        Create race management tab.

        Returns:
            Race tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Timer widget
        self._timer_widget = TimerWidget(self._controller)
        layout.addWidget(self._timer_widget)

        # Stint widget
        self._stint_widget = StintWidget(self._controller)
        layout.addWidget(self._stint_widget)

        return widget

    def _create_stats_tab(self) -> QWidget:
        """
        Create statistics tab.

        Returns:
            Statistics tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Driver Times & Stint Statistics"))

        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(5)
        self._stats_table.setHorizontalHeaderLabels([
            "Driver", "Time", "Driven Stints", "Planned Stints", "Remaining Stints"
        ])

        header = self._stats_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self._stats_table)

        return widget

    def _create_penalties_tab(self) -> QWidget:
        """
        Create penalties management tab.

        Returns:
            Penalties tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add penalty form
        form_group = QGroupBox("Add Penalty")
        form_layout = QHBoxLayout()

        form_layout.addWidget(QLabel("Reason:"))
        self._penalty_reason = QLineEdit()
        form_layout.addWidget(self._penalty_reason)

        form_layout.addWidget(QLabel("Unit:"))
        self._penalty_unit = QComboBox()
        self._penalty_unit.addItems(["Laps", "Time"])
        form_layout.addWidget(self._penalty_unit)

        form_layout.addWidget(QLabel("Value:"))
        self._penalty_value = QSpinBox()
        self._penalty_value.setRange(0, 1000)
        form_layout.addWidget(self._penalty_value)

        self._add_penalty_btn = QPushButton("➕ Add Penalty")
        form_layout.addWidget(self._add_penalty_btn)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Penalty list
        layout.addWidget(QLabel("Penalty Log"))

        self._penalty_table = QTableWidget()
        self._penalty_table.setColumnCount(4)
        self._penalty_table.setHorizontalHeaderLabels([
            "Time", "Reason", "Unit", "Value"
        ])

        header = self._penalty_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self._penalty_table)

        # Delete buttons
        button_layout = QHBoxLayout()
        self._delete_penalty_btn = QPushButton("🗑️ Delete Selected")
        self._clear_penalties_btn = QPushButton("Clear All Penalties")
        button_layout.addWidget(self._delete_penalty_btn)
        button_layout.addWidget(self._clear_penalties_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        return widget

    def _create_weather_tab(self) -> QWidget:
        """
        Create weather radar tab.

        Returns:
            Weather tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Weather Radar"))

        self._weather_view = QWebEngineView()
        layout.addWidget(self._weather_view)

        self._coords_label = QLabel()
        layout.addWidget(self._coords_label)

        return widget

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._settings_btn.clicked.connect(self._on_settings_clicked)
        self._add_penalty_btn.clicked.connect(self._on_add_penalty_clicked)
        self._delete_penalty_btn.clicked.connect(self._on_delete_penalty_clicked)
        self._clear_penalties_btn.clicked.connect(self._on_clear_penalties_clicked)

        self._controller.state_changed.connect(self._update_all)
        self._controller.timer_updated.connect(self._update_stats)

    @Slot()
    def _on_settings_clicked(self) -> None:
        """Handle settings button click."""
        dialog = SettingsDialog(self._controller, self)
        if dialog.exec():
            settings = dialog.get_settings()

            # Update controller state
            state = self._controller.state
            state.race_duration_hours = settings["race_duration_hours"]
            state.race_duration_minutes = settings["race_duration_minutes"]
            state.latitude = settings["latitude"]
            state.longitude = settings["longitude"]
            state.last_address = settings["last_address"]

            self._update_weather()

    @Slot()
    def _on_add_penalty_clicked(self) -> None:
        """Handle add penalty button click."""
        reason = self._penalty_reason.text().strip()
        if not reason:
            QMessageBox.warning(self, "Warning", "Please enter a penalty reason!")
            return

        unit = self._penalty_unit.currentText()
        value = self._penalty_value.value()

        self._controller.add_penalty(reason, unit, value)

        # Clear form
        self._penalty_reason.clear()
        self._penalty_value.setValue(0)

    @Slot()
    def _on_delete_penalty_clicked(self) -> None:
        """Handle delete penalty button click."""
        current_row = self._penalty_table.currentRow()
        if current_row < 0:
            return

        self._controller.remove_penalty(current_row)

    @Slot()
    def _on_clear_penalties_clicked(self) -> None:
        """Handle clear all penalties button click."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all penalties?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._controller.clear_penalties()

    @Slot()
    def _update_all(self) -> None:
        """Update all UI components."""
        self._update_stats()
        self._update_penalties()
        self._update_weather()

    @Slot()
    def _update_stats(self) -> None:
        """Update statistics table."""
        driver_names = self._controller.get_driver_names()
        state = self._controller.state

        self._stats_table.setRowCount(len(driver_names))

        current_driver = state.current_driver

        for i, driver_name in enumerate(driver_names):
            # Calculate statistics
            driven_stints = sum(
                1 for s in state.stints[:state.current_stint_idx]
                if s == driver_name
            )
            planned_stints = state.planned_stints.count(driver_name)
            remaining_stints = planned_stints - driven_stints

            # Driver name
            name_item = QTableWidgetItem(driver_name)
            if driver_name == current_driver:
                name_item.setBackground(QColor(58, 58, 58))
                name_item.setForeground(QColor(230, 230, 230))
            self._stats_table.setItem(i, 0, name_item)

            # Time
            time_str = format_time(state.driver_times.get(driver_name, 0.0))
            self._stats_table.setItem(i, 1, QTableWidgetItem(time_str))

            # Driven stints
            self._stats_table.setItem(i, 2, QTableWidgetItem(str(driven_stints)))

            # Planned stints
            self._stats_table.setItem(i, 3, QTableWidgetItem(str(planned_stints)))

            # Remaining stints
            self._stats_table.setItem(i, 4, QTableWidgetItem(str(remaining_stints)))

    @Slot()
    def _update_penalties(self) -> None:
        """Update penalties table."""
        penalties = self._controller.state.penalties

        self._penalty_table.setRowCount(len(penalties))

        for i, penalty in enumerate(penalties):
            self._penalty_table.setItem(i, 0, QTableWidgetItem(penalty.time))
            self._penalty_table.setItem(i, 1, QTableWidgetItem(penalty.reason))
            self._penalty_table.setItem(i, 2, QTableWidgetItem(penalty.unit))
            self._penalty_table.setItem(i, 3, QTableWidgetItem(str(penalty.value)))

    @Slot()
    def _update_weather(self) -> None:
        """Update weather radar display."""
        state = self._controller.state

        url = (
            f"https://embed.windy.com/embed2.html?"
            f"lat={state.latitude}&lon={state.longitude}&zoom=12"
            f"&level=surface&overlay=rain&menu=&message=true&marker=true"
            f"&calendar=&pressure=&type=map&location=coordinates&detail="
            f"&detailLat={state.latitude}&detailLon={state.longitude}"
            f"&metricWind=default&metricTemp=default&radarRange=-1"
        )

        self._weather_view.setUrl(QUrl(url))
        self._coords_label.setText(
            f"Coordinates: {state.latitude:.6f}, {state.longitude:.6f}"
        )
