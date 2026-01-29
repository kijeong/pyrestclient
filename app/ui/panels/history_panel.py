from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model import HistoryEntry


class HistoryPanel(QWidget):
    entry_selected = Signal(HistoryEntry)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        header_label = QLabel("History")
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Success", "Failure"])
        self._filter_combo.currentIndexChanged.connect(self._render_entries)

        header_row.addWidget(header_label)
        header_row.addStretch()
        header_row.addWidget(QLabel("Filter"))
        header_row.addWidget(self._filter_combo)
        layout.addLayout(header_row)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["Time", "Name", "Method", "URL", "Status", "Elapsed"]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.itemSelectionChanged.connect(self._emit_selection)

        layout.addWidget(self._table)

        self._entries: list[HistoryEntry] = []

    def set_entries(self, entries: list[HistoryEntry]) -> None:
        self._entries = list(reversed(entries))
        self._render_entries()

    def add_entry(self, entry: HistoryEntry) -> None:
        self._entries.insert(0, entry)
        self._render_entries()

    def _render_entries(self) -> None:
        filtered_entries = self._filtered_entries()
        self._table.setRowCount(len(filtered_entries))

        for row, entry in enumerate(filtered_entries):
            time_text = self._format_timestamp(entry.timestamp)
            status_text = self._format_status(entry)
            elapsed_text = f"{entry.elapsed_ms} ms" if entry.elapsed_ms is not None else ""

            row_values = [
                time_text,
                entry.name,
                entry.method,
                entry.url,
                status_text,
                elapsed_text,
            ]
            for column, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if 0 == column:
                    item.setData(Qt.ItemDataRole.UserRole, entry)
                if column == 4:
                    self._apply_status_style(item, entry)
                if column == 3:
                    item.setToolTip(entry.url)
                self._table.setItem(row, column, item)

        self._table.resizeColumnsToContents()

    def _filtered_entries(self) -> list[HistoryEntry]:
        filter_value = self._filter_combo.currentText()
        if filter_value == "Success":
            return [entry for entry in self._entries if entry.error is None]
        if filter_value == "Failure":
            return [entry for entry in self._entries if entry.error]
        return list(self._entries)

    def _emit_selection(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 0)
        if item is None:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(entry, HistoryEntry):
            self.entry_selected.emit(entry)

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        try:
            parsed = datetime.datetime.fromisoformat(timestamp)
        except ValueError:
            return timestamp
        return parsed.strftime("%H:%M:%S")

    @staticmethod
    def _format_status(entry: HistoryEntry) -> str:
        if entry.error:
            return entry.error
        if entry.status_code is not None:
            return str(entry.status_code)
        return "-"

    @staticmethod
    def _apply_status_style(item: QTableWidgetItem, entry: HistoryEntry) -> None:
        if entry.error:
            item.setForeground(QBrush(QColor("#b02a37")))
            item.setToolTip(entry.error)
            return
        if entry.status_code is None:
            return
        if 200 <= entry.status_code < 400:
            item.setForeground(QBrush(QColor("#0f5132")))
        elif 400 <= entry.status_code:
            item.setForeground(QBrush(QColor("#b02a37")))
