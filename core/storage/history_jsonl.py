from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.logger import get_logger
from core.model import HistoryEntry

logger = get_logger("history")


def append_history_entry(path: str | Path, entry: HistoryEntry) -> None:
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _history_to_dict(entry)
    line = json.dumps(payload, ensure_ascii=False)

    with target_path.open(mode="a", encoding="utf-8") as file_handle:
        file_handle.write(line + "\n")
        file_handle.flush()
        try:
            os.fsync(file_handle.fileno())
        except OSError:
            logger.exception("Failed to fsync history file")


def _history_to_dict(entry: HistoryEntry) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timestamp": entry.timestamp,
        "name": entry.name,
        "method": entry.method,
        "url": entry.url,
    }
    if entry.status_code is not None:
        payload["status_code"] = entry.status_code
    if entry.elapsed_ms is not None:
        payload["elapsed_ms"] = entry.elapsed_ms
    if entry.error:
        payload["error"] = entry.error
    return payload
