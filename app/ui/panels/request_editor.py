from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model import AuthConfig, AuthType, NetworkConfig, RequestData, WorkspaceRequest

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
AUTH_OPTIONS = ["No Auth", "Basic Auth", "Bearer Token"]


@dataclass(slots=True)
class RequestTabWidgets:
    name: str
    request_id: str
    folder_id: str
    method_combo: QComboBox
    url_edit: QLineEdit
    timeout_spin: QSpinBox
    headers_table: QTableWidget
    params_table: QTableWidget
    body_editor: QPlainTextEdit
    auth_type_combo: QComboBox
    auth_user_edit: QLineEdit
    auth_password_edit: QLineEdit
    auth_token_edit: QLineEdit
    proxy_edit: QLineEdit
    verify_ssl_check: QCheckBox
    follow_redirects_check: QCheckBox
    trust_env_check: QCheckBox


class RequestEditorPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._request_tabs = QTabWidget()
        layout.addWidget(self._request_tabs)
        self._request_tab_data: list[RequestTabWidgets] = []
        self._request_id_counter = 1

        self._request_tabs.addTab(
            self._build_request_tab(
                name="List Users",
                method="GET",
                url="https://api.example.com/users",
                body_text="",
            ),
            "List Users",
        )
        self._request_tabs.addTab(
            self._build_request_tab(
                name="Create User",
                method="POST",
                url="https://api.example.com/users",
                body_text="{\n    \"name\": \"Jane\"\n}",
            ),
            "Create User",
        )

    def _build_request_tab(
        self,
        name: str,
        method: str,
        url: str,
        body_text: str,
        headers: list[tuple[str, str]] | None = None,
        params: list[tuple[str, str]] | None = None,
        auth: AuthConfig | None = None,
        timeout_ms: int = 10000,
        network: NetworkConfig | None = None,
        request_id: str | None = None,
        folder_id: str | None = None,
    ) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        top_row = QHBoxLayout()
        method_combo = QComboBox()
        method_combo.addItems(METHODS)
        method_combo.setCurrentText(method)

        url_edit = QLineEdit()
        url_edit.setPlaceholderText("https://api.example.com")
        url_edit.setText(url)

        timeout_label = QLabel("Timeout (ms)")
        timeout_spin = QSpinBox()
        timeout_spin.setRange(0, 600_000)
        timeout_spin.setValue(timeout_ms)

        top_row.addWidget(method_combo)
        top_row.addWidget(url_edit, stretch=1)
        top_row.addWidget(timeout_label)
        top_row.addWidget(timeout_spin)
        layout.addLayout(top_row)

        editor_tabs = QTabWidget()
        resolved_headers = headers or [
            ("Accept", "application/json"),
            ("Content-Type", "application/json"),
        ]
        headers_table = self._create_key_value_table(
            pairs=resolved_headers,
            key_label="Header",
            value_label="Value",
        )
        resolved_params = params or [("limit", "25"), ("offset", "0")]
        params_table = self._create_key_value_table(
            pairs=resolved_params,
            key_label="Param",
            value_label="Value",
        )

        body_editor = QPlainTextEdit()
        body_editor.setPlainText(body_text)

        auth_tab = QWidget()
        auth_layout = QFormLayout(auth_tab)
        auth_type_combo = QComboBox()
        auth_type_combo.addItems(AUTH_OPTIONS)
        auth_user_edit = QLineEdit()
        auth_user_edit.setPlaceholderText("Username")
        auth_password_edit = QLineEdit()
        auth_password_edit.setPlaceholderText("Password")
        auth_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_token_edit = QLineEdit()
        auth_token_edit.setPlaceholderText("Bearer token")

        resolved_auth = auth or AuthConfig.none()
        if resolved_auth.auth_type is AuthType.BASIC:
            auth_type_combo.setCurrentText("Basic Auth")
            auth_user_edit.setText(resolved_auth.username)
            auth_password_edit.setText(resolved_auth.password)
        elif resolved_auth.auth_type is AuthType.BEARER:
            auth_type_combo.setCurrentText("Bearer Token")
            auth_token_edit.setText(resolved_auth.token)
        else:
            auth_type_combo.setCurrentText("No Auth")

        auth_layout.addRow(QLabel("Type"), auth_type_combo)
        auth_layout.addRow(QLabel("Username"), auth_user_edit)
        auth_layout.addRow(QLabel("Password"), auth_password_edit)
        auth_layout.addRow(QLabel("Token"), auth_token_edit)

        network_tab = QWidget()
        network_layout = QFormLayout(network_tab)
        proxy_edit = QLineEdit()
        proxy_edit.setPlaceholderText("http://proxy.local:8080")
        verify_ssl_check = QCheckBox("Verify SSL")
        verify_ssl_check.setChecked(True)
        follow_redirects_check = QCheckBox("Follow Redirects")
        trust_env_check = QCheckBox("Trust Environment Proxies")
        trust_env_check.setChecked(True)

        resolved_network = network or NetworkConfig()
        proxy_edit.setText(resolved_network.proxy_url)
        verify_ssl_check.setChecked(resolved_network.verify_ssl)
        follow_redirects_check.setChecked(resolved_network.follow_redirects)
        trust_env_check.setChecked(resolved_network.trust_env)

        network_layout.addRow(QLabel("Proxy URL"), proxy_edit)
        network_layout.addRow(verify_ssl_check)
        network_layout.addRow(follow_redirects_check)
        network_layout.addRow(trust_env_check)

        editor_tabs.addTab(headers_table, "Headers")
        editor_tabs.addTab(params_table, "Params")
        editor_tabs.addTab(body_editor, "Body")
        editor_tabs.addTab(auth_tab, "Auth")
        editor_tabs.addTab(network_tab, "Network")

        layout.addWidget(editor_tabs)
        resolved_request_id = request_id
        if resolved_request_id is None or 0 == len(resolved_request_id):
            resolved_request_id = f"req-{self._request_id_counter}"
            self._request_id_counter += 1

        resolved_folder_id = folder_id or "folder-1"

        self._request_tab_data.append(
            RequestTabWidgets(
                name=name,
                request_id=resolved_request_id,
                folder_id=resolved_folder_id,
                method_combo=method_combo,
                url_edit=url_edit,
                timeout_spin=timeout_spin,
                headers_table=headers_table,
                params_table=params_table,
                body_editor=body_editor,
                auth_type_combo=auth_type_combo,
                auth_user_edit=auth_user_edit,
                auth_password_edit=auth_password_edit,
                auth_token_edit=auth_token_edit,
                proxy_edit=proxy_edit,
                verify_ssl_check=verify_ssl_check,
                follow_redirects_check=follow_redirects_check,
                trust_env_check=trust_env_check,
            )
        )
        return container

    def build_request(self) -> RequestData:
        tab_index = self._request_tabs.currentIndex()
        tab_data = self._request_tab_data[tab_index]
        name = self._request_tabs.tabText(tab_index)

        request = RequestData(
            name=name,
            method=tab_data.method_combo.currentText(),
            url=tab_data.url_edit.text().strip(),
            headers=self._collect_pairs(tab_data.headers_table),
            params=self._collect_pairs(tab_data.params_table),
            body=tab_data.body_editor.toPlainText(),
            auth=self._resolve_auth(tab_data),
            timeout_ms=int(tab_data.timeout_spin.value()),
            network=NetworkConfig(
                proxy_url=tab_data.proxy_edit.text().strip(),
                verify_ssl=tab_data.verify_ssl_check.isChecked(),
                follow_redirects=tab_data.follow_redirects_check.isChecked(),
                trust_env=tab_data.trust_env_check.isChecked(),
            ),
        )
        return request

    def build_workspace_requests(self) -> list[WorkspaceRequest]:
        requests: list[WorkspaceRequest] = []
        for index, tab_data in enumerate(self._request_tab_data):
            name = self._request_tabs.tabText(index)
            requests.append(
                WorkspaceRequest(
                    id=tab_data.request_id,
                    folder_id=tab_data.folder_id,
                    name=name,
                    method=tab_data.method_combo.currentText(),
                    url=tab_data.url_edit.text().strip(),
                    headers=self._collect_pairs(tab_data.headers_table),
                    params=self._collect_pairs(tab_data.params_table),
                    body=tab_data.body_editor.toPlainText(),
                    auth=self._resolve_auth(tab_data),
                    timeout_ms=int(tab_data.timeout_spin.value()),
                    network=NetworkConfig(
                        proxy_url=tab_data.proxy_edit.text().strip(),
                        verify_ssl=tab_data.verify_ssl_check.isChecked(),
                        follow_redirects=tab_data.follow_redirects_check.isChecked(),
                        trust_env=tab_data.trust_env_check.isChecked(),
                    ),
                )
            )
        return requests

    def load_workspace_requests(self, requests: list[WorkspaceRequest]) -> None:
        self._request_tabs.clear()
        self._request_tab_data = []
        self._request_id_counter = len(requests) + 1

        for request in requests:
            tab_widget = self._build_request_tab(
                name=request.name,
                method=request.method,
                url=request.url,
                body_text=request.body,
                headers=request.headers,
                params=request.params,
                auth=request.auth,
                timeout_ms=request.timeout_ms,
                network=request.network,
                request_id=request.id,
                folder_id=request.folder_id,
            )
            self._request_tabs.addTab(tab_widget, request.name)

    def _create_key_value_table(
        self,
        pairs: list[tuple[str, str]],
        key_label: str,
        value_label: str,
    ) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([key_label, value_label])
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(pairs) + 1)

        for row_index, (key, value) in enumerate(pairs):
            table.setItem(row_index, 0, QTableWidgetItem(key))
            table.setItem(row_index, 1, QTableWidgetItem(value))

        table.horizontalHeader().setStretchLastSection(True)
        return table

    @staticmethod
    def _collect_pairs(table: QTableWidget) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for row in range(table.rowCount()):
            key_item = table.item(row, 0)
            if key_item is None:
                continue
            key_text = key_item.text().strip()
            if 0 == len(key_text):
                continue
            value_item = table.item(row, 1)
            value_text = value_item.text().strip() if value_item else ""
            pairs.append((key_text, value_text))
        return pairs

    @staticmethod
    def _resolve_auth(tab_data: RequestTabWidgets) -> AuthConfig:
        auth_type = tab_data.auth_type_combo.currentText()
        if auth_type == "Basic Auth":
            return AuthConfig.basic(
                tab_data.auth_user_edit.text().strip(),
                tab_data.auth_password_edit.text(),
            )
        if auth_type == "Bearer Token":
            return AuthConfig.bearer(tab_data.auth_token_edit.text().strip())
        return AuthConfig(auth_type=AuthType.NONE)
