from __future__ import annotations

import httpx
from PySide6.QtCore import QThread, Signal

from core.http_client import HttpClient
from core.logger import get_logger
from core.model import RequestData, ResponseData
from core.template import render_request


class RequestWorker(QThread):
    response_ready = Signal(ResponseData)
    failed = Signal(str)
    canceled = Signal()

    def __init__(
        self,
        request: RequestData,
        http_client: HttpClient | None = None,
        environment: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self._request = request
        self._http_client = http_client or HttpClient()
        self._environment = environment or {}
        self._logger = get_logger("worker")
        self._client: httpx.Client | None = None
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()
        self._logger.info("Cancel requested")
        self._close_client()

    def run(self) -> None:
        rendered_request = render_request(self._request, self._environment)
        if self._is_cancelled():
            self._logger.info("Request cancelled before start")
            self.canceled.emit()
            return

        self._logger.info(
            "Sending request '%s' %s %s",
            rendered_request.name,
            rendered_request.method,
            rendered_request.url,
        )

        self._client = self._http_client.create_client(rendered_request)
        try:
            response = self._http_client.send(rendered_request, self._client)
        except Exception as exc:
            if self._is_cancelled():
                self._logger.info("Request cancelled")
                self.canceled.emit()
            else:
                self._logger.exception("Request failed")
                self.failed.emit(str(exc))
            return
        finally:
            self._close_client()

        if self._is_cancelled():
            self._logger.info("Request cancelled after response")
            self.canceled.emit()
            return

        self._logger.info(
            "Response received '%s' status=%s time=%sms",
            rendered_request.name,
            response.status_code,
            response.elapsed_ms,
        )
        self.response_ready.emit(response)

    def _close_client(self) -> None:
        client = self._client
        if client is None:
            return
        try:
            client.close()
        except Exception:
            self._logger.exception("Failed to close HTTP client")
        self._client = None

    def _is_cancelled(self) -> bool:
        return self._cancelled or self.isInterruptionRequested()
