from __future__ import annotations

import logging
import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from core.logger import configure_logging, get_logger


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
    configure_logging(level=logging.DEBUG)
    sys.excepthook = _handle_exception

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
