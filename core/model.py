from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"


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
