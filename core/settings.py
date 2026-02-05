import json
from pathlib import Path
from typing import Any

from core.logger import get_logger

logger = get_logger("settings")


class AppSettings:
    """
    A simple JSON-based settings manager that mimics a subset of QSettings API.
    Saves configuration to 'conf/settings.json' relative to the current working directory.
    """

    def __init__(self, filename: str = "settings.json") -> None:
        self._conf_dir = Path.cwd() / "conf"
        self._settings_path = self._conf_dir / filename
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self._settings_path.exists():
            return

        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings from {self._settings_path}: {e}")
            self._data = {}

    def _save(self) -> None:
        try:
            self._conf_dir.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save settings to {self._settings_path}: {e}")

    def value(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def setValue(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()
