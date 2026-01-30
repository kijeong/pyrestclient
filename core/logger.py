from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_PREFIX = "rest_client"
_DEFAULT_LOG_NAME = "rest_client.log"


def configure_logging(log_path: Path | None = None, level: int = logging.INFO) -> Path:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return Path(log_path) if log_path else _default_log_path()

    log_file = log_path or _default_log_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_file


def get_logger(name: str) -> logging.Logger:
    if name.startswith(_LOGGER_PREFIX):
        return logging.getLogger(name)
    return logging.getLogger(f"{_LOGGER_PREFIX}.{name}")


def _default_log_path() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "logs" / _DEFAULT_LOG_NAME
