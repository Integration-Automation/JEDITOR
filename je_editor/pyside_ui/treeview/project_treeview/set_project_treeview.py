import os
import pathlib

from PySide6.QtCore import QDir, QModelIndex
from PySide6.QtWidgets import QMainWindow, QFileSystemModel, QTreeView

from je_editor.utils.file.open.open_file import read_file


def set_project_treeview(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.grid_layout.setColumnStretch(0, 4)
    ui_we_want_to_set.project_treeview_model = QFileSystemModel()
    ui_we_want_to_set.project_treeview_model.setRootPath(QDir.currentPath())
    ui_we_want_to_set.project_treeview = QTreeView()
    ui_we_want_to_set.project_treeview.setModel(ui_we_want_to_set.project_treeview_model)
    ui_we_want_to_set.project_treeview.setRootIndex(
        ui_we_want_to_set.project_treeview_model.index(os.getcwd())
    )
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.project_treeview, 0, 0, 0, 1)
    ui_we_want_to_set.project_treeview.clicked.connect(
        lambda: treeview_click(ui_we_want_to_set)
    )


def treeview_click(ui_we_want_to_set):
    clicked_item: QModelIndex = ui_we_want_to_set.project_treeview.currentIndex()
    model = clicked_item.model()
    path = pathlib.Path(os.getcwd() + "/" + model.data(clicked_item))
    if path.is_file():
        file, file_content = read_file(path)
        ui_we_want_to_set.code_edit.setPlainText(
            file_content
        )
