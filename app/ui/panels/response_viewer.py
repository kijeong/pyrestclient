from core.model import HistoryEntry, ResponseData
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

    def set_canceling(self) -> None:
        self._status_label.setText("Status: Canceling")
        self._time_label.setText("Time: --")
        self._body_view.setPlainText("Canceling request...")
        self._headers_view.setPlainText("")

    def set_response(self, response: ResponseData) -> None:
        self._status_label.setText(f"Status: {response.status_code}")
        self._time_label.setText(f"Time: {response.elapsed_ms} ms")
        self._body_view.setPlainText(response.body)
        self._headers_view.setPlainText(self._format_headers(response.headers))

    def set_canceled(self) -> None:
        self._status_label.setText("Status: Canceled")
        self._time_label.setText("Time: --")
        self._body_view.setPlainText("Request canceled by user.")
        self._headers_view.setPlainText("")

    def set_error(self, message: str) -> None:
        self._status_label.setText("Status: Error")
        self._time_label.setText("Time: --")
        self._body_view.setPlainText(message)
        self._headers_view.setPlainText("")

    def set_history_entry(self, entry: HistoryEntry) -> None:
        status_text = "--"
        if entry.error:
            status_text = "Error"
        elif entry.status_code is not None:
            status_text = str(entry.status_code)

        time_text = "--"
        if entry.elapsed_ms is not None:
            time_text = f"{entry.elapsed_ms} ms"

        self._status_label.setText(f"Status: {status_text}")
        self._time_label.setText(f"Time: {time_text}")

        body_lines = [
            f"Name: {entry.name}",
            f"Method: {entry.method}",
            f"URL: {entry.url}",
        ]
        if entry.error:
            body_lines.append(f"Error: {entry.error}")
        if entry.status_code is not None:
            body_lines.append(f"Status: {entry.status_code}")
        if entry.elapsed_ms is not None:
            body_lines.append(f"Elapsed: {entry.elapsed_ms} ms")

        self._body_view.setPlainText("\n".join(body_lines))
        self._headers_view.setPlainText("")

    @staticmethod
    def _format_headers(headers: list[tuple[str, str]]) -> str:
        return "\n".join(f"{key}: {value}" for key, value in headers)
