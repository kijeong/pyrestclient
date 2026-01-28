from core.model import ResponseData
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ResponseViewerPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        self._status_label = QLabel("Status: --")
        self._time_label = QLabel("Time: --")
        header_row.addWidget(self._status_label)
        header_row.addWidget(self._time_label)
        header_row.addStretch()

        layout.addLayout(header_row)

        self._response_tabs = QTabWidget()
        self._body_view = QPlainTextEdit()
        self._body_view.setReadOnly(True)
        self._headers_view = QPlainTextEdit()
        self._headers_view.setReadOnly(True)

        self._response_tabs.addTab(self._body_view, "Body")
        self._response_tabs.addTab(self._headers_view, "Headers")

        layout.addWidget(self._response_tabs)

    def set_loading(self, request_name: str) -> None:
        self._status_label.setText(f"Status: Sending ({request_name})")
        self._time_label.setText("Time: --")
        self._body_view.setPlainText("Sending request...")
        self._headers_view.setPlainText("")

    def set_response(self, response: ResponseData) -> None:
        self._status_label.setText(f"Status: {response.status_code}")
        self._time_label.setText(f"Time: {response.elapsed_ms} ms")
        self._body_view.setPlainText(response.body)
        self._headers_view.setPlainText(self._format_headers(response.headers))

    def set_error(self, message: str) -> None:
        self._status_label.setText("Status: Error")
        self._time_label.setText("Time: --")
        self._body_view.setPlainText(message)
        self._headers_view.setPlainText("")

    @staticmethod
    def _format_headers(headers: list[tuple[str, str]]) -> str:
        return "\n".join(f"{key}: {value}" for key, value in headers)
