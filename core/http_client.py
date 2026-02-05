from __future__ import annotations

import contextlib
from pathlib import Path

import httpx

from core.logger import get_logger
from core.model import AuthType, RequestData, ResponseData

logger = get_logger("http_client")


class HttpClient:
    def __init__(self, default_timeout_ms: int = 10000) -> None:
        self._default_timeout_ms = default_timeout_ms

    def create_client(self, request: RequestData) -> httpx.Client:
        timeout_ms = request.timeout_ms
        if 0 >= timeout_ms:
            timeout_ms = self._default_timeout_ms

        return httpx.Client(
            timeout=httpx.Timeout(timeout_ms / 1000.0),
            verify=request.network.verify_ssl,
            proxy=request.network.proxy_url or None,
            follow_redirects=request.network.follow_redirects,
            trust_env=request.network.trust_env,
        )

    def send(self, request: RequestData, client: httpx.Client | None = None) -> ResponseData:
        timeout_ms = request.timeout_ms
        if 0 >= timeout_ms:
            timeout_ms = self._default_timeout_ms

        headers = self._normalize_pairs(request.headers)
        params = self._normalize_pairs(request.params)

        # Set default User-Agent if not present
        if not any(key.lower() == "user-agent" for key, _ in headers):
            headers.append(("User-Agent", "jiran-restclient"))

        # For multipart requests, remove Content-Type header so httpx can set it with boundary
        if request.body_type == "multipart":
            headers_count = len(headers)
            headers = [h for h in headers if h[0].lower() != "content-type"]
            if len(headers) < headers_count:
                logger.debug("Removed explicit Content-Type header for multipart request")

        auth = None
        if request.auth.auth_type is AuthType.BASIC:
            auth = httpx.BasicAuth(request.auth.username, request.auth.password)
        elif request.auth.auth_type is AuthType.BEARER:
            token = request.auth.token.strip()
            if 0 < len(token):
                headers.append(("Authorization", f"Bearer {token}"))

        timeout = httpx.Timeout(timeout_ms / 1000.0)

        request_kwargs = {
            "headers": headers if 0 < len(headers) else None,
            "params": params if 0 < len(params) else None,
            "timeout": timeout,
            "auth": auth,
            "follow_redirects": request.network.follow_redirects,
        }

        # Use ExitStack to ensure files are closed properly
        with contextlib.ExitStack() as stack:
            if request.body_type == "multipart":
                files_payload = []
                for key, path_str in request.files:
                    path_str = path_str.strip()
                    if not path_str:
                        continue
                    try:
                        file_path = Path(path_str)
                        # Open file and register for closing
                        f = stack.enter_context(open(file_path, "rb"))
                        content = f.read()
                        # (filename, content)
                        files_payload.append((key, (file_path.name, content)))
                    except OSError as e:
                        logger.error(f"Failed to open file '{path_str}': {e}")
                        # We might want to stop here or proceed. 
                        # For now, let's allow it to fail at httpx level or proceed partially.
                        # But typically if a user uploads a file, they expect it to be there.
                        # Let's assume valid paths for now or user catches log.
                
                # Form fields as data (list of tuples handles duplicates)
                data_payload = request.form_fields
                
                request_kwargs["files"] = files_payload
                if data_payload:
                    request_kwargs["data"] = data_payload
                
            else:
                # Raw body
                body_text = request.body
                content = body_text if 0 < len(body_text.strip()) else None
                request_kwargs["content"] = content

            # --- Debug Logging ---
            logger.debug("=== Request Details ===")
            logger.debug(f"Method: {request.method}")
            logger.debug(f"URL: {request.url}")
            
            if request_kwargs.get("params"):
                logger.debug(f"Params: {request_kwargs['params']}")
            
            if request_kwargs.get("headers"):
                logger.debug(f"Headers: {request_kwargs['headers']}")
            
            if request_kwargs.get("content"):
                logger.debug(f"Body (Raw): {request_kwargs['content']}")
            
            if request_kwargs.get("data"):
                logger.debug(f"Body (Form Data): {request_kwargs['data']}")
            
            if request_kwargs.get("files"):
                # files is list of (key, (filename, stream))
                files_log = []
                for key, val in request_kwargs["files"]:
                    filename = val[0] if isinstance(val, tuple) and len(val) > 0 else "unknown"
                    files_log.append(f"{key}: {filename}")
                logger.debug(f"Body (Files): {files_log}")
            logger.debug("=======================")
            # ---------------------

            if client is None:
                response = httpx.request(
                    request.method,
                    request.url,
                    proxy=request.network.proxy_url or None,
                    verify=request.network.verify_ssl,
                    trust_env=request.network.trust_env,
                    **request_kwargs,
                )
            else:
                response = client.request(
                    request.method,
                    request.url,
                    **request_kwargs,
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
