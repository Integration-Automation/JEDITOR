import ast

from PySide6.QtCore import QAbstractTableModel, Qt, QTimer, QSortFilterProxyModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget, QLineEdit, QLabel

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class VariableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variables = []

    def update_data(self):
        parent_widget = self.parent()
        if parent_widget and getattr(parent_widget, "table", None):
            if parent_widget.table.state() != QTableView.State.NoState:
                return

        vars_dict = globals()
        self.beginResetModel()
        self.variables = [
            [name, type(value).__name__, repr(value), value]
            for name, value in vars_dict.items()
            if not name.startswith("__")  # 過濾內建變數
        ]
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self.variables)

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.variables)):
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self.variables[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return [
                language_wrapper.language_word_dict.get("variable_inspector_var_name"),
                language_wrapper.language_word_dict.get("variable_inspector_var_type"),
                language_wrapper.language_word_dict.get("variable_inspector_var_value")
            ][section]
        return None

    def flags(self, index):
        if not index.isValid() or not (0 <= index.row() < len(self.variables)):
            return Qt.ItemFlag.NoItemFlags
        base = super().flags(index)
        if index.column() == 2:  # 只允許編輯值欄
            base |= Qt.ItemFlag.ItemIsEditable
        return base

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.column() == 2:

            if value == "":
                return False

            old_repr = self.variables[index.row()][2]
            if str(value) == old_repr:
                return False

            var_name = self.variables[index.row()][0]
            try:
                new_value = ast.literal_eval(value)
            except Exception:
                new_value = value

            if new_value == self.variables[index.row()][3]:
                return False

            globals()[var_name] = new_value
            self.variables[index.row()][2] = repr(new_value)
            self.variables[index.row()][3] = new_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        return False

class VariableProxy(QSortFilterProxyModel):
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        return self.sourceModel().setData(
            self.mapToSource(index), value, role
        )

class VariableInspector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(language_wrapper.language_word_dict.get("variable_inspector_title"))
        layout = QVBoxLayout(self)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(language_wrapper.language_word_dict.get("variable_inspector_search"))
        layout.addWidget(QLabel(language_wrapper.language_word_dict.get("variable_inspector_search")))
        layout.addWidget(self.search_box)

        self.model = VariableModel(parent=self)
        self.proxy_model = VariableProxy(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(0)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            self.table.horizontalHeader().ResizeMode.Stretch
        )
        layout.addWidget(self.table, stretch=1)

        self.search_box.textChanged.connect(
            self.proxy_model.setFilterFixedString
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.model.update_data)
        self.timer.start(500)
