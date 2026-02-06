from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from core.logger import get_logger
from core.model import (
    AuthConfig,
    AuthType,
    EnvironmentScope,
    NetworkConfig,
    WorkspaceCollection,
    WorkspaceData,
    WorkspaceEnvironment,
    WorkspaceFolder,
    WorkspaceRequest,
)
from core.storage.base import WorkspaceStorage

SCHEMA_VERSION = 1

logger = get_logger("storage")


class JsonWorkspaceStorage(WorkspaceStorage):
    def __init__(self, schema_version: int = SCHEMA_VERSION) -> None:
        self._schema_version = schema_version

    def load(self, path: Path) -> WorkspaceData:
        with path.open(mode="r", encoding="utf-8") as file_handle:
            payload = json.load(fp=file_handle)
        return _workspace_from_dict(payload)

    def save(self, path: Path, workspace: WorkspaceData) -> None:
        payload = _workspace_to_dict(workspace, schema_version=self._schema_version)
        _atomic_write_json(path, payload)


def load_workspace(path: str | Path) -> WorkspaceData:
    storage = JsonWorkspaceStorage()
    return storage.load(Path(path))


def save_workspace(path: str | Path, workspace: WorkspaceData) -> None:
    storage = JsonWorkspaceStorage()
    storage.save(Path(path), workspace)


def _workspace_to_dict(workspace: WorkspaceData, schema_version: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "collections": [_collection_to_dict(item) for item in workspace.collections],
        "folders": [_folder_to_dict(item) for item in workspace.folders],
        "requests": [_request_to_dict(item) for item in workspace.requests],
        "environments": [_environment_to_dict(item) for item in workspace.environments],
    }
    if workspace.updated_at is not None:
        payload["updated_at"] = workspace.updated_at
    return payload


def _workspace_from_dict(payload: Any) -> WorkspaceData:
    if not isinstance(payload, dict):
        raise ValueError("workspace payload must be an object")

    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, int):
        raise ValueError("schema_version must be an int")

    updated_at_value = payload.get("updated_at")
    updated_at = _read_str(updated_at_value)

    collections = [
        _collection_from_dict(item) for item in _read_list(payload.get("collections"))
    ]
    folders = [_folder_from_dict(item) for item in _read_list(payload.get("folders"))]
    requests = [_request_from_dict(item) for item in _read_list(payload.get("requests"))]
    environments = [
        _environment_from_dict(item) for item in _read_list(payload.get("environments"))
    ]

    return WorkspaceData(
        schema_version=schema_version,
        updated_at=updated_at,
        collections=collections,
        folders=folders,
        requests=requests,
        environments=environments,
    )


def _collection_to_dict(item: WorkspaceCollection) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item.id,
        "name": item.name,
    }
    if 0 < len(item.description):
        payload["description"] = item.description
    return payload


def _collection_from_dict(payload: Any) -> WorkspaceCollection:
    data = _read_dict(payload)
    return WorkspaceCollection(
        id=_require_str(data, "id"),
        name=_require_str(data, "name"),
        description=_read_str(data.get("description")) or "",
    )


def _folder_to_dict(item: WorkspaceFolder) -> dict[str, Any]:
    return {
        "id": item.id,
        "collection_id": item.collection_id,
        "parent_id": item.parent_id,
        "name": item.name,
        "order": item.order,
    }


def _folder_from_dict(payload: Any) -> WorkspaceFolder:
    data = _read_dict(payload)
    parent_id = _read_str(data.get("parent_id"))
    return WorkspaceFolder(
        id=_require_str(data, "id"),
        collection_id=_require_str(data, "collection_id"),
        parent_id=parent_id,
        name=_require_str(data, "name"),
        order=_read_int(data, "order", default=0),
    )


def _request_to_dict(item: WorkspaceRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item.id,
        "folder_id": item.folder_id,
        "name": item.name,
        "method": item.method,
        "url": item.url,
        "headers": _pairs_to_dict_list(item.headers),
        "params": _pairs_to_dict_list(item.params),
        "body": item.body,
        "form_fields": _pairs_to_dict_list(item.form_fields),
        "files": _pairs_to_dict_list(item.files),
        "body_type": item.body_type,
        "auth": _auth_to_dict(item.auth),
        "timeout_ms": item.timeout_ms,
        "network": _network_to_dict(item.network),
    }
    return payload


def _request_from_dict(payload: Any) -> WorkspaceRequest:
    data = _read_dict(payload)
    return WorkspaceRequest(
        id=_require_str(data, "id"),
        folder_id=_require_str(data, "folder_id"),
        name=_require_str(data, "name"),
        method=_require_str(data, "method"),
        url=_require_str(data, "url"),
        headers=_pairs_from_dict_list(data.get("headers")),
        params=_pairs_from_dict_list(data.get("params")),
        body=_read_str(data.get("body")) or "",
        form_fields=_pairs_from_dict_list(data.get("form_fields")),
        files=_pairs_from_dict_list(data.get("files")),
        body_type=_read_str(data.get("body_type")) or "raw",
        auth=_auth_from_dict(_read_dict(data.get("auth"))),
        timeout_ms=_read_int(data, "timeout_ms", default=10000),
        network=_network_from_dict(_read_dict(data.get("network"))),
    )


def _environment_to_dict(item: WorkspaceEnvironment) -> dict[str, Any]:
    return {
        "scope": item.scope.value,
        "owner_id": item.owner_id,
        "variables": dict(item.variables),
    }


def _environment_from_dict(payload: Any) -> WorkspaceEnvironment:
    data = _read_dict(payload)
    scope_value = _read_str(data.get("scope")) or EnvironmentScope.GLOBAL.value
    scope = _parse_scope(scope_value)
    owner_id = _read_str(data.get("owner_id"))
    variables = _read_dict(data.get("variables"))
    return WorkspaceEnvironment(
        scope=scope,
        owner_id=owner_id,
        variables={str(key): str(value) for key, value in variables.items()},
    )


def _auth_to_dict(auth: AuthConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": auth.auth_type.value}
    if auth.auth_type is AuthType.BASIC:
        payload["username"] = auth.username
        payload["password"] = auth.password
    elif auth.auth_type is AuthType.BEARER:
        payload["token"] = auth.token
    return payload


def _auth_from_dict(payload: dict[str, Any]) -> AuthConfig:
    auth_type_value = _read_str(payload.get("type")) or AuthType.NONE.value
    try:
        auth_type = AuthType(auth_type_value)
    except ValueError:
        logger.warning("Unknown auth type: %s", auth_type_value)
        auth_type = AuthType.NONE

    if auth_type is AuthType.BASIC:
        return AuthConfig.basic(
            username=_read_str(payload.get("username")) or "",
            password=_read_str(payload.get("password")) or "",
        )

    if auth_type is AuthType.BEARER:
        return AuthConfig.bearer(token=_read_str(payload.get("token")) or "")

    return AuthConfig.none()


def _network_to_dict(network: NetworkConfig) -> dict[str, Any]:
    return {
        "proxy_url": network.proxy_url,
        "verify_ssl": network.verify_ssl,
        "follow_redirects": network.follow_redirects,
        "trust_env": network.trust_env,
    }


def _network_from_dict(payload: dict[str, Any]) -> NetworkConfig:
    return NetworkConfig(
        proxy_url=_read_str(payload.get("proxy_url")) or "",
        verify_ssl=_read_bool(payload, "verify_ssl", default=True),
        follow_redirects=_read_bool(payload, "follow_redirects", default=False),
        trust_env=_read_bool(payload, "trust_env", default=True),
    )


def _pairs_to_dict_list(pairs: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"key": key, "value": value} for key, value in pairs]


def _pairs_from_dict_list(items: Any) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for item in _read_list(items):
        if not isinstance(item, dict):
            continue
        key = _read_str(item.get("key"))
        if key is None or 0 == len(key):
            continue
        value = _read_str(item.get("value")) or ""
        result.append((key, value))
    return result


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use mkstemp instead of NamedTemporaryFile to avoid file locking issues on Windows
    fd, temp_path_str = tempfile.mkstemp(dir=str(path.parent), text=True)
    # Close the low-level handle immediately so we can open it cleanly
    os.close(fd)
    
    temp_path = Path(temp_path_str)

    try:
        with temp_path.open("w", encoding="utf-8") as temp_file:
            json.dump(obj=payload, fp=temp_file, ensure_ascii=False, indent=2)
            temp_file.flush()
            try:
                os.fsync(temp_file.fileno())
            except OSError:
                logger.exception("Failed to fsync temp file")

        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    except Exception:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                logger.exception("Failed to remove temp file")
        raise


def _fsync_directory(path: Path) -> None:
    if not hasattr(os, "O_DIRECTORY"):
        return

    try:
        dir_fd = os.open(path, os.O_DIRECTORY)
    except OSError:
        logger.exception("Failed to open directory for fsync")
        return

    try:
        os.fsync(dir_fd)
    except OSError:
        logger.exception("Failed to fsync directory")
    finally:
        os.close(dir_fd)


def _read_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _read_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _read_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _require_str(data: dict[str, Any], key: str) -> str:
    value = _read_str(data.get(key))
    if value is None or 0 == len(value):
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _read_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key)
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


def _read_bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key)
    if isinstance(value, bool):
        return value
    return default


def _parse_scope(scope_value: str) -> EnvironmentScope:
    try:
        return EnvironmentScope(scope_value)
    except ValueError:
        logger.warning("Unknown environment scope: %s", scope_value)
        return EnvironmentScope.GLOBAL
