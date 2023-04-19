from PySide6.QtCore import QDir
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QMainWindow, QScrollArea, QPlainTextEdit, QGridLayout, QWidget, QFileSystemModel, \
    QTreeView


def set_ui(ui_we_want_to_set: QMainWindow):
    # set qt window
    ui_we_want_to_set.q_widget = QWidget()
    ui_we_want_to_set.grid_layout = QGridLayout(ui_we_want_to_set.q_widget)
    ui_we_want_to_set.grid_layout.setContentsMargins(0, 0, 0, 0)
    ui_we_want_to_set.setCentralWidget(ui_we_want_to_set.q_widget)
    ui_we_want_to_set.resize(600, 600)
    ui_we_want_to_set.setWindowTitle("JEditor")
    # code edit and code result plaintext
    ui_we_want_to_set.code_edit = QPlainTextEdit()
    ui_we_want_to_set.code_edit.setLineWrapMode(ui_we_want_to_set.code_edit.LineWrapMode.NoWrap)
    ui_we_want_to_set.code_result = QPlainTextEdit()
    ui_we_want_to_set.code_result.setLineWrapMode(ui_we_want_to_set.code_edit.LineWrapMode.NoWrap)
    ui_we_want_to_set.code_result.setReadOnly(True)
    ui_we_want_to_set.code_edit_scroll_area = QScrollArea()
    ui_we_want_to_set.code_edit_scroll_area.setWidgetResizable(True)
    ui_we_want_to_set.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
    ui_we_want_to_set.code_edit_scroll_area.setWidget(ui_we_want_to_set.code_edit)
    ui_we_want_to_set.code_result_scroll_area = QScrollArea()
    ui_we_want_to_set.code_result_scroll_area.setWidgetResizable(True)
    ui_we_want_to_set.code_result_scroll_area.setViewportMargins(0, 0, 0, 0)
    ui_we_want_to_set.code_result_scroll_area.setWidget(ui_we_want_to_set.code_result)
    ui_we_want_to_set.grid_layout.setRowStretch(0, 10)
    ui_we_want_to_set.grid_layout.setColumnStretch(1, 10)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.code_edit_scroll_area, 0, 1)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.code_result_scroll_area, 1, 1)
    ui_we_want_to_set.grid_layout.setColumnStretch(0, 4)
    ui_we_want_to_set.project_treeview_model = QFileSystemModel()
    ui_we_want_to_set.project_treeview_model.setRootPath(QDir.currentPath())
    ui_we_want_to_set.project_treeview = QTreeView()
    ui_we_want_to_set.project_treeview.setModel(ui_we_want_to_set.project_treeview_model)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.project_treeview, 0, 0, 0, 1)
