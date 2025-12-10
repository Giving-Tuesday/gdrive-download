"""Results table widget with checkboxes for file selection."""

from typing import List, Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QCheckBox,
    QAbstractItemView,
)


class ResultsTable(QWidget):
    """Table widget showing search results with selection checkboxes."""

    selectionChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._results: List[Dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Results count label
        self.count_label = QLabel("No results")
        layout.addWidget(self.count_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Name", "Type", "Modified", "Drive"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Modified
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Drive
        self.table.setColumnWidth(0, 30)

        layout.addWidget(self.table)

        # Selection buttons
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def populate(self, results: List[Dict]):
        """Populate the table with search results."""
        self._results = results
        self.table.setRowCount(len(results))

        for row, item in enumerate(results):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda: self.selectionChanged.emit())
            self.table.setCellWidget(row, 0, checkbox)

            # Name
            name_item = QTableWidgetItem(item.get("name", ""))
            name_item.setData(Qt.UserRole, item)  # Store full data
            self.table.setItem(row, 1, name_item)

            # Type (extract from mimeType)
            mime_type = item.get("mimeType", "")
            type_display = self._mime_to_display(mime_type)
            self.table.setItem(row, 2, QTableWidgetItem(type_display))

            # Modified date
            modified = item.get("modifiedTime", "")[:10] if item.get("modifiedTime") else ""
            self.table.setItem(row, 3, QTableWidgetItem(modified))

            # Drive name
            drive = item.get("drive", "My Drive")
            self.table.setItem(row, 4, QTableWidgetItem(drive))

        self.count_label.setText(f"{len(results)} file(s) found")
        self.selectionChanged.emit()

    def _mime_to_display(self, mime_type: str) -> str:
        """Convert MIME type to display string."""
        mime_map = {
            "application/vnd.google-apps.document": "Document",
            "application/vnd.google-apps.spreadsheet": "Spreadsheet",
            "application/vnd.google-apps.presentation": "Presentation",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
            "application/pdf": "PDF",
        }
        return mime_map.get(mime_type, mime_type.split("/")[-1] if "/" in mime_type else mime_type)

    def clear(self):
        """Clear all results."""
        self._results = []
        self.table.setRowCount(0)
        self.count_label.setText("No results")
        self.selectionChanged.emit()

    def select_all(self):
        """Select all rows."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def deselect_all(self):
        """Deselect all rows."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def get_selected(self) -> List[Dict]:
        """Get list of selected file data."""
        selected = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                item = self.table.item(row, 1)
                if item:
                    data = item.data(Qt.UserRole)
                    if data:
                        selected.append(data)
        return selected

    def get_all(self) -> List[Dict]:
        """Get all results."""
        return self._results.copy()

    def has_results(self) -> bool:
        """Check if there are any results."""
        return len(self._results) > 0

    def has_selection(self) -> bool:
        """Check if any rows are selected."""
        return len(self.get_selected()) > 0

    def setEnabled(self, enabled: bool):
        """Enable/disable the widget."""
        self.table.setEnabled(enabled)
        self.select_all_btn.setEnabled(enabled)
        self.deselect_all_btn.setEnabled(enabled)
