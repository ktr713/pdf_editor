import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.utils.logging import configure_logging


def run() -> int:
    """Create and run the desktop application."""
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Overlay Editor")
    window = MainWindow()
    window.show()
    return app.exec()
