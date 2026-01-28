from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.http_client import HttpClient
from core.model import RequestData, ResponseData


class RequestWorker(QThread):
    response_ready = Signal(ResponseData)
    failed = Signal(str)

    def __init__(self, request: RequestData, http_client: HttpClient | None = None) -> None:
        super().__init__()
        self._request = request
        self._http_client = http_client or HttpClient()

    def run(self) -> None:
        try:
            response = self._http_client.send(self._request)
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        self.response_ready.emit(response)
