import os
import pathlib

from PySide6.QtCore import QDir, QFileInfo
from PySide6.QtWidgets import QMainWindow, QFileSystemModel, QTreeView, QScrollArea

from je_editor.pyside_ui.auto_save.auto_save_thread import SaveThread
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
    ui_we_want_to_set.tree_view_scroll_area = QScrollArea()
    ui_we_want_to_set.tree_view_scroll_area.setWidgetResizable(True)
    ui_we_want_to_set.tree_view_scroll_area.setViewportMargins(0, 0, 0, 0)
    ui_we_want_to_set.tree_view_scroll_area.setWidget(ui_we_want_to_set.project_treeview)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.tree_view_scroll_area, 0, 0, 0, 1)
    ui_we_want_to_set.project_treeview.clicked.connect(
        lambda: treeview_click(ui_we_want_to_set)
    )


def treeview_click(ui_we_want_to_set):
    clicked_item: QFileSystemModel = ui_we_want_to_set.project_treeview.selectedIndexes()[0]
    file_info: QFileInfo = ui_we_want_to_set.project_treeview.model().fileInfo(clicked_item)
    path = pathlib.Path(file_info.absoluteFilePath())
    if path.is_file():
        file, file_content = read_file(path)
        ui_we_want_to_set.code_edit.setPlainText(
            file_content
        )
        ui_we_want_to_set.current_file = file
        if ui_we_want_to_set.auto_save_thread is None:
            ui_we_want_to_set.auto_save_thread = SaveThread(
                ui_we_want_to_set.current_file,
                ui_we_want_to_set.code_edit.toPlainText()
            )
            ui_we_want_to_set.auto_save_thread.start()
        if ui_we_want_to_set.auto_save_thread is not None:
            ui_we_want_to_set.auto_save_thread.file = ui_we_want_to_set.current_file
