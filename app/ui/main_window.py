from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.panels.collection_tree import CollectionTreePanel
from app.ui.panels.request_editor import RequestEditorPanel
from app.ui.panels.response_viewer import ResponseViewerPanel
from core.http_client import HttpClient
from core.model import ResponseData
from workers.request_worker import RequestWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("REST Client Prototype")
        self.resize(1200, 800)

        self._environments = self._build_environments()
        self._collection_tree = CollectionTreePanel()
        self._collection_tree.setMinimumWidth(240)
        self._request_editor = RequestEditorPanel()
        self._response_viewer = ResponseViewerPanel()
        self._http_client = HttpClient()
        self._current_worker: RequestWorker | None = None

        self._init_toolbar()
        self._init_layout()
        self._connect_signals()

    def _init_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)

        self._send_button = QPushButton("Send")
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        toolbar.addWidget(self._send_button)
        toolbar.addWidget(self._cancel_button)
        toolbar.addSeparator()

        env_label = QLabel("Environment:")
        self._environment_combo = QComboBox()
        self._environment_combo.addItems(list(self._environments.keys()))
        self._manage_env_button = QPushButton("Manage")

        toolbar.addWidget(env_label)
        toolbar.addWidget(self._environment_combo)
        toolbar.addWidget(self._manage_env_button)

        self.addToolBar(toolbar)

    def _connect_signals(self) -> None:
        self._send_button.clicked.connect(self._on_send_clicked)
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        self._manage_env_button.clicked.connect(self._on_manage_env_clicked)

    def _init_layout(self) -> None:
        main_splitter = QSplitter(orientation=Qt.Orientation.Horizontal)
        right_splitter = QSplitter(orientation=Qt.Orientation.Vertical)

        right_splitter.addWidget(self._request_editor)
        right_splitter.addWidget(self._response_viewer)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 2)

        main_splitter.addWidget(self._collection_tree)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(main_splitter)

        self.setCentralWidget(central_widget)

    def _on_send_clicked(self) -> None:
        request = self._request_editor.build_request()
        if 0 == len(request.url):
            self._response_viewer.set_error("URL을 입력해주세요.")
            return

        if self._current_worker and self._current_worker.isRunning():
            self._response_viewer.set_error("요청이 이미 진행 중입니다.")
            return

        self._response_viewer.set_loading(request.name)
        self._send_button.setEnabled(False)
        self._cancel_button.setEnabled(False)

        environment = self._current_environment()
        worker = RequestWorker(request, self._http_client, environment)
        worker.response_ready.connect(self._on_response_ready)
        worker.failed.connect(self._on_request_failed)
        worker.finished.connect(self._on_worker_finished)
        self._current_worker = worker
        worker.start()

    def _on_cancel_clicked(self) -> None:
        self._response_viewer.set_error("Cancel 기능은 M4에서 제공됩니다.")

    def _on_response_ready(self, response: ResponseData) -> None:
        self._response_viewer.set_response(response)

    def _on_request_failed(self, message: str) -> None:
        self._response_viewer.set_error(message)

    def _on_worker_finished(self) -> None:
        self._send_button.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._current_worker = None

    def _on_manage_env_clicked(self) -> None:
        environment = self._current_environment()
        if 0 == len(environment):
            QMessageBox.information(self, "Environment", "선택된 Environment에 변수가 없습니다.")
            return

        details = "\n".join(f"{key} = {value}" for key, value in environment.items())
        QMessageBox.information(self, "Environment Variables", details)

    def _current_environment(self) -> dict[str, str]:
        name = self._environment_combo.currentText()
        return dict(self._environments.get(name, {}))

    @staticmethod
    def _build_environments() -> dict[str, dict[str, str]]:
        return {
            "No Environment": {},
            "Dev": {
                "env_name": "dev",
                "base_url": "https://httpbin.org",
            },
            "Staging": {
                "env_name": "staging",
                "base_url": "https://httpbin.org",
            },
            "Prod": {
                "env_name": "prod",
                "base_url": "https://httpbin.org",
            },
        }
