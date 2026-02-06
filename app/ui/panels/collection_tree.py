from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from core.model import WorkspaceCollection, WorkspaceFolder, WorkspaceRequest


class CollectionTreePanel(QWidget):
    request_selected = Signal(str)

    _ID_ROLE = int(Qt.ItemDataRole.UserRole) + 1
    _TYPE_ROLE = int(Qt.ItemDataRole.UserRole) + 2
    _TYPE_COLLECTION = "collection"
    _TYPE_FOLDER = "folder"
    _TYPE_REQUEST = "request"

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Collections")
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._tree)

        self._collection_id_counter = 1
        self._folder_id_counter = 1
        self._request_id_counter = 1
        self._items_by_id: dict[str, QTreeWidgetItem] = {}

        self._populate_dummy_data()

    def build_workspace_collections(self) -> tuple[list[WorkspaceCollection], list[WorkspaceFolder]]:
        collections: list[WorkspaceCollection] = []
        folders: list[WorkspaceFolder] = []
        for index in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(index)
            if item is None:
                continue
            collection_id = self._ensure_item_id(item, self._TYPE_COLLECTION)
            collections.append(
                WorkspaceCollection(
                    id=collection_id,
                    name=item.text(0),
                )
            )
            self._collect_folders(item, collection_id, None, folders)
        return collections, folders

    def load_workspace_tree(
        self,
        collections: list[WorkspaceCollection],
        folders: list[WorkspaceFolder],
        requests: list[WorkspaceRequest],
    ) -> None:
        self._tree.clear()
        self._reset_counters()

        collection_items: dict[str, QTreeWidgetItem] = {}
        for collection in collections:
            item = self._create_item(collection.name, self._TYPE_COLLECTION, collection.id)
            self._tree.addTopLevelItem(item)
            collection_items[collection.id] = item

        if 0 == len(collection_items):
            fallback = WorkspaceCollection(id="col-1", name="Default")
            item = self._create_item(fallback.name, self._TYPE_COLLECTION, fallback.id)
            self._tree.addTopLevelItem(item)
            collection_items[fallback.id] = item

        folder_items: dict[str, QTreeWidgetItem] = {}
        ordered_folders = sorted(folders, key=lambda item: (item.collection_id, item.order))
        for folder in ordered_folders:
            parent_item = None
            if folder.parent_id is not None:
                parent_item = folder_items.get(folder.parent_id)
            if parent_item is None:
                parent_item = collection_items.get(folder.collection_id)
            if parent_item is None:
                parent_item = next(iter(collection_items.values()))

            folder_item = self._create_item(folder.name, self._TYPE_FOLDER, folder.id)
            parent_item.addChild(folder_item)
            folder_items[folder.id] = folder_item

        for request in requests:
            parent_item = folder_items.get(request.folder_id)
            if parent_item is None:
                continue
            request_item = self._create_item(request.name, self._TYPE_REQUEST, request.id)
            parent_item.addChild(request_item)

        self._tree.expandAll()

    def _on_selection_changed(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            return
        
        item = items[0]
        item_type = self._item_type(item)
        if item_type == self._TYPE_REQUEST:
            request_id = item.data(0, self._ID_ROLE)
            if request_id:
                self.request_selected.emit(request_id)

    def _populate_dummy_data(self) -> None:
        self._reset_counters()
        sample_collection = self._create_item("Sample API", self._TYPE_COLLECTION, "col-1")
        users_folder = self._create_item("Users", self._TYPE_FOLDER, "folder-1")
        users_folder.addChild(self._create_item("List Users", self._TYPE_REQUEST, "req-1"))
        users_folder.addChild(self._create_item("Create User", self._TYPE_REQUEST, "req-2"))
        sample_collection.addChild(users_folder)

        auth_folder = self._create_item("Auth", self._TYPE_FOLDER, "folder-2")
        auth_folder.addChild(self._create_item("Login", self._TYPE_REQUEST, "req-3"))
        auth_folder.addChild(self._create_item("Refresh Token", self._TYPE_REQUEST, "req-4"))
        sample_collection.addChild(auth_folder)

        self._tree.addTopLevelItem(sample_collection)

        sandbox_collection = self._create_item("Sandbox", self._TYPE_COLLECTION, "col-2")
        sandbox_collection.addChild(self._create_item("Health Check", self._TYPE_REQUEST, "req-5"))
        self._tree.addTopLevelItem(sandbox_collection)

        self._tree.expandAll()

    def select_request_item(self, request_id: str) -> None:
        item = self._items_by_id.get(request_id)
        if item is None:
            return

        current_items = self._tree.selectedItems()
        if current_items and current_items[0] is item:
            return

        self._tree.setCurrentItem(item)
        self._tree.scrollToItem(item)

    def _collect_folders(
        self,
        parent_item: QTreeWidgetItem,
        collection_id: str,
        parent_folder_id: str | None,
        folders: list[WorkspaceFolder],
    ) -> None:
        for index in range(parent_item.childCount()):
            child = parent_item.child(index)
            if child is None:
                continue
            if self._item_type(child) == self._TYPE_REQUEST:
                continue
            folder_id = self._ensure_item_id(child, self._TYPE_FOLDER)
            folders.append(
                WorkspaceFolder(
                    id=folder_id,
                    collection_id=collection_id,
                    parent_id=parent_folder_id,
                    name=child.text(0),
                    order=index,
                )
            )
            self._collect_folders(child, collection_id, folder_id, folders)

    def _create_item(self, name: str, item_type: str, item_id: str | None = None) -> QTreeWidgetItem:
        resolved_id = item_id or self._next_id(item_type)
        item = QTreeWidgetItem([name])
        item.setData(0, self._ID_ROLE, resolved_id)
        item.setData(0, self._TYPE_ROLE, item_type)
        self._items_by_id[resolved_id] = item
        if item_id is not None:
            self._track_counter(item_type, resolved_id)
        return item

    def _ensure_item_id(self, item: QTreeWidgetItem, item_type: str) -> str:
        item_id = item.data(0, self._ID_ROLE)
        if isinstance(item_id, str) and 0 < len(item_id):
            return item_id
        resolved_id = self._next_id(item_type)
        item.setData(0, self._ID_ROLE, resolved_id)
        item.setData(0, self._TYPE_ROLE, item_type)
        return resolved_id

    def _item_type(self, item: QTreeWidgetItem) -> str:
        value = item.data(0, self._TYPE_ROLE)
        if isinstance(value, str):
            return value
        if 0 < item.childCount():
            return self._TYPE_FOLDER
        return self._TYPE_REQUEST

    def _next_id(self, item_type: str) -> str:
        if item_type == self._TYPE_COLLECTION:
            current = self._collection_id_counter
            self._collection_id_counter += 1
            return f"col-{current}"
        if item_type == self._TYPE_FOLDER:
            current = self._folder_id_counter
            self._folder_id_counter += 1
            return f"folder-{current}"
        current = self._request_id_counter
        self._request_id_counter += 1
        return f"req-{current}"

    def _reset_counters(self) -> None:
        self._collection_id_counter = 1
        self._folder_id_counter = 1
        self._request_id_counter = 1
        self._items_by_id.clear()

    def _track_counter(self, item_type: str, item_id: str) -> None:
        if item_type == self._TYPE_COLLECTION:
            prefix = "col-"
            counter_name = "_collection_id_counter"
        elif item_type == self._TYPE_FOLDER:
            prefix = "folder-"
            counter_name = "_folder_id_counter"
        else:
            prefix = "req-"
            counter_name = "_request_id_counter"

        if not item_id.startswith(prefix):
            return
        suffix = item_id[len(prefix) :]
        if not suffix.isdigit():
            return
        value = int(suffix) + 1
        current = getattr(self, counter_name)
        if current < value:
            setattr(self, counter_name, value)
