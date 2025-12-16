from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QLineEdit, QGroupBox, QMessageBox, QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Qt, Slot, QThread, Signal

from controllers.race_controller import RaceController
from utils.geocode_util import geocode_address
from utils.time_utils import dms_to_decimal


class GeocodeThread(QThread):
    """Background thread for geocoding operations."""

    result_ready = Signal(bool, float, float, str)  # success, lat, lon, message

    def __init__(self, address: str):
        """
        Initialize geocode thread.

        Args:
            address: Address to geocode
        """
        super().__init__()
        self._address = address

    def run(self) -> None:
        """Execute geocoding in background."""
        try:
            lat, lon = geocode_address(self._address)
            if lat is not None and lon is not None:
                self.result_ready.emit(True, lat, lon, f"Address found: {self._address}")
            else:
                self.result_ready.emit(False, 0.0, 0.0, "Address not found!")
        except Exception as e:
            self.result_ready.emit(False, 0.0, 0.0, f"Geocoding error: {str(e)}")


class SettingsDialog(QDialog):
    """Dialog for race settings and configuration."""

    def __init__(self, controller: RaceController, parent=None):
        """
        Initialize settings dialog.

        Args:
            controller: Race controller instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._controller = controller
        self._geocode_thread: Optional[GeocodeThread] = None

        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        self._setup_ui()
        self._connect_signals()
        self._load_current_settings()

    def _setup_ui(self) -> None:
        """Set up user interface."""
        layout = QVBoxLayout(self)

        # Race duration settings
        duration_group = QGroupBox("Race Duration")
        duration_layout = QHBoxLayout()

        duration_layout.addWidget(QLabel("Hours:"))
        self._hours_spin = QSpinBox()
        self._hours_spin.setRange(0, 24)
        duration_layout.addWidget(self._hours_spin)

        duration_layout.addWidget(QLabel("Minutes:"))
        self._minutes_spin = QSpinBox()
        self._minutes_spin.setRange(0, 59)
        duration_layout.addWidget(self._minutes_spin)

        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)

        # Location settings
        location_group = QGroupBox("Weather Radar Location")
        location_layout = QVBoxLayout()

        # Address input
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel("Address:"))
        self._address_input = QLineEdit()
        address_layout.addWidget(self._address_input)
        self._geocode_btn = QPushButton("Search")
        address_layout.addWidget(self._geocode_btn)
        location_layout.addLayout(address_layout)

        # Coordinate input
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("Latitude:"))
        self._lat_input = QLineEdit()
        coord_layout.addWidget(self._lat_input)

        coord_layout.addWidget(QLabel("Longitude:"))
        self._lon_input = QLineEdit()
        coord_layout.addWidget(self._lon_input)

        self._update_coords_btn = QPushButton("Update")
        coord_layout.addWidget(self._update_coords_btn)
        location_layout.addLayout(coord_layout)

        self._location_status = QLabel("")
        location_layout.addWidget(self._location_status)

        location_group.setLayout(location_layout)
        layout.addWidget(location_group)

        # Driver management
        driver_group = QGroupBox("Manage Drivers")
        driver_layout = QVBoxLayout()

        self._driver_list = QListWidget()
        self._driver_list.setMaximumHeight(150)
        driver_layout.addWidget(self._driver_list)

        # Add driver
        add_layout = QHBoxLayout()
        self._new_driver_input = QLineEdit()
        self._new_driver_input.setPlaceholderText("Enter driver name")
        add_layout.addWidget(self._new_driver_input)
        self._add_driver_btn = QPushButton("➕ Add Driver")
        add_layout.addWidget(self._add_driver_btn)
        driver_layout.addLayout(add_layout)

        # Remove driver
        self._remove_driver_btn = QPushButton("🗑️ Remove Selected Driver")
        driver_layout.addWidget(self._remove_driver_btn)

        driver_group.setLayout(driver_layout)
        layout.addWidget(driver_group)

        # Backup/Restore
        backup_group = QGroupBox("Backup & Restore")
        backup_layout = QHBoxLayout()

        self._restore_btn = QPushButton("🔄 Restore from Autosave")
        backup_layout.addWidget(self._restore_btn)

        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # Dialog buttons
        button_layout = QHBoxLayout()
        self._ok_btn = QPushButton("OK")
        self._cancel_btn = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self._ok_btn)
        button_layout.addWidget(self._cancel_btn)
        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect signals and slots."""
        self._geocode_btn.clicked.connect(self._on_geocode_clicked)
        self._update_coords_btn.clicked.connect(self._on_update_coords_clicked)
        self._add_driver_btn.clicked.connect(self._on_add_driver_clicked)
        self._remove_driver_btn.clicked.connect(self._on_remove_driver_clicked)
        self._restore_btn.clicked.connect(self._on_restore_clicked)
        self._ok_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)

        self._controller.drivers_changed.connect(self._update_driver_list)

    def _load_current_settings(self) -> None:
        """Load current settings from controller."""
        state = self._controller.state

        self._hours_spin.setValue(state.race_duration_hours)
        self._minutes_spin.setValue(state.race_duration_minutes)
        self._lat_input.setText(str(state.latitude))
        self._lon_input.setText(str(state.longitude))
        self._address_input.setText(state.last_address)

        self._update_driver_list()

    @Slot()
    def _update_driver_list(self) -> None:
        """Update driver list display."""
        self._driver_list.clear()
        for driver_name in self._controller.get_driver_names():
            self._driver_list.addItem(driver_name)

    @Slot()
    def _on_geocode_clicked(self) -> None:
        """Handle geocode button click."""
        address = self._address_input.text().strip()
        if not address:
            return

        self._location_status.setText("⏳ Searching for address...")
        self._geocode_btn.setEnabled(False)

        self._geocode_thread = GeocodeThread(address)
        self._geocode_thread.result_ready.connect(self._on_geocode_result)
        self._geocode_thread.finished.connect(self._on_geocode_finished)
        self._geocode_thread.start()

    @Slot(bool, float, float, str)
    def _on_geocode_result(self, success: bool, lat: float, lon: float, message: str) -> None:
        """
        Handle geocoding result.

        Args:
            success: Whether geocoding was successful
            lat: Latitude coordinate
            lon: Longitude coordinate
            message: Status message
        """
        if success:
            self._lat_input.setText(str(lat))
            self._lon_input.setText(str(lon))
            self._location_status.setText(f"✅ {message}")
        else:
            self._location_status.setText(f"❌ {message}")

    @Slot()
    def _on_geocode_finished(self) -> None:
        """Handle geocoding thread completion."""
        self._geocode_btn.setEnabled(True)
        self._geocode_thread = None

    @Slot()
    def _on_update_coords_clicked(self) -> None:
        """Handle update coordinates button click."""
        lat_text = self._lat_input.text().strip()
        lon_text = self._lon_input.text().strip()

        try:
            # Try DMS format first
            if '°' in lat_text:
                lat = dms_to_decimal(lat_text)
            else:
                lat = float(lat_text)

            if '°' in lon_text:
                lon = dms_to_decimal(lon_text)
            else:
                lon = float(lon_text)

            self._lat_input.setText(str(lat))
            self._lon_input.setText(str(lon))
            self._location_status.setText("✅ Coordinates updated!")

        except ValueError as e:
            self._location_status.setText(
                "❌ Invalid coordinates! Use decimal (49.99, 14.37) or DMS (49°59'21.0\"N) format"
            )

    @Slot()
    def _on_add_driver_clicked(self) -> None:
        """Handle add driver button click."""
        name = self._new_driver_input.text().strip()
        if not name:
            return

        if self._controller.add_driver(name):
            self._new_driver_input.clear()
            QMessageBox.information(self, "Success", f"Added driver: {name}")
        else:
            QMessageBox.warning(self, "Warning", "Driver already exists!")

    @Slot()
    def _on_remove_driver_clicked(self) -> None:
        """Handle remove driver button click."""
        current_item = self._driver_list.currentItem()
        if not current_item:
            return

        driver_name = current_item.text()

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to remove driver '{driver_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self._controller.remove_driver(driver_name):
                QMessageBox.information(self, "Success", f"Removed driver: {driver_name}")

    @Slot()
    def _on_restore_clicked(self) -> None:
        """Handle restore from autosave button click."""
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "Are you sure you want to restore from autosave? Current state will be lost.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self._controller.load_state():
                QMessageBox.information(self, "Success", "State restored from autosave!")
                self._load_current_settings()
            else:
                QMessageBox.warning(self, "Error", "Failed to restore from autosave!")

    def get_settings(self) -> dict:
        """
        Get current settings from dialog.

        Returns:
            Dictionary containing settings
        """
        return {
            "race_duration_hours": self._hours_spin.value(),
            "race_duration_minutes": self._minutes_spin.value(),
            "latitude": float(self._lat_input.text()),
            "longitude": float(self._lon_input.text()),
            "last_address": self._address_input.text().strip()
        }
