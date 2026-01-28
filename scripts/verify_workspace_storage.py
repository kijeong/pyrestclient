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

from core.model import (
    AuthConfig,
    EnvironmentScope,
    NetworkConfig,
    WorkspaceCollection,
    WorkspaceData,
    WorkspaceEnvironment,
    WorkspaceFolder,
    WorkspaceRequest,
)
from core.storage.json_storage import load_workspace, save_workspace


def build_sample_workspace() -> WorkspaceData:
    return WorkspaceData(
        schema_version=1,
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        collections=[
            WorkspaceCollection(
                id="col-1",
                name="Default",
                description="Sample collection",
            )
        ],
        folders=[
            WorkspaceFolder(
                id="fld-1",
                collection_id="col-1",
                parent_id=None,
                name="Users",
                order=0,
            )
        ],
        requests=[
            WorkspaceRequest(
                id="req-1",
                folder_id="fld-1",
                name="List Users",
                method="GET",
                url="https://httpbin.org/anything",
                headers=[("Accept", "application/json")],
                params=[("limit", "25"), ("offset", "0")],
                body="",
                auth=AuthConfig.none(),
                timeout_ms=10000,
                network=NetworkConfig(
                    proxy_url="",
                    verify_ssl=True,
                    follow_redirects=False,
                    trust_env=True,
                ),
            )
        ],
        environments=[
            WorkspaceEnvironment(
                scope=EnvironmentScope.GLOBAL,
                owner_id=None,
                variables={
                    "base_url": "https://httpbin.org",
                    "env_name": "dev",
                },
            )
        ],
    )


def verify_roundtrip(path: Path) -> None:
    workspace = build_sample_workspace()
    save_workspace(path=path, workspace=workspace)
    loaded = load_workspace(path=path)

    if loaded != workspace:
        raise AssertionError("Workspace roundtrip mismatch")

    print(f"Workspace save/load OK: {path}")


def main() -> None:
    path = Path("workspace_test.json")
    verify_roundtrip(path=path)


if __name__ == "__main__":
    main()
