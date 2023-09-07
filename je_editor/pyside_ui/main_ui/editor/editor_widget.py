import pathlib
from pathlib import Path

from PySide6.QtCore import Qt, QFileInfo, QDir
from PySide6.QtWidgets import QWidget, QGridLayout, QSplitter, QScrollArea, QFileSystemModel, QTreeView

from je_editor.pyside_ui.code.auto_save import auto_save_thread
from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.code.textedit_code_result.code_record import CodeRecord
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.file.open.open_file import read_file


class EditorWidget(QWidget):

    def __init__(self):
        super().__init__()
        # Init variable
        self.auto_save_thread = None
        self.current_file = None
        self.tree_view_scroll_area = None
        self.project_treeview = None
        self.project_treeview_model = None
        self.python_compiler = None
        # UI
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle("JEditor")
        # Treeview
        self.set_project_treeview()
        # Use to put full ui
        self.full_splitter = QSplitter()
        self.full_splitter.setOrientation(Qt.Orientation.Horizontal)
        # Code edit and result QSplitter
        self.edit_splitter = QSplitter(self.full_splitter)
        self.edit_splitter.setOrientation(Qt.Orientation.Vertical)
        # code edit and code result plaintext
        self.code_edit = CodeEditor()
        self.code_result = CodeRecord()
        self.code_edit_scroll_area = QScrollArea()
        self.code_edit_scroll_area.setWidgetResizable(True)
        self.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_edit_scroll_area.setWidget(self.code_edit)
        self.code_result_scroll_area = QScrollArea()
        self.code_result_scroll_area.setWidgetResizable(True)
        self.code_result_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_result_scroll_area.setWidget(self.code_result)
        # Edit splitter
        self.edit_splitter.addWidget(self.code_edit_scroll_area)
        self.edit_splitter.addWidget(self.code_result_scroll_area)
        self.edit_splitter.setStretchFactor(0, 3)
        self.edit_splitter.setStretchFactor(1, 1)
        self.edit_splitter.setSizes([300, 100])
        self.full_splitter.addWidget(self.project_treeview)
        self.full_splitter.addWidget(self.edit_splitter)
        self.full_splitter.setStretchFactor(0, 1)
        self.full_splitter.setStretchFactor(1, 3)
        self.full_splitter.setSizes([100, 300])
        # Font
        self.code_edit.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        self.code_result.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        # Add to layout
        self.grid_layout.addWidget(self.full_splitter)
        # current file
        self.current_file = None
        if self.current_file is not None and self.auto_save_thread is None:
            auto_save_thread.auto_save_instance.file = self.current_file
            auto_save_thread.auto_save_instance.editor = self.code_edit
            if not auto_save_thread.auto_save_instance.is_alive():
                auto_save_thread.auto_save_instance.start()

    def set_project_treeview(self) -> None:
        self.project_treeview_model = QFileSystemModel()
        self.project_treeview_model.setRootPath(QDir.currentPath())
        self.project_treeview = QTreeView()
        self.project_treeview.setModel(self.project_treeview_model)
        self.project_treeview.setRootIndex(
            self.project_treeview_model.index(str(Path.cwd()))
        )
        self.tree_view_scroll_area = QScrollArea()
        self.tree_view_scroll_area.setWidgetResizable(True)
        self.tree_view_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.tree_view_scroll_area.setWidget(self.project_treeview)
        self.grid_layout.addWidget(self.tree_view_scroll_area, 0, 0, 0, 1)
        self.project_treeview.clicked.connect(
            self.treeview_click
        )

    def treeview_click(self) -> None:
        clicked_item: QFileSystemModel = self.project_treeview.selectedIndexes()[0]
        file_info: QFileInfo = self.project_treeview.model().fileInfo(clicked_item)
        path = pathlib.Path(file_info.absoluteFilePath())
        if path.is_file():
            file, file_content = read_file(str(path))
            self.code_edit.setPlainText(
                file_content
            )
            self.current_file = file
            auto_save_thread.auto_save_instance.file = self.current_file
            auto_save_thread.auto_save_instance.editor = self.code_edit
            if not auto_save_thread.auto_save_instance.is_alive():
                auto_save_thread.auto_save_instance.start()
            if self.auto_save_thread is not None:
                self.auto_save_thread.file = self.current_file
            user_setting_dict.update({"last_file": str(self.current_file)})
