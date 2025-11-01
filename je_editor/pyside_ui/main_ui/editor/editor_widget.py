from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QTextCharFormat

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
    """
    EditorWidget 是主要的程式碼編輯器元件，包含：
    - 專案檔案樹狀檢視
    - 程式碼編輯區
    - 執行結果、格式檢查、除錯輸出
    - 自動儲存與檔案管理

    EditorWidget is the main code editor widget, including:
    - Project file tree view
    - Code editing area
    - Execution result, format check, debugger output
    - Auto-save and file management
    """

    def __init__(self, main_window: EditorMain):
        jeditor_logger.info(f"Init EditorWidget main_window: {main_window}")
        super().__init__()
        # ---------------- Init variables 初始化變數 ----------------
        self.checker: Union[PEP8FormatChecker, None] = None
        self.current_file = None
        self.tree_view_scroll_area = None
        self.project_treeview: Union[QTreeView, None] = None
        self.project_treeview_model = None
        self.python_compiler = None
        self.main_window = main_window
        self.tab_manager = self.main_window.tab_widget

        # 執行相關物件 / Execution related objects
        self.exec_program: Union[None, ExecManager] = None
        self.exec_shell: Union[None, ShellManager] = None
        self.exec_python_debugger: Union[None, ExecManager] = None

        # 自動儲存執行緒 / Auto-save thread
        self.code_save_thread: Union[CodeEditSaveThread, None] = None

        # ---------------- UI 初始化 ----------------
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))

        # 建立專案檔案樹狀檢視 / Setup project tree view
        self.set_project_treeview()

        # 主分割器 (左：檔案樹，右：編輯器) / Main splitter (left: tree, right: editor)
        self.full_splitter = QSplitter()
        self.full_splitter.setOrientation(Qt.Orientation.Horizontal)

        # 編輯器分割器 (上：編輯器，下：輸出) / Editor splitter (top: editor, bottom: output)
        self.edit_splitter = QSplitter(self.full_splitter)
        self.edit_splitter.setOrientation(Qt.Orientation.Vertical)

        # 程式碼編輯器與輸出區 / Code editor and result area
        self.code_edit = CodeEditor(self)
        self.code_result = CodeRecord()
        self.code_result_cursor = self.code_result.textCursor()

        # 捲動區包裝編輯器與輸出 / Scroll areas for editor and result
        self.code_edit_scroll_area = QScrollArea()
        self.code_edit_scroll_area.setWidgetResizable(True)
        self.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_edit_scroll_area.setWidget(self.code_edit)

        self.code_result_scroll_area = QScrollArea()
        self.code_result_scroll_area.setWidgetResizable(True)
        self.code_result_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_result_scroll_area.setWidget(self.code_result)

        # 格式檢查與除錯輸出 / Format check and debugger output
        self.format_check_result = CodeRecord()
        self.debugger_result = CodeRecord()

        # 輸出分頁 (執行結果 / 格式檢查 / 除錯) / Output tabs
        self.code_difference_result = QTabWidget()
        self.code_difference_result.addTab(
            self.code_result_scroll_area, language_wrapper.language_word_dict.get("editor_code_result"))
        self.code_difference_result.addTab(
            self.format_check_result, language_wrapper.language_word_dict.get("editor_format_check"))
        self.code_difference_result.addTab(
            self.debugger_result, language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))

        # 加入分割器 / Add widgets to splitters
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

        # 設定字體樣式 / Set font style
        self.code_edit.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        self.code_result.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )

        # 加入主版面配置 / Add to main layout
        self.grid_layout.addWidget(self.full_splitter)

    # ---------------- Project Treeview ----------------
    def set_project_treeview(self) -> None:
        """
        建立並設定專案檔案樹狀檢視
        Setup and configure project file tree view
        """
        jeditor_logger.info("EditorWidget set_project_treeview")
        self.project_treeview_model = QFileSystemModel()
        self.project_treeview_model.setRootPath(QDir.currentPath())
        self.project_treeview = QTreeView()
        self.project_treeview.setModel(self.project_treeview_model)

        # 設定根目錄 (工作目錄或當前路徑) / Set root directory (working dir or current path)
        if self.main_window.working_dir is None:
            self.project_treeview.setRootIndex(
                self.project_treeview_model.index(str(Path.cwd()))
            )
        else:
            self.project_treeview.setRootIndex(
                self.project_treeview_model.index(self.main_window.working_dir)
            )

        # 包裝成可捲動區域 / Wrap in scroll area
        self.tree_view_scroll_area = QScrollArea()
        self.tree_view_scroll_area.setWidgetResizable(True)
        self.tree_view_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.tree_view_scroll_area.setWidget(self.project_treeview)
        self.grid_layout.addWidget(self.tree_view_scroll_area, 0, 0, 0, 1)

        # 點擊檔案時觸發 / Connect click event
        self.project_treeview.clicked.connect(self.treeview_click)

    def check_is_open(self, path: Path):
        """
        檢查檔案是否已經開啟，如果已開啟則切換到該分頁。
        Check if the file is already open, if yes then switch to that tab.
        """
        jeditor_logger.info(f"EditorWidget check_is_open path: {path}")
        if file_is_open_manager_dict.get(str(path), None) is not None:
            # 嘗試在分頁中找到對應的 EditorWidget
            # Try to find the corresponding EditorWidget in tab manager
            widget: QWidget = self.tab_manager.findChild(EditorWidget, str(path))
            if widget is None:
                # 如果找不到，代表之前的紀錄失效，移除紀錄
                # If not found, remove stale record
                file_is_open_manager_dict.pop(str(path), None)
            else:
                # 如果找到，直接切換到該分頁
                # If found, switch to that tab
                self.tab_manager.setCurrentWidget(widget)
                return False
        else:
            # 如果檔案未開啟，加入紀錄
            # If file not open, add to open manager dict
            file_is_open_manager_dict.update({str(path): str(path)})
            return True

    def open_an_file(self, path: Path) -> bool:
        """
        開啟檔案並載入到編輯器。
        Open a file and load it into the editor.

        :param path: 檔案路徑 / File path
        :return: 如果檔案已經開啟則回傳 False / Return False if file tab already exists
        """
        jeditor_logger.info(f"EditorWidget open_an_file path: {path}")
        if not self.check_is_open(path):
            return False

        # 如果有自動儲存執行緒，暫時跳過這一輪
        # If auto-save thread exists, skip this round
        if self.code_save_thread:
            self.code_save_thread.skip_this_round = True

        # 讀取檔案內容 / Read file content
        file, file_content = read_file(str(path))
        self.code_edit.setPlainText(file_content)

        # 更新目前檔案資訊 / Update current file info
        self.current_file = file
        self.code_edit.current_file = file
        self.code_edit.reset_highlighter()

        # 更新使用者設定中的最後開啟檔案 / Update last opened file in user settings
        user_setting_dict.update({"last_file": str(self.current_file)})

        # 啟動或更新自動儲存執行緒 / Start or update auto-save thread
        if self.current_file is not None and self.code_save_thread is None:
            init_new_auto_save_thread(self.current_file, self)
        else:
            self.code_save_thread.file = self.current_file
            self.code_save_thread.skip_this_round = False

        # 更新分頁標籤名稱 / Update tab title
        self.rename_self_tab()
        return True

    def treeview_click(self) -> None:
        """
        當使用者點擊檔案樹中的項目時觸發。
        Triggered when user clicks an item in the project tree view.
        """
        jeditor_logger.info("EditorWidget treeview_click")
        clicked_item: QFileSystemModel = self.project_treeview.selectedIndexes()[0]
        file_info: QFileInfo = self.project_treeview.model().fileInfo(clicked_item)
        path = pathlib.Path(file_info.absoluteFilePath())
        if path.is_file():
            self.open_an_file(path)

    def rename_self_tab(self):
        """
        將目前分頁的標籤名稱改為目前檔案名稱。
        Rename the current tab to the current file name.
        """
        jeditor_logger.info("EditorWidget rename_self_tab")
        if self.tab_manager.currentWidget() is self:
            self.tab_manager.setTabText(
                self.tab_manager.currentIndex(), str(Path(self.current_file)))
            self.setObjectName(str(Path(self.current_file)))

    def check_file_format(self):
        """
        檢查目前檔案的程式碼格式 (僅支援 Python)。
        Check the code format of the current file (only supports Python).
        """
        if self.current_file:
            jeditor_logger.info("EditorWidget check_file_format")
            suffix_checker = Path(self.current_file).suffix
            if suffix_checker == ".py":
                # 使用 PEP8 格式檢查器 / Use PEP8 format checker
                self.checker = PEP8FormatChecker(self.current_file)
                self.checker.check_all_format()
                self.format_check_result.setPlainText("")

                # 顯示錯誤訊息並套用顏色 / Display errors with color formatting
                for error in self.checker.error_list:
                    text_cursor = self.format_check_result.textCursor()
                    text_format = QTextCharFormat()
                    text_format.setForeground(actually_color_dict.get("error_output_color"))
                    text_cursor.insertText(error, text_format)
                    text_cursor.insertBlock()
                self.checker.error_list.clear()
            else:
                # 非 Python 檔案，顯示提示訊息 / Show message if not Python file
                message_box = QMessageBox()
                message_box.setText(
                    language_wrapper.language_word_dict.get("python_format_checker_only_support_python_message"))
                message_box.exec_()

    def close(self) -> bool:
        """
        關閉編輯器，釋放資源並移除自動儲存紀錄。
        Close the editor, release resources, and remove auto-save records.
        """
        jeditor_logger.info("EditorWidget close")
        if self.code_save_thread is not None:
            self.code_save_thread.still_run = False
            self.code_save_thread = None
        if self.current_file:
            file_is_open_manager_dict.pop(str(Path(self.current_file)), None)
            auto_save_manager_dict.pop(self.current_file, None)
        return super().close()
