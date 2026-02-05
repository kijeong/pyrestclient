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


def load_history_entries(path: str | Path, limit: int | None = None) -> list[HistoryEntry]:
    target_path = Path(path)
    if not target_path.exists():
        return []

    entries: list[HistoryEntry] = []
    with target_path.open(mode="r", encoding="utf-8") as file_handle:
        for line_number, line in enumerate(file_handle, start=1):
            payload_text = line.strip()
            if 0 == len(payload_text):
                continue
            try:
                payload = json.loads(payload_text)
                entries.append(_history_from_dict(payload))
            except Exception:
                logger.exception("Failed to parse history line %s", line_number)
    
    if limit is not None and limit > 0:
        return entries[-limit:]
    return entries


def default_history_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "history.jsonl"


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


def _history_from_dict(payload: Any) -> HistoryEntry:
    if not isinstance(payload, dict):
        raise ValueError("history payload must be an object")
    return HistoryEntry(
        timestamp=_require_str(payload, "timestamp"),
        name=_require_str(payload, "name"),
        method=_require_str(payload, "method"),
        url=_require_str(payload, "url"),
        status_code=_optional_int(payload, "status_code"),
        elapsed_ms=_optional_int(payload, "elapsed_ms"),
        error=_optional_str(payload, "error"),
    )


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or 0 == len(value):
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValueError(f"{key} must be an int")


def _optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError(f"{key} must be a string")
