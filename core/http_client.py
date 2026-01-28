from __future__ import annotations

import httpx

from core.model import AuthType, RequestData, ResponseData


class HttpClient:
    def __init__(self, default_timeout_ms: int = 10000) -> None:
        self._default_timeout_ms = default_timeout_ms

    def send(self, request: RequestData) -> ResponseData:
        timeout_ms = request.timeout_ms
        if 0 >= timeout_ms:
            timeout_ms = self._default_timeout_ms

        headers = self._normalize_pairs(request.headers)
        params = self._normalize_pairs(request.params)

        auth = None
        if request.auth.auth_type is AuthType.BASIC:
            auth = httpx.BasicAuth(request.auth.username, request.auth.password)
        elif request.auth.auth_type is AuthType.BEARER:
            token = request.auth.token.strip()
            if 0 < len(token):
                headers.append(("Authorization", f"Bearer {token}"))

        body_text = request.body
        content = body_text if 0 < len(body_text.strip()) else None

        response = httpx.request(
            request.method,
            request.url,
            headers=headers if 0 < len(headers) else None,
            params=params if 0 < len(params) else None,
            content=content,
            timeout=httpx.Timeout(timeout_ms / 1000.0),
            auth=auth,
        )

        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        return ResponseData(
            status_code=response.status_code,
            headers=list(response.headers.items()),
            body=response.text,
            elapsed_ms=elapsed_ms,
        )

    @staticmethod
    def _normalize_pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
        normalized: list[tuple[str, str]] = []
        for key, value in pairs:
            key_text = key.strip()
            if 0 < len(key_text):
                normalized.append((key_text, value.strip()))
        return normalized
