from __future__ import annotations

import re
from typing import Mapping

from core.model import AuthConfig, AuthType, NetworkConfig, RequestData

_TEMPLATE_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


def render_text(text: str, variables: Mapping[str, str]) -> str:
    if 0 == len(text) or 0 == len(variables):
        return text

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return _TEMPLATE_PATTERN.sub(_replace, text)


def render_pairs(pairs: list[tuple[str, str]], variables: Mapping[str, str]) -> list[tuple[str, str]]:
    return [(render_text(key, variables), render_text(value, variables)) for key, value in pairs]


def render_auth(auth: AuthConfig, variables: Mapping[str, str]) -> AuthConfig:
    if auth.auth_type is AuthType.BASIC:
        return AuthConfig.basic(
            render_text(auth.username, variables),
            render_text(auth.password, variables),
        )
    if auth.auth_type is AuthType.BEARER:
        return AuthConfig.bearer(render_text(auth.token, variables))
    return AuthConfig.none()


def render_network(network: NetworkConfig, variables: Mapping[str, str]) -> NetworkConfig:
    return NetworkConfig(
        proxy_url=render_text(network.proxy_url, variables),
        verify_ssl=network.verify_ssl,
        follow_redirects=network.follow_redirects,
        trust_env=network.trust_env,
    )


def render_request(request: RequestData, variables: Mapping[str, str]) -> RequestData:
    if 0 == len(variables):
        return request

    return RequestData(
        name=request.name,
        method=request.method,
        url=render_text(request.url, variables),
        headers=render_pairs(request.headers, variables),
        params=render_pairs(request.params, variables),
        body=render_text(request.body, variables),
        form_fields=render_pairs(request.form_fields, variables),
        files=render_pairs(request.files, variables),
        body_type=request.body_type,
        auth=render_auth(request.auth, variables),
        timeout_ms=request.timeout_ms,
        network=render_network(request.network, variables),
    )
