from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QTableView


class CommitTable(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_data = QStandardItemModel(0, 5, self)  # 多一欄
        self.model_data.setHorizontalHeaderLabels(["#", "SHA", "Message", "Author", "Date"])
        self.setModel(self.model_data)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)

    def set_commits(self, commits):
        self.model_data.setRowCount(0)
        for idx, c in enumerate(commits, start=1):
            row = [
                QStandardItem(str(idx)),  # 行號
                QStandardItem(c["sha"][:7]),
                QStandardItem(c["message"]),
                QStandardItem(c["author"]),
                QStandardItem(c["date"]),
            ]
            for item in row:
                item.setEditable(False)
            self.model_data.appendRow(row)
