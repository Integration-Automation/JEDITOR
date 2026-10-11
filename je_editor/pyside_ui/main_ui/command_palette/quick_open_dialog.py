"""
快速開啟：以模糊搜尋在專案中找到並開啟檔案
Quick open: fuzzy-search the project tree and open a file.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import (
    CommandPaletteDialog
)
from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry
from je_editor.pyside_ui.main_ui.workspace.workspace_roots import (
    labelled_root_paths, primary_root_path
)
from je_editor.utils.file_scan.file_indexer import build_file_entries
from je_editor.utils.file_scan.workspace_scan import (
    FoundFile, LabelledRoot, as_labelled_roots, index_workspace_files
)
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 切換成指令模式的前綴，與 VS Code 的 Ctrl+P 行為一致
# Prefix that switches to command mode, matching VS Code's Ctrl+P behaviour
COMMAND_MODE_PREFIX = ">"


class FileIndexThread(QThread):
    """
    背景索引專案檔案，避免大型專案在走訪時卡住 UI
    Index project files in the background so a large tree never blocks the UI.
    """

    indexed = Signal(list)  # list[str] of the paths to show

    def __init__(self, root: str | list[LabelledRoot]) -> None:
        """
        :param root: 要索引的專案根目錄；工作區有好幾個根目錄時是「顯示名稱與路徑」的清單
            / The project root to index, or each root's label and path when the
            workspace has several
        """
        super().__init__()
        # 具名執行緒：萬一它在執行中被銷毀，Qt 的中止訊息才說得出是哪一條
        # A named thread, so Qt's abort message says which one if it is ever
        # destroyed while still running
        self.setObjectName("FileIndexThread")
        self._roots = as_labelled_roots(root)
        self._stop_requested = False
        # 索引結果，含開檔用的完整路徑；在送出 indexed 之前就填好
        # What the index found, full paths included; filled before indexed is emitted
        self.found: list[FoundFile] = []

    def stop(self) -> None:
        """要求提前結束索引 / Ask the walk to finish early."""
        self._stop_requested = True

    def run(self) -> None:
        """執行索引並送出結果 / Run the index and emit the result."""
        try:
            found = index_workspace_files(
                self._roots, should_stop=lambda: self._stop_requested)
        except OSError as error:
            jeditor_logger.error(f"quick_open_dialog.py index failed: {error!r}")
            found = []
        self.found = found
        self.indexed.emit([item.display_path for item in found])


class QuickOpenDialog(CommandPaletteDialog):
    """
    快速開啟對話框
    The quick open dialog.

    索引在背景進行，完成後結果會直接補進清單；輸入 ``>`` 可切換到指令模式。
    Indexing runs in the background and streams into the list when done; typing
    ``>`` switches the picker into command mode.
    """

    # 類別層級預設值：基底類別的 __init__ 會先呼叫 _refresh_results，
    # 那時子類別的實例屬性還不存在。使用不可變的空 tuple 避免共用可變狀態。
    # Class-level defaults: the base __init__ calls _refresh_results before the
    # subclass attributes exist. Immutable empty tuples avoid shared mutable state.
    _in_command_mode = False
    _file_entries: tuple = ()
    _command_entries: tuple = ()

    def __init__(
            self, parent, root: str | list[LabelledRoot], command_entries: list[CommandEntry],
            main_window=None) -> None:
        """
        :param parent: Qt 父視窗 / The Qt parent widget
        :param root: 專案根目錄，或每個根目錄的顯示名稱與路徑
            / The project root being indexed, or each root's label and path
        :param command_entries: 指令模式使用的選單指令 / Menu commands for command mode
        :param main_window: 用來開檔的主視窗，``None`` 時沿用 ``parent``
            / The window used to open files; ``None`` reuses ``parent``
        """
        word = language_wrapper.language_word_dict
        super().__init__(
            parent, [],
            title=word.get("quick_open_title"),
            placeholder=word.get("quick_open_placeholder"),
        )
        self._main_window = main_window if main_window is not None else parent
        self._file_entries = []
        self._command_entries = command_entries
        self._in_command_mode = False

        self._index_thread = FileIndexThread(root)
        self._index_thread.indexed.connect(self._on_indexed)
        self._index_thread.start()

    def _on_indexed(self, relative_paths: list) -> None:
        """索引完成後建立項目並套用 / Build entries once indexing finishes."""
        jeditor_logger.info(f"quick_open_dialog.py indexed {len(relative_paths)} files")
        entries = build_file_entries(relative_paths)
        full_paths = {item.display_path: item.full_path for item in self._index_thread.found}
        for entry in entries:
            entry.payload = make_file_opener(self._main_window, Path(full_paths[entry.path]))
        self._file_entries = entries
        if not self._in_command_mode:
            self.set_commands(entries)

    def _refresh_results(self, query: str) -> None:
        """
        依查詢字串切換檔案 / 指令模式後再過濾
        Switch between file and command mode, then filter.
        """
        wants_command_mode = query.startswith(COMMAND_MODE_PREFIX)
        if wants_command_mode != self._in_command_mode:
            self._in_command_mode = wants_command_mode
        self._commands = list(
            self._command_entries if wants_command_mode else self._file_entries)
        if wants_command_mode:
            query = query[len(COMMAND_MODE_PREFIX):]
        super()._refresh_results(query)

    def closeEvent(self, event) -> None:
        """
        關閉前停掉索引執行緒
        Stop the index thread before the dialog goes away.

        先擋掉信號再等待，避免執行緒在物件已銷毀後才送出結果。
        Signals are blocked before waiting so a late result cannot reach a dead
        widget, and waiting keeps the QThread from being destroyed while running.
        """
        thread = getattr(self, "_index_thread", None)
        if thread is not None and thread.isRunning():
            thread.blockSignals(True)
            thread.stop()
            thread.wait()
        super().closeEvent(event)


def make_file_opener(main_window, full_path: Path):
    """
    建立開啟指定檔案的觸發函式
    Build a trigger that opens one file in a new editor tab.

    刻意在模組層級建立閉包，只捕捉主視窗與路徑而不捕捉對話框；
    對話框設定了 ``WA_DeleteOnClose``，觸發時它已經被銷毀。
    The closure lives at module level and captures only the window and path, never
    the dialog: the dialog sets ``WA_DeleteOnClose`` and is already gone when the
    trigger fires.

    :param main_window: 用來開檔的主視窗 / The window used to open the file
    :param full_path: 要開啟的完整路徑 / The absolute path to open
    :return: 可直接呼叫的觸發函式 / A callable trigger
    """

    def open_file() -> None:
        if main_window is not None and hasattr(main_window, "go_to_new_tab"):
            main_window.go_to_new_tab(full_path)

    return open_file


def resolve_project_root(main_window: EditorMain) -> str:
    """
    取得要索引的專案根目錄
    Resolve the project root that should be indexed.

    以主視窗的工作目錄為主，未設定時退回目前的工作目錄。
    Prefers the main window's working directory, falling back to the process cwd.

    :param main_window: 主編輯器視窗 / The main editor window
    :return: 專案根目錄路徑 / The project root path
    """
    return primary_root_path(main_window)


def open_quick_open(main_window: EditorMain) -> QuickOpenDialog:
    """
    建立並顯示快速開啟面板
    Build and show the quick open picker.

    :param main_window: 主編輯器視窗 / The main editor window
    :return: 已顯示的對話框 / The shown dialog
    """
    from je_editor.pyside_ui.main_ui.command_palette.menu_command_collector import (
        collect_menu_commands
    )
    roots = labelled_root_paths(main_window)
    jeditor_logger.info(f"quick_open_dialog.py open_quick_open roots: {roots}")
    dialog = QuickOpenDialog(
        main_window, roots, collect_menu_commands(getattr(main_window, "menu", None)))
    dialog.show()
    return dialog
