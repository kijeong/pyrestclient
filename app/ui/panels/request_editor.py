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

from core.model import AuthConfig, AuthType, NetworkConfig, RequestData

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
AUTH_OPTIONS = ["No Auth", "Basic Auth", "Bearer Token"]


@dataclass(slots=True)
class RequestTabWidgets:
    name: str
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

    def _build_request_tab(self, name: str, method: str, url: str, body_text: str) -> QWidget:
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
        timeout_spin.setValue(10_000)

        top_row.addWidget(method_combo)
        top_row.addWidget(url_edit, stretch=1)
        top_row.addWidget(timeout_label)
        top_row.addWidget(timeout_spin)
        layout.addLayout(top_row)

        editor_tabs = QTabWidget()
        headers_table = self._create_key_value_table(
            pairs=[("Accept", "application/json"), ("Content-Type", "application/json")],
            key_label="Header",
            value_label="Value",
        )
        params_table = self._create_key_value_table(
            pairs=[("limit", "25"), ("offset", "0")],
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
        self._request_tab_data.append(
            RequestTabWidgets(
                name=name,
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
