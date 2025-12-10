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
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
)


class ResultsTable(QWidget):
    """Table widget showing search results with selection checkboxes."""

    selectionChanged = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._results: List[Dict] = []

        # Make the widget expand
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Modified
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Drive
        self.table.setColumnWidth(0, 30)

        layout.addWidget(self.table, 1)  # stretch factor 1

        # Selection buttons
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()

        self.expand_btn = QPushButton("Expand ⤢")
        self.expand_btn.clicked.connect(self._show_expanded_dialog)
        self.expand_btn.setEnabled(False)
        btn_layout.addWidget(self.expand_btn)

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
        self.expand_btn.setEnabled(len(results) > 0)
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
        self.expand_btn.setEnabled(False)
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
        self.expand_btn.setEnabled(enabled and self.has_results())

    def _show_expanded_dialog(self):
        """Show results in an expanded modal dialog."""
        dialog = ExpandedResultsDialog(self._results, self._get_checked_rows(), self)
        if dialog.exec_() == QDialog.Accepted:
            # Sync checkbox state back from dialog
            checked_rows = dialog.get_checked_rows()
            for row in range(self.table.rowCount()):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox:
                    checkbox.setChecked(row in checked_rows)

    def _get_checked_rows(self) -> set:
        """Get set of checked row indices."""
        checked = set()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                checked.add(row)
        return checked


class ExpandedResultsDialog(QDialog):
    """Modal dialog showing results in a larger view."""

    def __init__(
        self,
        results: List[Dict],
        checked_rows: set,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._results = results
        self._checked_rows = checked_rows.copy()

        self.setWindowTitle(f"Search Results ({len(results)} files)")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Name", "Type", "Modified", "Drive"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(0, 30)

        self._populate_table()
        layout.addWidget(self.table, 1)

        # Selection buttons row
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(deselect_all_btn)

        btn_layout.addStretch()

        self.selection_label = QLabel()
        self._update_selection_label()
        btn_layout.addWidget(self.selection_label)

        layout.addLayout(btn_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_table(self):
        """Populate the table with results."""
        mime_map = {
            "application/vnd.google-apps.document": "Document",
            "application/vnd.google-apps.spreadsheet": "Spreadsheet",
            "application/vnd.google-apps.presentation": "Presentation",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
            "application/pdf": "PDF",
        }

        self.table.setRowCount(len(self._results))
        for row, item in enumerate(self._results):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(row in self._checked_rows)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            self.table.setCellWidget(row, 0, checkbox)

            # Name
            self.table.setItem(row, 1, QTableWidgetItem(item.get("name", "")))

            # Type
            mime_type = item.get("mimeType", "")
            type_display = mime_map.get(
                mime_type, mime_type.split("/")[-1] if "/" in mime_type else mime_type
            )
            self.table.setItem(row, 2, QTableWidgetItem(type_display))

            # Modified date
            modified = item.get("modifiedTime", "")[:10] if item.get("modifiedTime") else ""
            self.table.setItem(row, 3, QTableWidgetItem(modified))

            # Drive name
            drive = item.get("drive", "My Drive")
            self.table.setItem(row, 4, QTableWidgetItem(drive))

    def _on_checkbox_changed(self):
        """Update checked rows set when checkbox changes."""
        self._checked_rows = set()
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                self._checked_rows.add(row)
        self._update_selection_label()

    def _update_selection_label(self):
        """Update the selection count label."""
        count = len(self._checked_rows)
        self.selection_label.setText(f"{count} of {len(self._results)} selected")

    def _select_all(self):
        """Select all rows."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def _deselect_all(self):
        """Deselect all rows."""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def get_checked_rows(self) -> set:
        """Get set of checked row indices."""
        return self._checked_rows.copy()
