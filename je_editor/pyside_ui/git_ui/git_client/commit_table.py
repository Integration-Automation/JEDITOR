from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QTableView


class CommitTable(QTableView):
    """
    CommitTable 類別：用來顯示 Git Commit 紀錄的表格
    CommitTable class: A table view to display Git commit history
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 建立一個 QStandardItemModel，初始為 0 行 5 欄
        # Create a QStandardItemModel with 0 rows and 5 columns
        self.model_data = QStandardItemModel(0, 5, self)  # 多一欄 / 5 columns

        # 設定表頭標籤
        # Set horizontal header labels
        self.model_data.setHorizontalHeaderLabels(["#", "SHA", "Message", "Author", "Date"])

        # 將模型綁定到 QTableView
        # Set the model for QTableView
        self.setModel(self.model_data)

        # 設定選擇行為為整列選取
        # Set selection behavior to select entire rows
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        # 禁止編輯表格內容
        # Disable editing of table cells
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        # 讓最後一欄自動延展填滿
        # Stretch the last column to fill available space
        self.horizontalHeader().setStretchLastSection(True)

    def set_commits(self, commits):
        """
        將 commit 資料填入表格
        Populate the table with commit data
        :param commits: commit 資料清單 (list of dicts with sha, message, author, date)
        """
        # 清空現有資料
        # Clear existing rows
        self.model_data.setRowCount(0)

        # 遍歷 commit 清單，逐行加入表格
        # Iterate over commits and append rows
        for index, commit in enumerate(commits, start=1):
            row = [
                QStandardItem(str(index)),          # 行號 / row number
                QStandardItem(commit["sha"][:7]),      # SHA 短碼 / short SHA
                QStandardItem(commit["message"]),      # 提交訊息 / commit message
                QStandardItem(commit["author"]),       # 作者 / author
                QStandardItem(commit["date"]),         # 日期 / date
            ]
            # 設定每個欄位不可編輯
            # Make each item non-editable
            for item in row:
                item.setEditable(False)

            # 將這一列加入模型
            # Append row to the model
            self.model_data.appendRow(row)