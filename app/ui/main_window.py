import datetime
import os

from PySide6.QtCore import QByteArray, QPoint, Qt, QTimer
from PySide6.QtGui import QFontMetrics, QGuiApplication, QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.panels.collection_tree import CollectionTreePanel
from app.ui.panels.history_panel import HistoryPanel
from app.ui.panels.request_editor import RequestEditorPanel
from app.ui.panels.response_viewer import ResponseViewerPanel
from core.http_client import HttpClient
from core.logger import get_logger
from core.settings import AppSettings
from core.model import (
    EnvironmentScope,
    HistoryEntry,
    RequestData,
    ResponseData,
    WorkspaceData,
    WorkspaceEnvironment,
)
from core.storage.history_jsonl import (
    append_history_entry,
    default_history_path,
    load_history_entries,
)
from core.storage.json_storage import load_workspace, save_workspace
from core.template import render_request
from workers.request_worker import RequestWorker


_LOGGER = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("REST Client Prototype")
        self.resize(1200, 800)

        self._settings = AppSettings()
        
        # Load Settings
        try:
            self._default_timeout_ms = int(self._settings.value("default_timeout_ms", 10000))
        except (ValueError, TypeError):
            self._default_timeout_ms = 10000
        if self._settings.value("default_timeout_ms") is None:
             self._settings.setValue("default_timeout_ms", 10000)

        try:
            self._history_max_items = int(self._settings.value("history_max_items", 100))
        except (ValueError, TypeError):
            self._history_max_items = 100
        if self._settings.value("history_max_items") is None:
             self._settings.setValue("history_max_items", 100)
             
        try:
            self._editor_font_size = int(self._settings.value("editor_font_size", 12))
        except (ValueError, TypeError):
            self._editor_font_size = 12
        if self._settings.value("editor_font_size") is None:
             self._settings.setValue("editor_font_size", 12)

        self._environments = self._build_environments()
        self._collection_tree = CollectionTreePanel()
        self._collection_tree.setMinimumWidth(240)
        self._history_panel = HistoryPanel()
        self._request_editor = RequestEditorPanel()
        self._response_viewer = ResponseViewerPanel()
        
        # Apply Font Size
        self._request_editor.set_font_size(self._editor_font_size)
        self._response_viewer.set_font_size(self._editor_font_size)

        self._http_client = HttpClient(default_timeout_ms=self._default_timeout_ms)
        self._current_worker: RequestWorker | None = None
        self._workspace_path: str | None = None
        self._history_path = default_history_path()
        self._pending_history_request: RequestData | None = None
        self._notification_timer = QTimer(self)
        self._notification_timer.setSingleShot(True)
        self._notification_timer.timeout.connect(self._hide_notification)
        self._environment_overlay: QWidget | None = None

        self._init_menu()
        self._init_toolbar()
        self._init_layout()
        self._restore_window_state()
        self._connect_signals()
        self._init_workspace()

    def closeEvent(self, event: QCloseEvent) -> None:
        # Save Window State
        try:
            window_settings = {
                "geometry": self.saveGeometry().toHex().data().decode("utf-8"),
                "state": self.saveState().toHex().data().decode("utf-8"),
                "ui_main_splitter": self._main_splitter.saveState().toHex().data().decode("utf-8"),
                "ui_left_splitter": self._left_splitter.saveState().toHex().data().decode("utf-8"),
                "ui_right_splitter": self._right_splitter.saveState().toHex().data().decode("utf-8"),
            }
            self._settings.setValue("window", window_settings)
        except Exception as e:
            _LOGGER.error(f"Failed to save window state: {e}")

        if self._workspace_path:
            try:
                save_workspace(self._workspace_path, self._build_workspace())
                _LOGGER.info(f"Auto-saved workspace to {self._workspace_path}")
            except Exception as e:
                _LOGGER.error(f"Failed to auto-save workspace: {e}")
                # We don't block exit on save failure, but logging is good.

        settings = AppSettings()
        if self._workspace_path:
            settings.setValue("last_workspace", self._workspace_path)
        
        event.accept()

    def _init_workspace(self) -> None:
        settings = AppSettings()
        last_path = settings.value("last_workspace")
        
        target_path = last_path
        
        # If no last path or file doesn't exist, fallback to default in CWD
        if not target_path or not isinstance(target_path, str) or not os.path.exists(target_path):
            target_path = os.path.abspath("workspace.json")
        
        if os.path.exists(target_path):
            try:
                workspace = load_workspace(target_path)
                self._apply_workspace(workspace)
                self._workspace_path = target_path
                self._show_notification(f"Workspace loaded: {os.path.basename(target_path)}")
                return
            except Exception as e:
                _LOGGER.error(f"Failed to load workspace {target_path}: {e}")
                # Proceed to overwrite/create if it was invalid? 
                # Better to be safe and maybe create a new name or just use current default state.
                # If specifically requested "save initial workspace if none exists", we might proceed.
        
        # If file doesn't exist (or failed load? no, safe to keep current state if load failed to avoid dataloss overwriting)
        # If file doesn't exist, save initial state.
        if not os.path.exists(target_path):
            try:
                save_workspace(target_path, self._build_workspace())
                self._workspace_path = target_path
                self._show_notification(f"New workspace created: {os.path.basename(target_path)}")
            except Exception as e:
                _LOGGER.error(f"Failed to create initial workspace {target_path}: {e}")

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
        self._history_panel.entry_selected.connect(self._on_history_selected)

    def _init_layout(self) -> None:
        self._main_splitter = QSplitter(orientation=Qt.Orientation.Horizontal)
        self._left_splitter = QSplitter(orientation=Qt.Orientation.Vertical)
        self._right_splitter = QSplitter(orientation=Qt.Orientation.Vertical)

        self._left_splitter.addWidget(self._collection_tree)
        self._left_splitter.addWidget(self._history_panel)
        self._left_splitter.setStretchFactor(0, 3)
        self._left_splitter.setStretchFactor(1, 2)

        self._right_splitter.addWidget(self._request_editor)
        self._right_splitter.addWidget(self._response_viewer)
        self._right_splitter.setStretchFactor(0, 3)
        self._right_splitter.setStretchFactor(1, 2)

        self._main_splitter.addWidget(self._left_splitter)
        self._main_splitter.addWidget(self._right_splitter)
        self._main_splitter.setStretchFactor(0, 1)
        self._main_splitter.setStretchFactor(1, 3)

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        self._notification_banner = QLabel()
        self._notification_banner.setVisible(False)
        self._notification_banner.setWordWrap(True)
        self._notification_banner.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._notification_banner.setStyleSheet(
            ""
            "background-color: #fff3cd;"
            "color: #664d03;"
            "border: 1px solid #ffecb5;"
            "padding: 6px 10px;"
            "border-radius: 4px;"
            ""
        )
        layout.addWidget(self._notification_banner)
        layout.addWidget(self._main_splitter)

        self.setCentralWidget(central_widget)
        self._load_history_entries()

    def _restore_window_state(self) -> None:
        try:
            window_settings = self._settings.value("window")
            if not isinstance(window_settings, dict):
                return

            geometry = window_settings.get("geometry")
            if geometry:
                self.restoreGeometry(QByteArray.fromHex(geometry.encode("utf-8")))
            
            state = window_settings.get("state")
            if state:
                self.restoreState(QByteArray.fromHex(state.encode("utf-8")))

            main_splitter_state = window_settings.get("ui_main_splitter")
            if main_splitter_state:
                self._main_splitter.restoreState(QByteArray.fromHex(main_splitter_state.encode("utf-8")))
            
            left_splitter_state = window_settings.get("ui_left_splitter")
            if left_splitter_state:
                self._left_splitter.restoreState(QByteArray.fromHex(left_splitter_state.encode("utf-8")))
            
            right_splitter_state = window_settings.get("ui_right_splitter")
            if right_splitter_state:
                self._right_splitter.restoreState(QByteArray.fromHex(right_splitter_state.encode("utf-8")))
        except Exception as e:
            _LOGGER.error(f"Failed to restore window state: {e}")

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
        self._pending_history_request = render_request(request, environment)
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
        self._record_history(status_code=response.status_code, elapsed_ms=response.elapsed_ms)

    def _on_request_failed(self, message: str) -> None:
        self._response_viewer.set_error(message)
        self._record_history(error=message)

    def _on_request_canceled(self) -> None:
        self._response_viewer.set_canceled()
        self._record_history(error="Canceled")

    def _on_worker_finished(self) -> None:
        self._send_button.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._current_worker = None
        self._pending_history_request = None

    def _on_manage_env_clicked(self) -> None:
        environment = self._current_environment()
        if 0 == len(environment):
            self._show_environment_dialog("Environment", "선택된 Environment에 변수가 없습니다.")
            return

        details = "\n".join(f"{key} = {value}" for key, value in environment.items())
        self._show_environment_dialog("Environment Variables", details)

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
        self._show_notification("Workspace를 불러왔습니다.")

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

        self._show_notification("Workspace를 저장했습니다.")

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
        self._show_notification("Workspace를 저장했습니다.")

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

    def _show_notification(self, message: str) -> None:
        self._notification_banner.setText(message)
        self._notification_banner.setVisible(True)
        self._notification_timer.start(3000)

    def _hide_notification(self) -> None:
        self._notification_banner.setVisible(False)

    def _show_environment_dialog(self, title: str, message: str) -> None:
        platform_name = QGuiApplication.platformName().lower()
        if platform_name.startswith("wayland"):
            self._show_environment_overlay(title, message)
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        message_view = QPlainTextEdit()
        message_view.setReadOnly(True)
        message_view.setPlainText(message)
        message_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        metrics = QFontMetrics(message_view.font())
        lines = message.splitlines() or [""]
        max_line_width = max(metrics.horizontalAdvance(line) for line in lines)
        width_padding = 80
        min_width = 360
        max_width = 900
        target_width = max(min_width, min(max_width, max_line_width + width_padding))

        visible_lines = min(len(lines), 12)
        line_height = metrics.lineSpacing()
        target_height = line_height * visible_lines + 24
        message_view.setFixedHeight(target_height)
        message_view.setMinimumWidth(target_width)

        layout.addWidget(message_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        margins = layout.contentsMargins()
        dialog_width = target_width + margins.left() + margins.right()
        dialog_height = (
            target_height
            + buttons.sizeHint().height()
            + margins.top()
            + margins.bottom()
            + layout.spacing()
        )
        dialog.setFixedSize(dialog_width, dialog_height)
        _LOGGER.debug(
            "env-dialog size=%s dialog_width=%s dialog_height=%s",
            dialog.size(),
            dialog_width,
            dialog_height,
        )

        def _resolve_window_center() -> QPoint:
            window_handle = self.windowHandle()
            frame_geometry = self.frameGeometry()
            global_center = self.mapToGlobal(self.rect().center())
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen is not None:
                _LOGGER.debug(
                    "env-dialog screen geometry=%s available=%s",
                    screen.geometry(),
                    screen.availableGeometry(),
                )
            _LOGGER.debug(
                "env-dialog frameGeometry=%s rect=%s global_center=%s",
                frame_geometry,
                self.rect(),
                global_center,
            )
            if window_handle is None:
                _LOGGER.debug("env-dialog windowHandle missing")
                return self.mapToGlobal(self.rect().center())
            window_pos = window_handle.position()
            window_size = window_handle.size()
            _LOGGER.debug(
                "env-dialog windowHandle pos=%s size=%s",
                window_pos,
                window_size,
            )
            return QPoint(
                int(window_pos.x() + (window_size.width() / 2)),
                int(window_pos.y() + (window_size.height() / 2)),
            )

        def _center_dialog() -> None:
            parent_center = _resolve_window_center()
            target_x = parent_center.x() - (dialog.width() // 2)
            target_y = parent_center.y() - (dialog.height() // 2)
            _LOGGER.debug(
                "env-dialog parent_center=%s target=(%s,%s)",
                parent_center,
                target_x,
                target_y,
            )
            dialog.move(target_x, target_y)
            _LOGGER.debug(
                "env-dialog moved pos=%s frameGeometry=%s",
                dialog.pos(),
                dialog.frameGeometry(),
            )

        QTimer.singleShot(0, _center_dialog)
        dialog.exec()

    def _clear_environment_overlay(self) -> None:
        self._environment_overlay = None

    def _show_environment_overlay(self, title: str, message: str) -> None:
        if self._environment_overlay is not None:
            self._environment_overlay.close()
            self._environment_overlay = None

        overlay = QWidget(self)
        overlay.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        overlay.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.25);")
        overlay.setGeometry(self.rect())
        overlay.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        dialog_frame = QFrame(overlay)
        dialog_frame.setStyleSheet(
            ""
            "background-color: #ffffff;"
            "border: 1px solid #c0c0c0;"
            "border-radius: 6px;"
            ""
        )
        frame_layout = QVBoxLayout(dialog_frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600;")
        frame_layout.addWidget(title_label)

        message_view = QPlainTextEdit()
        message_view.setReadOnly(True)
        message_view.setPlainText(message)
        message_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        metrics = QFontMetrics(message_view.font())
        lines = message.splitlines() or [""]
        max_line_width = max(metrics.horizontalAdvance(line) for line in lines)
        width_padding = 80
        min_width = 360
        max_width = 900
        title_width = title_label.sizeHint().width()
        target_width = max(min_width, min(max_width, max(max_line_width, title_width) + width_padding))

        visible_lines = min(len(lines), 12)
        line_height = metrics.lineSpacing()
        target_height = line_height * visible_lines + 24
        message_view.setFixedHeight(target_height)
        message_view.setMinimumWidth(target_width)

        frame_layout.addWidget(message_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(overlay.close)
        frame_layout.addWidget(buttons)

        margins = frame_layout.contentsMargins()
        spacing = frame_layout.spacing()
        dialog_width = target_width + margins.left() + margins.right()
        dialog_height = (
            title_label.sizeHint().height()
            + target_height
            + buttons.sizeHint().height()
            + margins.top()
            + margins.bottom()
            + spacing * 2
        )
        dialog_frame.setFixedSize(dialog_width, dialog_height)

        parent_center = overlay.rect().center()
        dialog_frame.move(
            parent_center.x() - (dialog_width // 2),
            parent_center.y() - (dialog_height // 2),
        )

        overlay.destroyed.connect(self._clear_environment_overlay)
        overlay.show()
        overlay.raise_()
        dialog_frame.raise_()
        overlay.activateWindow()
        overlay.setFocus()
        self._environment_overlay = overlay

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

    def _load_history_entries(self) -> None:
        try:
            entries = load_history_entries(self._history_path, limit=self._history_max_items)
        except Exception as exc:
            QMessageBox.warning(self, "History", f"History 로드 실패: {exc}")
            return
        self._history_panel.set_entries(entries)

    def _record_history(
        self,
        status_code: int | None = None,
        elapsed_ms: int | None = None,
        error: str | None = None,
    ) -> None:
        request = self._pending_history_request
        if request is None:
            return
        entry = HistoryEntry(
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            name=request.name,
            method=request.method,
            url=request.url,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            error=error,
        )
        try:
            append_history_entry(self._history_path, entry)
        except Exception as exc:
            QMessageBox.warning(self, "History", f"History 저장 실패: {exc}")
        self._history_panel.add_entry(entry)

    def _on_history_selected(self, entry: HistoryEntry) -> None:
        self._request_editor.apply_history_entry(entry)
        self._response_viewer.set_history_entry(entry)

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
