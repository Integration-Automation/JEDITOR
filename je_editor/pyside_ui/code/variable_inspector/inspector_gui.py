import ast

from PySide6.QtCore import QAbstractTableModel, Qt, QTimer, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget, QLineEdit, QLabel

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class VariableModel(QAbstractTableModel):
    """
    變數模型：負責管理與顯示 Python 全域變數
    Variable model: manages and displays Python global variables
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variables = []  # 儲存變數資訊 [名稱, 型別, 值字串, 真實值]
                            # Store variable info [name, type, repr(value), actual value]

    def update_data(self):
        """
        更新變數清單，從全域變數中擷取
        Update variable list from globals()
        """
        parent_widget = self.parent()
        # 避免在 table 正在互動時更新，造成衝突
        # Avoid updating while table is in active state
        if parent_widget and getattr(parent_widget, "table", None):
            if parent_widget.table.state() != QTableView.State.NoState:
                return

        vars_dict = globals()
        self.beginResetModel()
        self.variables = [
            [name, type(value).__name__, repr(value), value]
            for name, value in vars_dict.items()
            if not name.startswith("__")  # 過濾內建變數 / filter out built-in variables
        ]
        self.endResetModel()

    def rowCount(self, parent=None):
        # 回傳變數數量 / return number of variables
        return len(self.variables)

    def columnCount(self, parent=None):
        # 固定三欄：名稱、型別、值 / fixed 3 columns: name, type, value
        return 3

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        # 提供表格顯示的資料
        # Provide data for table display
        if not index.isValid() or not (0 <= index.row() < len(self.variables)):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.variables[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        # 設定表頭文字 (支援多語系)
        # Set header labels (multi-language support)
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return [
                language_wrapper.language_word_dict.get("variable_inspector_var_name"),
                language_wrapper.language_word_dict.get("variable_inspector_var_type"),
                language_wrapper.language_word_dict.get("variable_inspector_var_value")
            ][section]
        return None

    def flags(self, index):
        # 設定欄位屬性，僅允許「值」欄可編輯
        # Set column flags, only "value" column is editable
        if not index.isValid() or not (0 <= index.row() < len(self.variables)):
            return Qt.ItemFlag.NoItemFlags
        base = super().flags(index)
        if index.column() == 2:  # 只允許編輯值欄 / only value column editable
            base |= Qt.ItemFlag.ItemIsEditable
        return base

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        更新變數值，並同步到全域變數
        Update variable value and sync to globals()
        """
        if role == Qt.ItemDataRole.EditRole and index.column() == 2:

            if value == "":
                return False

            old_repr = self.variables[index.row()][2]
            if str(value) == old_repr:
                return False

            var_name = self.variables[index.row()][0]
            try:
                # 嘗試將輸入轉換為 Python 物件
                # Try to evaluate input as Python object
                new_value = ast.literal_eval(value)
            except Exception:
                # 若失敗則當作字串處理
                # If failed, treat as string
                new_value = value

            if new_value == self.variables[index.row()][3]:
                return False

            # 更新全域變數與模型資料
            # Update globals and model data
            globals()[var_name] = new_value
            self.variables[index.row()][2] = repr(new_value)
            self.variables[index.row()][3] = new_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False


class VariableProxy(QSortFilterProxyModel):
    """
    過濾代理模型：支援搜尋與編輯轉發
    Proxy model: supports filtering and forwards editing
    """
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        # 將編輯操作轉發到原始模型
        # Forward editing to source model
        return self.sourceModel().setData(
            self.mapToSource(index), value, role
        )


class VariableInspector(QWidget):
    """
    變數檢視器：提供 GUI 介面顯示與搜尋全域變數
    Variable inspector: GUI interface to display and search global variables
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(language_wrapper.language_word_dict.get("variable_inspector_title"))
        layout = QVBoxLayout(self)

        # 搜尋框 / search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(language_wrapper.language_word_dict.get("variable_inspector_search"))
        layout.addWidget(QLabel(language_wrapper.language_word_dict.get("variable_inspector_search")))
        layout.addWidget(self.search_box)

        # 模型與代理模型 / model and proxy model
        self.model = VariableModel(parent=self)
        self.proxy_model = VariableProxy(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)  # 不分大小寫 / case-insensitive
        self.proxy_model.setFilterKeyColumn(0)  # 僅針對變數名稱過濾 / filter by variable name

        # 表格顯示 / table view
        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            self.table.horizontalHeader().ResizeMode.Stretch
        )
        layout.addWidget(self.table, stretch=1)

        # 綁定搜尋框輸入事件 / bind search box input
        self.search_box.textChanged.connect(
            self.proxy_model.setFilterFixedString
        )

        # 定時更新變數清單 (每 500ms)
        # Periodically update variable list (every 500ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.model.update_data)
        self.timer.start(500)