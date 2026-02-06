from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

# Import QtSvg to ensure SVG image format plugins are included by PyInstaller
import PySide6.QtSvg  # noqa: F401
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from core.logger import configure_logging, get_logger
from core.settings import AppSettings


def _handle_exception(exc_type: type[BaseException], exc: BaseException, tb: object) -> None:
    logger = get_logger("app")
    logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))

    message = "".join(traceback.format_exception(exc_type, exc, tb))
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "Unexpected Error", message)
    else:
        sys.stderr.write(message)


def main() -> None:
    settings = AppSettings()
    
    # Resolve base directory
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True.
        base_dir = Path(sys.executable).parent
        if hasattr(sys, "_MEIPASS"):
            # Onefile mode
            base_dir = Path(sys._MEIPASS)
        elif (base_dir / "_internal").exists():
            # Onedir mode (PyInstaller >= 6.0)
            base_dir = base_dir / "_internal"
    else:
        base_dir = Path(__file__).resolve().parent.parent

    # Configure logging
    log_level_str = settings.value("log_level")
    if not log_level_str:
        log_level_str = "DEBUG"
        settings.setValue("log_level", log_level_str)
    
    log_path_str = settings.value("log_path")
    if not log_path_str:
        # Default to installed path/logs/rest_client.log
        log_path_default = base_dir / "logs" / "rest_client.log"
        # Ensure log directory exists
        try:
            log_path_default.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback to user home if write permission fails
            log_path_default = Path.home() / ".rest_client" / "logs" / "rest_client.log"
            log_path_default.parent.mkdir(parents=True, exist_ok=True)
            
        log_path_str = str(log_path_default)
        settings.setValue("log_path", log_path_str)

    # Resolve log level
    log_level = logging.DEBUG
    if isinstance(log_level_str, str):
        level_upper = log_level_str.upper()
        log_level = getattr(logging, level_upper, logging.DEBUG)
    elif isinstance(log_level_str, int):
        log_level = log_level_str
        
    log_path = Path(log_path_str) if log_path_str else None
    
    configure_logging(log_path=log_path, level=log_level)
    
    logger = get_logger("app")
    logger.debug(f"Base directory: {base_dir}")
    logger.debug(f"Frozen state: {getattr(sys, 'frozen', False)}")
    
    sys.excepthook = _handle_exception

    app = QApplication([])
    app.setOrganizationName("Jiran")
    app.setApplicationName("RestClient")
    
    # Set Window Icon
    # Prefer PNG for window icon as it has better default support in Qt without plugins
    icon_path = base_dir / "resources" / "icons" / "app_icon.png"
    if not icon_path.exists():
         # Fallback to ICO if PNG missing
         icon_path = base_dir / "resources" / "icons" / "app_icon.ico"

    logger.debug(f"Looking for icon at: {icon_path}")
    if icon_path.exists():
        logger.debug("Icon file found, setting window icon.")
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        logger.warning(f"Icon file not found at {icon_path}")
    
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
