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

from PySide6.QtCore import Qt, QFileInfo, QDir, QFileSystemWatcher
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QWidget, QGridLayout, QSplitter, QScrollArea, QFileSystemModel, QTreeView, QTabWidget, \
    QMessageBox

from je_editor.pyside_ui.code.auto_save.auto_save_manager import auto_save_manager_dict, init_new_auto_save_thread, \
    file_is_open_manager_dict
from je_editor.pyside_ui.main_ui.console_widget.console_gui import ConsoleWidget
from je_editor.pyside_ui.code.variable_inspector.inspector_gui import VariableInspector
from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
from je_editor.pyside_ui.code.auto_save.auto_save_thread import CodeEditSaveThread
from je_editor.pyside_ui.code.code_format.pep8_format import PEP8FormatChecker
from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.code.split_view.split_editor_view import SplitEditorView
from je_editor.pyside_ui.code.textedit_code_result.code_record import CodeRecord
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.encodings.text_codec import (
    DEFAULT_ENCODING, LINE_ENDING_LF
)
from je_editor.utils.file.open.open_file import read_file, read_file_with_encoding


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

    def __init__(self, main_window: EditorMain) -> None:
        jeditor_logger.info(f"Init EditorWidget main_window: {main_window}")
        super().__init__()
        # 啟用拖放功能 / Enable drag and drop
        self.setAcceptDrops(True)
        # ---------------- Init variables 初始化變數 ----------------
        self.checker: Union[PEP8FormatChecker, None] = None
        self.current_file = None
        # 目前檔案的編碼與行尾，開檔時偵測，存檔時照原樣寫回
        # The current file's encoding and line ending, detected on open and
        # written back unchanged on save
        self.file_encoding: str = DEFAULT_ENCODING
        self.line_ending: str = LINE_ENDING_LF
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

        # 未儲存修改標記 / Track unsaved modifications
        self._is_modified = False

        # 檔案變更偵測 / File change detection
        self._file_watcher = QFileSystemWatcher(self)
        self._file_watcher.fileChanged.connect(self._on_file_changed_externally)
        self._ignore_next_change = False

        # 程式碼編輯器與輸出區 / Code editor and result area
        self.code_edit = CodeEditor(self)
        self.code_result = CodeRecord()

        # 監聽文字變更以標記未儲存狀態 / Track text changes for unsaved indicator
        self.code_edit.textChanged.connect(self._on_text_changed)
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

        # 終端機 / Terminal console
        self.console_widget = ConsoleWidget(self)

        # 變數查看器 / Variable inspector
        self.variable_inspector = VariableInspector()

        # Git 用戶端 / Git client
        self.git_gui = GitGui()

        # 輸出分頁 (執行結果 / 格式檢查 / 除錯 / 終端機 / 變數查看器 / Git) / Output tabs
        self.code_difference_result = QTabWidget()
        self.code_difference_result.addTab(
            self.code_result_scroll_area, language_wrapper.language_word_dict.get("editor_code_result"))
        self.code_difference_result.addTab(
            self.format_check_result, language_wrapper.language_word_dict.get("editor_format_check"))
        self.code_difference_result.addTab(
            self.debugger_result, language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))
        self.code_difference_result.addTab(
            self.console_widget, language_wrapper.language_word_dict.get("editor_terminal"))
        self.code_difference_result.addTab(
            self.variable_inspector, language_wrapper.language_word_dict.get("variable_inspector_title"))
        self.code_difference_result.addTab(
            self.git_gui, language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))

        # 加入分割器 / Add widgets to splitters
        self.edit_splitter.addWidget(self.code_edit_scroll_area)
        self.edit_splitter.addWidget(self.code_difference_result)
        self.edit_splitter.setStretchFactor(0, 3)
        self.edit_splitter.setStretchFactor(1, 1)
        self.edit_splitter.setSizes([300, 100])

        # 同檔分割檢視，開啟時才建立 / The same-file split view, created on demand
        self.split_view: Union[SplitEditorView, None] = None

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

    def check_is_open(self, path: Path) -> bool:
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

        # 讀取檔案內容，同時記下編碼與行尾，存檔時照原樣寫回
        # Read the content, remembering the encoding and line ending so a save
        # writes the file back the way it was found
        result = read_file_with_encoding(str(path))
        if result is None:
            return False
        file, file_content, self.file_encoding, self.line_ending = result
        self.code_edit.setPlainText(file_content)

        # 依內容偵測縮排寬度；失敗不可影響開檔 / Detect indent; must not break opening
        try:
            self.code_edit.apply_detected_indentation()
        except Exception as detect_error:
            jeditor_logger.warning(f"Indent detection failed: {detect_error}")

        # 更新目前檔案資訊 / Update current file info
        self.current_file = file
        self.code_edit.current_file = file
        self.code_edit.reset_highlighter()
        # 換檔後重新取得 git 比較基準 / Reload the git baseline for the new file
        self.code_edit.load_git_baseline()

        # 更新使用者設定中的最後開啟檔案 / Update last opened file in user settings
        user_setting_dict.update({"last_file": str(self.current_file)})

        # 啟動或更新自動儲存執行緒 / Start or update auto-save thread
        if self.current_file is not None and self.code_save_thread is None:
            init_new_auto_save_thread(self.current_file, self)
        elif self.code_save_thread is not None:
            self.code_save_thread.file = self.current_file
            self.code_save_thread.skip_this_round = False

        # 更新檔案監控 / Update file watcher
        watched = self._file_watcher.files()
        if watched:
            self._file_watcher.removePaths(watched)
        self._file_watcher.addPath(str(path))

        # 更新分頁標籤名稱 / Update tab title
        self.rename_self_tab()
        return True

    def treeview_click(self) -> None:
        """
        當使用者點擊檔案樹中的項目時觸發。
        Triggered when user clicks an item in the project tree view.
        """
        jeditor_logger.info("EditorWidget treeview_click")
        indexes = self.project_treeview.selectedIndexes()
        if not indexes:
            return
        clicked_item: QFileSystemModel = indexes[0]
        file_info: QFileInfo = self.project_treeview.model().fileInfo(clicked_item)
        path = pathlib.Path(file_info.absoluteFilePath())
        if path.is_file():
            self.open_an_file(path)

    def _on_text_changed(self) -> None:
        """
        文字變更時標記為未儲存，並在 tab 標題加上 *
        Mark as modified when text changes, add * to tab title
        """
        if not self._is_modified:
            self._is_modified = True
            idx = self.tab_manager.indexOf(self)
            if idx >= 0:
                title = self.tab_manager.tabText(idx)
                if not title.endswith(" *"):
                    self.tab_manager.setTabText(idx, title + " *")

    def mark_saved(self) -> None:
        """
        儲存後清除未儲存標記
        Clear the unsaved marker after saving
        """
        self._is_modified = False
        idx = self.tab_manager.indexOf(self)
        if idx >= 0:
            title = self.tab_manager.tabText(idx)
            if title.endswith(" *"):
                self.tab_manager.setTabText(idx, title[:-2])

    def toggle_split_view(self) -> bool:
        """
        切換同檔分割檢視
        Toggle the split view of the same file.

        兩個檢視共用同一份文件，因此任一邊的編輯會立刻出現在另一邊，而捲動與游標
        各自獨立。
        Both views share one document, so an edit in either appears in the other
        at once, while scrolling and the caret stay independent.

        :return: 切換後是否為開啟 / whether the split view is now shown
        """
        if self.split_view is not None:
            self.split_view.close()
            self.split_view.setParent(None)
            self.split_view.deleteLater()
            self.split_view = None
            return False
        self.split_view = SplitEditorView(self.code_edit)
        # 插在主編輯器下方、輸出區上方 / Below the main editor, above the output
        self.edit_splitter.insertWidget(1, self.split_view)
        self.edit_splitter.setSizes([200, 200, 100])
        return True

    def rename_self_tab(self) -> None:
        """
        將分頁的標籤名稱改為目前檔案名稱 (不限當前分頁)。
        Rename this tab to the current file name (works for any tab, not just current).
        """
        jeditor_logger.info("EditorWidget rename_self_tab")
        idx = self.tab_manager.indexOf(self)
        if idx >= 0 and self.current_file is not None:
            self.tab_manager.setTabText(idx, str(Path(self.current_file)))
            self.setObjectName(str(Path(self.current_file)))
            self._is_modified = False

    def check_file_format(self) -> None:
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
                message_box = QMessageBox(self)
                message_box.setText(
                    language_wrapper.language_word_dict.get("python_format_checker_only_support_python_message"))
                message_box.exec_()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        接受包含檔案 URL 的拖放事件
        Accept drag events containing file URLs
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        拖放檔案時開啟檔案
        Open files when dropped
        """
        for url in event.mimeData().urls():
            file_path = Path(url.toLocalFile())
            if file_path.is_file():
                self.open_an_file(file_path)
        event.acceptProposedAction()

    def mark_ignore_next_file_change(self) -> None:
        """
        標記下一次檔案變更事件應被忽略（由自動儲存呼叫）
        Mark the next file change event to be ignored (called by auto-save before writing)
        """
        self._ignore_next_change = True

    def _on_file_changed_externally(self, path: str) -> None:
        """
        檔案被外部修改時提示使用者
        Prompt user when file is modified externally
        """
        if self._ignore_next_change:
            self._ignore_next_change = False
            # 重新加入監控（某些系統會在寫入後移除監控）
            if path not in self._file_watcher.files():
                self._file_watcher.addPath(path)
            return

        file_path = Path(path)
        if not file_path.exists():
            return

        reply = QMessageBox.question(
            self,
            language_wrapper.language_word_dict.get("file_changed_externally_title"),
            language_wrapper.language_word_dict.get("file_changed_externally_message").format(file=file_path.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            result = read_file(str(file_path))
            if result is not None:
                self._ignore_next_change = True
                self.code_edit.setPlainText(result[1])
                self._is_modified = False
                idx = self.tab_manager.indexOf(self)
                if idx >= 0:
                    title = self.tab_manager.tabText(idx)
                    if title.endswith(" *"):
                        self.tab_manager.setTabText(idx, title[:-2])

        # 重新加入監控 / Re-add to watcher
        if path not in self._file_watcher.files():
            self._file_watcher.addPath(path)

    def close(self) -> bool:
        """
        關閉編輯器，釋放資源並移除自動儲存紀錄。
        Close the editor, release resources, and remove auto-save records.
        """
        jeditor_logger.info("EditorWidget close")

        # 先移除檔案監控，防止關閉後仍觸發變更對話框
        # Remove file watcher first to prevent change dialogs after close
        watched = self._file_watcher.files()
        if watched:
            self._file_watcher.removePaths(watched)

        # 停止自動儲存執行緒 / Stop auto-save thread
        if self.code_save_thread is not None:
            self.code_save_thread.still_run = False
            self.code_save_thread = None

        # 關閉內嵌終端機的互動式 shell / Shut down the embedded console's interactive shell
        if self.console_widget is not None:
            self.console_widget.close()

        # 停止所有正在執行的子程序 / Stop all running subprocesses
        for mgr in (self.exec_program, self.exec_shell, self.exec_python_debugger):
            if mgr is not None:
                if mgr.timer is not None:
                    mgr.timer.stop()
                mgr.exit_program()
        self.exec_program = None
        self.exec_shell = None
        self.exec_python_debugger = None

        # 停止仍在執行的背景檢查 / Stop background checks still running
        self.code_edit.diff_marker_manager.stop()
        self.code_edit.lint_manager.stop()
        self.code_edit.blame_manager.stop()

        if self.current_file:
            file_is_open_manager_dict.pop(str(Path(self.current_file)), None)
            auto_save_manager_dict.pop(self.current_file, None)
        return super().close()
