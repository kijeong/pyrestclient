from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

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
    
    # Configure logging
    log_level_str = settings.value("log_level")
    if not log_level_str:
        log_level_str = "DEBUG"
        settings.setValue("log_level", log_level_str)

    log_path_str = settings.value("log_path")
    if not log_path_str:
        # Default to installed path/logs/rest_client.log
        base_dir = Path(__file__).resolve().parent.parent
        log_path_default = base_dir / "logs" / "rest_client.log"
        log_path_str = str(log_path_default)
        settings.setValue("log_path", log_path_str)

    # Resolve log level
    log_level = logging.DEBUG
    if isinstance(log_level_str, str):
        level_upper = log_level_str.upper()
        # logging.getLevelName returns int for string input (in most cases) or we can use getattr
        # Ideally use getattr to be safe with constants
        log_level = getattr(logging, level_upper, logging.DEBUG)
    elif isinstance(log_level_str, int):
        log_level = log_level_str
        
    log_path = Path(log_path_str) if log_path_str else None
    
    configure_logging(log_path=log_path, level=log_level)
    
    sys.excepthook = _handle_exception

    app = QApplication([])
    app.setOrganizationName("Jiran")
    app.setApplicationName("RestClient")
    
    # Set Window Icon
    base_dir = Path(__file__).resolve().parent.parent
    icon_path = base_dir / "resources" / "icons" / "app_icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
