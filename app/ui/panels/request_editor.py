from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model import AuthConfig, AuthType, HistoryEntry, NetworkConfig, RequestData, WorkspaceRequest

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
AUTH_OPTIONS = ["No Auth", "Basic Auth", "Bearer Token"]
BODY_TYPES = ["Raw (Text/JSON)", "Multipart/Form-Data"]


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
    body_type_combo: QComboBox
    body_stack: QStackedWidget
    body_editor: QPlainTextEdit
    multipart_table: QTableWidget
    auth_type_combo: QComboBox
    auth_user_edit: QLineEdit
    auth_password_edit: QLineEdit
    auth_token_edit: QLineEdit
    proxy_edit: QLineEdit
    verify_ssl_check: QCheckBox
    follow_redirects_check: QCheckBox
    trust_env_check: QCheckBox


class RequestEditorPanel(QWidget):
    request_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._request_tabs = QTabWidget()
        self._request_tabs.currentChanged.connect(self._on_tab_changed)
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
        body_type: str = "raw",
        form_fields: list[tuple[str, str]] | None = None,
        files: list[tuple[str, str]] | None = None,
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

        # Body Tab Setup
        body_tab_widget = QWidget()
        body_layout = QVBoxLayout(body_tab_widget)
        
        body_type_layout = QHBoxLayout()
        body_type_label = QLabel("Body Type:")
        body_type_combo = QComboBox()
        body_type_combo.addItems(BODY_TYPES)
        
        current_body_type_index = 0
        if body_type == "multipart":
            current_body_type_index = 1
        body_type_combo.setCurrentIndex(current_body_type_index)
        
        body_type_layout.addWidget(body_type_label)
        body_type_layout.addWidget(body_type_combo)
        body_type_layout.addStretch()
        body_layout.addLayout(body_type_layout)

        body_stack = QStackedWidget()
        
        # 1. Raw Editor
        body_editor = QPlainTextEdit()
        body_editor.setPlainText(body_text)
        if hasattr(self, "_current_font_size"):
             font = body_editor.font()
             font.setPointSize(self._current_font_size)
             body_editor.setFont(font)
        body_stack.addWidget(body_editor)

        # 2. Multipart Editor
        multipart_table = self._create_multipart_table(form_fields or [], files or [])
        body_stack.addWidget(multipart_table)

        # Sync combo with stack
        body_type_combo.currentIndexChanged.connect(body_stack.setCurrentIndex)
        body_stack.setCurrentIndex(current_body_type_index)

        body_layout.addWidget(body_stack)

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
        editor_tabs.addTab(body_tab_widget, "Body")
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
                body_type_combo=body_type_combo,
                body_stack=body_stack,
                body_editor=body_editor,
                multipart_table=multipart_table,
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

        body_type_str = "raw"
        if tab_data.body_type_combo.currentIndex() == 1:
            body_type_str = "multipart"

        form_fields, files = self._collect_multipart_data(tab_data.multipart_table)

        request = RequestData(
            name=name,
            method=tab_data.method_combo.currentText(),
            url=tab_data.url_edit.text().strip(),
            headers=self._collect_pairs(tab_data.headers_table),
            params=self._collect_pairs(tab_data.params_table),
            body=tab_data.body_editor.toPlainText(),
            form_fields=form_fields,
            files=files,
            body_type=body_type_str,
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
            
            body_type_str = "raw"
            if tab_data.body_type_combo.currentIndex() == 1:
                body_type_str = "multipart"
            
            form_fields, files = self._collect_multipart_data(tab_data.multipart_table)

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
                    form_fields=form_fields,
                    files=files,
                    body_type=body_type_str,
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
                body_type=request.body_type,
                form_fields=request.form_fields,
                files=request.files,
            )
            self._request_tabs.addTab(tab_widget, request.name)
        
        # Re-apply font size to all new tabs if set
        if hasattr(self, "_current_font_size"):
             self.set_font_size(self._current_font_size)

    def set_font_size(self, size: int) -> None:
        self._current_font_size = size
        for tab_data in self._request_tab_data:
            font = tab_data.body_editor.font()
            font.setPointSize(size)
            tab_data.body_editor.setFont(font)

    def apply_history_entry(self, entry: HistoryEntry) -> None:
        if 0 == self._request_tabs.count():
            tab_widget = self._build_request_tab(
                name=entry.name,
                method=entry.method,
                url=entry.url,
                body_text="",
            )
            self._request_tabs.addTab(tab_widget, entry.name)
            self._request_tabs.setCurrentWidget(tab_widget)
            return

        tab_index = self._request_tabs.currentIndex()
        tab_data = self._request_tab_data[tab_index]
        tab_data.name = entry.name
        tab_data.method_combo.setCurrentText(entry.method)
        tab_data.url_edit.setText(entry.url)
        self._request_tabs.setTabText(tab_index, entry.name)
        # Note: History currently doesn't persist full body/files, so we don't clear/set them here to avoid data loss on simple history click.
        # Ideally history should store full request data.

    def select_request(self, request_id: str) -> None:
        for index, tab_data in enumerate(self._request_tab_data):
            if tab_data.request_id == request_id:
                if self._request_tabs.currentIndex() != index:
                    self._request_tabs.setCurrentIndex(index)
                return

    def _on_tab_changed(self, index: int) -> None:
        if index < 0 or index >= len(self._request_tab_data):
            return
        tab_data = self._request_tab_data[index]
        self.request_selected.emit(tab_data.request_id)

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

    def _create_multipart_table(
        self,
        form_fields: list[tuple[str, str]],
        files: list[tuple[str, str]],
    ) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Key", "Type", "Value", "Action"])
        table.verticalHeader().setVisible(False)
        
        # Merge lists for display
        rows = []
        for k, v in form_fields:
            rows.append((k, "Text", v))
        for k, v in files:
            rows.append((k, "File", v))
            
        table.setRowCount(len(rows) + 5) # Extra empty rows

        for i in range(table.rowCount()):
            key, type_val, val = "", "Text", ""
            if i < len(rows):
                key, type_val, val = rows[i]
            
            # Key
            table.setItem(i, 0, QTableWidgetItem(key))
            
            # Type Combo
            combo = QComboBox()
            combo.addItems(["Text", "File"])
            combo.setCurrentText(type_val)
            table.setCellWidget(i, 1, combo)
            
            # Value
            table.setItem(i, 2, QTableWidgetItem(val))
            
            # Action Button (Browse)
            btn = QPushButton("Browse...")
            # Use lambda with default arg to capture current row index? 
            # No, row index in loop is not reliable if rows change, but here initialization is static.
            # Better to connect to a handler that finds the button's position.
            btn.clicked.connect(lambda checked=False, r=i: self._on_browse_file(table, r))
            if type_val == "Text":
                btn.setVisible(False)
            table.setCellWidget(i, 3, btn)
            
            # Connect combo change to show/hide button
            combo.currentTextChanged.connect(lambda text, r=i: self._on_multipart_type_changed(table, r, text))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        return table

    def _on_browse_file(self, table: QTableWidget, row: int) -> None:
        # Try to determine row dynamically from sender position for robustness
        sender = self.sender()
        if isinstance(sender, QWidget):
            index = table.indexAt(sender.pos())
            if index.isValid():
                row = index.row()

        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            table.setItem(row, 2, QTableWidgetItem(file_path))

    def _on_multipart_type_changed(self, table: QTableWidget, row: int, text: str) -> None:
        # Find row from sender combo
        sender = self.sender()
        if isinstance(sender, QWidget):
             index = table.indexAt(sender.pos())
             if index.isValid():
                 row = index.row()
        
        btn = table.cellWidget(row, 3)
        if btn:
            btn.setVisible(text == "File")
            
    def _collect_multipart_data(self, table: QTableWidget) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        form_fields = []
        files = []
        
        for row in range(table.rowCount()):
            key_item = table.item(row, 0)
            if not key_item or not key_item.text().strip():
                continue
            
            key = key_item.text().strip()
            
            type_widget = table.cellWidget(row, 1)
            type_val = "Text"
            if isinstance(type_widget, QComboBox):
                type_val = type_widget.currentText()
                
            val_item = table.item(row, 2)
            val = val_item.text().strip() if val_item else ""
            
            if type_val == "File":
                files.append((key, val))
            else:
                form_fields.append((key, val))
                
        return form_fields, files

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
