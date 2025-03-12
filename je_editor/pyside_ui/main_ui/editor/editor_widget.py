from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager
    from je_editor.pyside_ui.code.code_process.code_exec import ExecManager

import pathlib
from pathlib import Path
from typing import Union

from PySide6.QtCore import Qt, QFileInfo, QDir
from PySide6.QtWidgets import QWidget, QGridLayout, QSplitter, QScrollArea, QFileSystemModel, QTreeView, QTabWidget, \
    QMessageBox

from je_editor.pyside_ui.code.auto_save.auto_save_manager import auto_save_manager_dict, init_new_auto_save_thread, \
    file_is_open_manager_dict
from je_editor.pyside_ui.code.auto_save.auto_save_thread import CodeEditSaveThread
from je_editor.pyside_ui.code.code_format.pep8_format import PEP8FormatChecker
from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.code.textedit_code_result.code_record import CodeRecord
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.file.open.open_file import read_file


class EditorWidget(QWidget):

    def __init__(self, main_window: EditorMain):
        jeditor_logger.info(f"Init EditorWidget main_window: {main_window}")
        super().__init__()
        # Init variable
        self.checker: Union[PEP8FormatChecker, None] = None
        self.current_file = None
        self.tree_view_scroll_area = None
        self.project_treeview = None
        self.project_treeview_model = None
        self.python_compiler = None
        self.main_window = main_window
        self.tab_manager = self.main_window.tab_widget
        # Attr
        # Current execute instance if none not running
        self.exec_program: Union[None, ExecManager] = None
        self.exec_shell: Union[None, ShellManager] = None
        self.exec_python_debugger: Union[None, ExecManager] = None
        # Autosave
        self.code_save_thread: Union[CodeEditSaveThread, None] = None
        # UI
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))
        # Treeview
        self.set_project_treeview()
        # Use to put full ui
        self.full_splitter = QSplitter()
        self.full_splitter.setOrientation(Qt.Orientation.Horizontal)
        # Code edit and result QSplitter
        self.edit_splitter = QSplitter(self.full_splitter)
        self.edit_splitter.setOrientation(Qt.Orientation.Vertical)
        # code edit and code result plaintext
        self.code_edit = CodeEditor(self)
        self.code_result = CodeRecord()
        self.code_edit_scroll_area = QScrollArea()
        self.code_edit_scroll_area.setWidgetResizable(True)
        self.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_edit_scroll_area.setWidget(self.code_edit)
        self.code_result_scroll_area = QScrollArea()
        self.code_result_scroll_area.setWidgetResizable(True)
        self.code_result_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_result_scroll_area.setWidget(self.code_result)
        # Code format checker
        self.format_check_result = CodeRecord()
        self.format_check_result.setTextColor(actually_color_dict.get("warning_output_color"))
        # Debugger
        self.debugger_result = CodeRecord()
        # Code result tab
        self.code_difference_result = QTabWidget()
        self.code_difference_result.addTab(
            self.code_result_scroll_area, language_wrapper.language_word_dict.get("editor_code_result"))
        self.code_difference_result.addTab(
            self.format_check_result, language_wrapper.language_word_dict.get("editor_format_check"))
        self.code_difference_result.addTab(
            self.debugger_result, language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))
        # Edit splitter
        self.edit_splitter.addWidget(self.code_edit_scroll_area)
        self.edit_splitter.addWidget(self.code_difference_result)
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

    def set_project_treeview(self) -> None:
        jeditor_logger.info("EditorWidget set_project_treeview")
        self.project_treeview_model = QFileSystemModel()
        self.project_treeview_model.setRootPath(QDir.currentPath())
        self.project_treeview = QTreeView()
        self.project_treeview.setModel(self.project_treeview_model)
        if self.main_window.working_dir is None:
            self.project_treeview.setRootIndex(
                self.project_treeview_model.index(str(Path.cwd()))
            )
        else:
            self.project_treeview.setRootIndex(
                self.project_treeview_model.index(self.main_window.working_dir)
            )
        self.tree_view_scroll_area = QScrollArea()
        self.tree_view_scroll_area.setWidgetResizable(True)
        self.tree_view_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.tree_view_scroll_area.setWidget(self.project_treeview)
        self.grid_layout.addWidget(self.tree_view_scroll_area, 0, 0, 0, 1)
        self.project_treeview.clicked.connect(self.treeview_click)

    def check_is_open(self, path: Path):
        jeditor_logger.info(f"EditorWidget check_is_open path: {path}")
        if file_is_open_manager_dict.get(str(path), None) is not None:
            widget: QWidget = self.tab_manager.findChild(EditorWidget, str(path))
            if widget is None:
                file_is_open_manager_dict.pop(str(path), None)
            else:
                self.tab_manager.setCurrentWidget(widget)
                return False
        else:
            file_is_open_manager_dict.update({str(path): str(path)})
            return True

    def open_an_file(self, path: Path) -> bool:
        """
        :param path: open file path
        :return: return False if file tab exists
        """
        jeditor_logger.info(f"EditorWidget open_an_file path: {path}")
        if not self.check_is_open(path):
            return False
        if self.code_save_thread:
            self.code_save_thread.skip_this_round = True
        file, file_content = read_file(str(path))
        self.code_edit.setPlainText(
            file_content
        )
        self.current_file = file
        self.code_edit.current_file = file
        self.code_edit.reset_highlighter()
        user_setting_dict.update({"last_file": str(self.current_file)})
        if self.current_file is not None and self.code_save_thread is None:
            init_new_auto_save_thread(self.current_file, self)
        else:
            self.code_save_thread.file = self.current_file
            self.code_save_thread.skip_this_round = False
        self.rename_self_tab()
        return True

    def treeview_click(self) -> None:
        jeditor_logger.info("EditorWidget treeview_click")
        clicked_item: QFileSystemModel = self.project_treeview.selectedIndexes()[0]
        file_info: QFileInfo = self.project_treeview.model().fileInfo(clicked_item)
        path = pathlib.Path(file_info.absoluteFilePath())
        if path.is_file():
            self.open_an_file(path)

    def rename_self_tab(self):
        jeditor_logger.info("EditorWidget rename_self_tab")
        if self.tab_manager.currentWidget() is self:
            self.tab_manager.setTabText(
                self.tab_manager.currentIndex(), str(Path(self.current_file)))
            self.setObjectName(str(Path(self.current_file)))

    def check_file_format(self):
        if self.current_file:
            jeditor_logger.info("EditorWidget check_file_format")
            suffix_checker = Path(self.current_file).suffix
            if suffix_checker == ".py":
                self.checker = PEP8FormatChecker(self.current_file)
                self.checker.check_all_format()
                self.format_check_result.setPlainText("")
                for error in self.checker.error_list:
                    self.format_check_result.append(error)
                self.checker.error_list.clear()
            else:
                message_box = QMessageBox()
                message_box.setText(
                    language_wrapper.language_word_dict.get("python_format_checker_only_support_python_message"))
                message_box.exec_()

    def close(self) -> bool:
        jeditor_logger.info("EditorWidget close")
        if self.code_save_thread is not None:
            self.code_save_thread.still_run = False
            self.code_save_thread = None
        if self.current_file:
            file_is_open_manager_dict.pop(str(Path(self.current_file)), None)
            auto_save_manager_dict.pop(self.current_file, None)
        return super().close()
