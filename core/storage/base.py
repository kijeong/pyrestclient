from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.model import WorkspaceData


class WorkspaceStorage(ABC):
    @abstractmethod
    def load(self, path: Path) -> WorkspaceData:
        raise NotImplementedError

    @abstractmethod
    def save(self, path: Path, workspace: WorkspaceData) -> None:
        raise NotImplementedError
