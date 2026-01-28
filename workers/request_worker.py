from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.http_client import HttpClient
from core.logger import get_logger
from core.model import RequestData, ResponseData
from core.template import render_request


class RequestWorker(QThread):
    response_ready = Signal(ResponseData)
    failed = Signal(str)

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

    def run(self) -> None:
        try:
            rendered_request = render_request(self._request, self._environment)
            self._logger.info(
                "Sending request '%s' %s %s",
                rendered_request.name,
                rendered_request.method,
                rendered_request.url,
            )
            response = self._http_client.send(rendered_request)
        except Exception as exc:
            self._logger.exception("Request failed")
            self.failed.emit(str(exc))
            return

        self._logger.info(
            "Response received '%s' status=%s time=%sms",
            rendered_request.name,
            response.status_code,
            response.elapsed_ms,
        )
        self.response_ready.emit(response)
