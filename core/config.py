from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NetworkDefaults:
    timeout_ms: int = 10000
    verify_ssl: bool = True
    follow_redirects: bool = False
    trust_env: bool = True
