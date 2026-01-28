from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget


class CollectionTreePanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Collections")
        layout.addWidget(self._tree)

        self._populate_dummy_data()

    def _populate_dummy_data(self) -> None:
        sample_collection = QTreeWidgetItem(["Sample API"])
        users_folder = QTreeWidgetItem(["Users"])
        users_folder.addChild(QTreeWidgetItem(["List Users"]))
        users_folder.addChild(QTreeWidgetItem(["Create User"]))
        sample_collection.addChild(users_folder)

        auth_folder = QTreeWidgetItem(["Auth"])
        auth_folder.addChild(QTreeWidgetItem(["Login"]))
        auth_folder.addChild(QTreeWidgetItem(["Refresh Token"]))
        sample_collection.addChild(auth_folder)

        self._tree.addTopLevelItem(sample_collection)

        sandbox_collection = QTreeWidgetItem(["Sandbox"])
        sandbox_collection.addChild(QTreeWidgetItem(["Health Check"]))
        self._tree.addTopLevelItem(sandbox_collection)

        self._tree.expandAll()
