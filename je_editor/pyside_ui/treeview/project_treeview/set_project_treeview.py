from PySide6.QtCore import QDir
from PySide6.QtWidgets import QMainWindow, QFileSystemModel, QTreeView


def set_project_treeview(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.grid_layout.setColumnStretch(0, 4)
    ui_we_want_to_set.project_treeview_model = QFileSystemModel()
    ui_we_want_to_set.project_treeview_model.setRootPath(QDir.currentPath())
    ui_we_want_to_set.project_treeview = QTreeView()
    ui_we_want_to_set.project_treeview.setModel(ui_we_want_to_set.project_treeview_model)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.project_treeview, 0, 0, 0, 1)