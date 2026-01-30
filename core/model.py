from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"


class EnvironmentScope(Enum):
    GLOBAL = "global"
    COLLECTION = "collection"
    REQUEST = "request"


@dataclass(slots=True)
class AuthConfig:
    auth_type: AuthType
    username: str = ""
    password: str = ""
    token: str = ""

    @classmethod
    def none(cls) -> "AuthConfig":
        return cls(auth_type=AuthType.NONE)

    @classmethod
    def basic(cls, username: str, password: str) -> "AuthConfig":
        return cls(auth_type=AuthType.BASIC, username=username, password=password)

    @classmethod
    def bearer(cls, token: str) -> "AuthConfig":
        return cls(auth_type=AuthType.BEARER, token=token)


@dataclass(slots=True)
class NetworkConfig:
    proxy_url: str = ""
    verify_ssl: bool = True
    follow_redirects: bool = False
    trust_env: bool = True


@dataclass(slots=True)
class RequestData:
    name: str
    method: str
    url: str
    headers: list[tuple[str, str]] = field(default_factory=list)
    params: list[tuple[str, str]] = field(default_factory=list)
    body: str = ""
    form_fields: list[tuple[str, str]] = field(default_factory=list)
    files: list[tuple[str, str]] = field(default_factory=list)
    body_type: str = "raw"  # raw, multipart
    auth: AuthConfig = field(default_factory=AuthConfig.none)
    timeout_ms: int = 10000
    network: NetworkConfig = field(default_factory=NetworkConfig)


@dataclass(slots=True)
class ResponseData:
    status_code: int
    headers: list[tuple[str, str]]
    body: str
    elapsed_ms: int
    error: str | None = None


@dataclass(slots=True)
class HistoryEntry:
    timestamp: str
    name: str
    method: str
    url: str
    status_code: int | None = None
    elapsed_ms: int | None = None
    error: str | None = None


@dataclass(slots=True)
class WorkspaceCollection:
    id: str
    name: str
    description: str = ""


@dataclass(slots=True)
class WorkspaceFolder:
    id: str
    collection_id: str
    parent_id: str | None
    name: str
    order: int = 0


@dataclass(slots=True)
class WorkspaceRequest:
    id: str
    folder_id: str
    name: str
    method: str
    url: str
    headers: list[tuple[str, str]] = field(default_factory=list)
    params: list[tuple[str, str]] = field(default_factory=list)
    body: str = ""
    form_fields: list[tuple[str, str]] = field(default_factory=list)
    files: list[tuple[str, str]] = field(default_factory=list)
    body_type: str = "raw"  # raw, multipart
    auth: AuthConfig = field(default_factory=AuthConfig.none)
    timeout_ms: int = 10000
    network: NetworkConfig = field(default_factory=NetworkConfig)


@dataclass(slots=True)
class WorkspaceEnvironment:
    scope: EnvironmentScope
    owner_id: str | None
    variables: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class WorkspaceData:
    schema_version: int
    updated_at: str | None = None
    collections: list[WorkspaceCollection] = field(default_factory=list)
    folders: list[WorkspaceFolder] = field(default_factory=list)
    requests: list[WorkspaceRequest] = field(default_factory=list)
    environments: list[WorkspaceEnvironment] = field(default_factory=list)
