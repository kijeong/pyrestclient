import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
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
from core.model import EnvironmentScope, ResponseData, WorkspaceData, WorkspaceEnvironment
from core.storage.json_storage import load_workspace, save_workspace
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
        self._workspace_path: str | None = None

        self._init_menu()
        self._init_toolbar()
        self._init_layout()
        self._connect_signals()

    def _init_menu(self) -> None:
        file_menu = QMenu("File", self)
        self.menuBar().addMenu(file_menu)

        self._open_action = file_menu.addAction("Open Workspace...")
        self._save_action = file_menu.addAction("Save Workspace")
        self._save_as_action = file_menu.addAction("Save Workspace As...")

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
        self._open_action.triggered.connect(self._on_open_workspace)
        self._save_action.triggered.connect(self._on_save_workspace)
        self._save_as_action.triggered.connect(self._on_save_as_workspace)

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
        self._cancel_button.setEnabled(True)

        environment = self._current_environment()
        worker = RequestWorker(request, self._http_client, environment)
        worker.response_ready.connect(self._on_response_ready)
        worker.failed.connect(self._on_request_failed)
        worker.canceled.connect(self._on_request_canceled)
        worker.finished.connect(self._on_worker_finished)
        self._current_worker = worker
        worker.start()

    def _on_cancel_clicked(self) -> None:
        if not self._current_worker or not self._current_worker.isRunning():
            self._response_viewer.set_error("취소할 요청이 없습니다.")
            return

        self._response_viewer.set_canceling()
        self._cancel_button.setEnabled(False)
        self._current_worker.cancel()

    def _on_response_ready(self, response: ResponseData) -> None:
        self._response_viewer.set_response(response)

    def _on_request_failed(self, message: str) -> None:
        self._response_viewer.set_error(message)

    def _on_request_canceled(self) -> None:
        self._response_viewer.set_canceled()

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

    def _on_open_workspace(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workspace",
            "",
            "Workspace Files (*.json)",
        )
        if 0 == len(path):
            return

        try:
            workspace = load_workspace(path)
        except Exception as exc:
            QMessageBox.critical(self, "Open Workspace", f"로드 실패: {exc}")
            return

        self._apply_workspace(workspace)
        self._workspace_path = path
        QMessageBox.information(self, "Open Workspace", "Workspace를 불러왔습니다.")

    def _on_save_workspace(self) -> None:
        if self._workspace_path is None:
            self._on_save_as_workspace()
            return

        workspace = self._build_workspace()
        try:
            save_workspace(self._workspace_path, workspace)
        except Exception as exc:
            QMessageBox.critical(self, "Save Workspace", f"저장 실패: {exc}")
            return

        QMessageBox.information(self, "Save Workspace", "Workspace를 저장했습니다.")

    def _on_save_as_workspace(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workspace As",
            "workspace.json",
            "Workspace Files (*.json)",
        )
        if 0 == len(path):
            return

        workspace = self._build_workspace()
        try:
            save_workspace(path, workspace)
        except Exception as exc:
            QMessageBox.critical(self, "Save Workspace", f"저장 실패: {exc}")
            return

        self._workspace_path = path
        QMessageBox.information(self, "Save Workspace", "Workspace를 저장했습니다.")

    def _current_environment(self) -> dict[str, str]:
        name = self._environment_combo.currentText()
        return dict(self._environments.get(name, {}))

    def _build_workspace(self) -> WorkspaceData:
        collections, folders = self._collection_tree.build_workspace_collections()
        requests = self._request_editor.build_workspace_requests()
        environments = self._build_workspace_environments()
        return WorkspaceData(
            schema_version=1,
            updated_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            collections=collections,
            folders=folders,
            requests=requests,
            environments=environments,
        )

    def _apply_workspace(self, workspace: WorkspaceData) -> None:
        self._collection_tree.load_workspace_tree(
            workspace.collections,
            workspace.folders,
            workspace.requests,
        )
        self._request_editor.load_workspace_requests(workspace.requests)
        self._environments = self._build_environment_map(workspace)
        self._environment_combo.clear()
        self._environment_combo.addItems(list(self._environments.keys()))

    def _build_environment_map(self, workspace: WorkspaceData) -> dict[str, dict[str, str]]:
        environment_map: dict[str, dict[str, str]] = {"No Environment": {}}
        index = 1
        for env in workspace.environments:
            if env.scope is not EnvironmentScope.GLOBAL:
                continue
            name = env.variables.get("name")
            if name is None or 0 == len(name):
                name = f"Env {index}"
            index += 1
            environment_map[name] = dict(env.variables)
        return environment_map

    def _build_workspace_environments(self) -> list[WorkspaceEnvironment]:
        environments: list[WorkspaceEnvironment] = []
        for name, variables in self._environments.items():
            if name == "No Environment":
                continue
            variables_payload = dict(variables)
            variables_payload.setdefault("name", name)
            environments.append(
                WorkspaceEnvironment(
                    scope=EnvironmentScope.GLOBAL,
                    owner_id=None,
                    variables=variables_payload,
                )
            )
        return environments

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
