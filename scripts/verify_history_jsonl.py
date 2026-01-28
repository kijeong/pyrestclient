from __future__ import annotations

import datetime
import sys
from pathlib import Path


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


_ensure_repo_root()

from core.model import HistoryEntry
from core.storage.history_jsonl import append_history_entry


def build_entry(success: bool) -> HistoryEntry:
    timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    if success:
        return HistoryEntry(
            timestamp=timestamp,
            name="List Users",
            method="GET",
            url="https://httpbin.org/anything",
            status_code=200,
            elapsed_ms=321,
        )
    return HistoryEntry(
        timestamp=timestamp,
        name="List Users",
        method="GET",
        url="https://httpbin.org/delay/10",
        error="ReadTimeout",
    )


def main() -> None:
    path = Path("history_test.jsonl")
    append_history_entry(path=path, entry=build_entry(success=True))
    append_history_entry(path=path, entry=build_entry(success=False))
    print(f"History append OK: {path}")


if __name__ == "__main__":
    main()
