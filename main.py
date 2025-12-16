import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from controllers.race_controller import RaceController
from views.main_window import MainWindow


def main() -> int:
    """
    Main application entry point.

    Returns:
        Exit code
    """
    if getattr(sys, "frozen", False):
        # läuft als EXE
        base_dir = Path(sys._MEIPASS)
    else:
        # läuft als Skript
        base_dir = Path(__file__).parent


    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Kart Endurance Manager")

    # Apply stylesheet
    stylesheet_path = base_dir / "resources" / "styles.qss"
    if stylesheet_path.exists():
        with open(stylesheet_path, 'r', encoding='utf-8') as file:
            app.setStyleSheet(file.read())

    # Create controller and main window
    controller = RaceController(base_dir)
    window = MainWindow(controller)
    window.show()

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
