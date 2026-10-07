"""
除錯相關的動作：開始除錯、接上程式、中斷點條件、標出執行到哪一行
The debugging actions: start, attach, breakpoint conditions, and marking where execution is.

選單、工具列與快捷鍵都呼叫這裡，這裡再去找視窗的 ``DebugController``。視窗沒有
控制器、或轉接器沒有登記時，每個函式都回傳 ``False``，呼叫端就知道要退回原本的
pdb 主控台。
Menus, the toolbar and shortcuts all call in here, and from here the window's
``DebugController`` is found. With no controller on the window, or no adapter
registered, every function returns ``False``, which tells the caller to fall
back to the pdb console.
"""
from __future__ import annotations

import shiboken6
from PySide6.QtWidgets import QInputDialog, QWidget

from je_editor.core.debug.debug_session import (
    Breakpoint, DebugAttachRequest, DebugLaunchRequest, DebugState
)
from je_editor.core.uri.resource_uri import to_uri
from je_editor.pyside_ui.main_ui.debug_panel.debug_controller import DebugController
from je_editor.pyside_ui.main_ui.debug_panel.debug_panel_widget import DebugPanelWidget
from je_editor.pyside_ui.main_ui.workspace.workspace_roots import primary_root_path
from je_editor.utils.debugger.attach_address import parse_address
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

DOCK_NAME = "debug_panel"
_PANEL_ATTRIBUTE = "debug_panel"


def controller_of(main_window: object) -> DebugController | None:
    """
    取得視窗的除錯控制
    The debugging control of a window.

    :param main_window: 主視窗 / the main window
    :return: 控制器；視窗沒有，或轉接器沒有登記時為 ``None``
        the controller, or ``None`` when the window has none or no adapter is registered
    """
    controller = getattr(main_window, "debug_controller", None)
    if isinstance(controller, DebugController) and controller.available():
        return controller
    return None


def _editors(main_window: object) -> list:
    """視窗裡每個編輯分頁的編輯器 / The editor of every editor tab in the window."""
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return []
    tabs = (tab_widget.widget(index) for index in range(tab_widget.count()))
    return [tab.code_edit for tab in tabs if isinstance(tab, EditorWidget)]


def collect_breakpoints(main_window: object) -> dict[str, list[Breakpoint]]:
    """
    收集每個開著的檔案的中斷點
    Collect the breakpoints of every open file.

    :param main_window: 主視窗 / the main window
    :return: 檔案的 URI 對應它的中斷點 / each file's URI and its breakpoints
    """
    found: dict[str, list[Breakpoint]] = {}
    for code_edit in _editors(main_window):
        breakpoints = code_edit.debug_breakpoints()
        if breakpoints:
            found[breakpoints[0].uri] = breakpoints
    return found


def start_debugging(main_window: object, file_path: str | None) -> bool:
    """
    以除錯轉接器開始除錯一個檔案
    Start debugging a file through the debug adapter.

    :param main_window: 主視窗 / the main window
    :param file_path: 要除錯的檔案 / the file to debug
    :return: 有啟動時為 ``True`` / ``True`` when it started
    """
    controller = controller_of(main_window)
    if controller is None or not file_path or controller.is_active():
        return False
    request = DebugLaunchRequest(
        str(file_path), working_directory=primary_root_path(main_window),
        interpreter=str(getattr(main_window, "python_compiler", None) or ""))
    show_debug_panel(main_window)
    return controller.launch(request, collect_breakpoints(main_window))


def attach_to_process(main_window: QWidget, address: str | None = None) -> bool:
    """
    接上一個等著除錯器的程式
    Attach to a program that waits for a debugger.

    :param main_window: 主視窗 / the main window
    :param address: ``host:port``；沒給時問使用者 / ``host:port``, asked for when omitted
    :return: 有連上時為 ``True`` / ``True`` when it connected
    """
    controller = controller_of(main_window)
    if controller is None or controller.is_active():
        return False
    words = language_wrapper.language_word_dict
    if address is None:
        address, accepted = QInputDialog.getText(
            main_window, words.get("debug_menu_attach"), words.get("debug_attach_prompt"))
        if not accepted:
            return False
    parsed = parse_address(address)
    if parsed is None:
        controller.output.emit("console", words.get("debug_attach_invalid") + "\n")
        show_debug_panel(main_window)
        return False
    show_debug_panel(main_window)
    return controller.attach(DebugAttachRequest(parsed[1], parsed[0]), collect_breakpoints(main_window))


def edit_breakpoint_condition(main_window: QWidget, condition: str | None = None) -> bool:
    """
    設定游標那一行中斷點的條件；那一行沒有中斷點時會加上
    Set the condition of the breakpoint on the caret's line, adding one when the line has none.

    :param main_window: 主視窗 / the main window
    :param condition: 條件，空字串表示一律停；沒給時問使用者
        the condition, empty to stop every time, asked for when omitted
    :return: 有設定時為 ``True`` / ``True`` when it was set
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

    tab_widget = getattr(main_window, "tab_widget", None)
    tab = tab_widget.currentWidget() if tab_widget is not None else None
    if not isinstance(tab, EditorWidget):
        return False
    code_edit = tab.code_edit
    line = code_edit.textCursor().blockNumber()
    if condition is None:
        words = language_wrapper.language_word_dict
        condition, accepted = QInputDialog.getText(
            main_window, words.get("debug_menu_breakpoint_condition"),
            words.get("debug_breakpoint_condition_prompt").format(line=line + 1),
            text=code_edit.breakpoint_manager.condition(line))
        if not accepted:
            return False
    code_edit.breakpoint_manager.set_condition(line, condition.strip())
    code_edit.line_number.update()
    code_edit.sync_debug_breakpoints()
    return True


def build_debug_panel(main_window: object) -> DebugPanelWidget:
    """
    建立除錯面板並接上視窗
    Build the debug panel and connect it to the window.

    :param main_window: 主視窗 / the main window
    :return: 新的面板 / the new panel
    """
    controller = getattr(main_window, "debug_controller", None)
    panel = DebugPanelWidget(controller)
    panel.frame_selected.connect(lambda path, line: show_execution_line(main_window, path, line))
    controller.state_changed.connect(
        lambda state: clear_execution_lines(main_window) if state is not DebugState.PAUSED else None)
    setattr(main_window, _PANEL_ATTRIBUTE, panel)
    return panel


def show_debug_panel(main_window: object) -> None:
    """
    顯示除錯面板，還沒有的話就開一個
    Show the debug panel, opening one when there is none.

    :param main_window: 主視窗 / the main window
    """
    from je_editor.pyside_ui.main_ui.menu.dock_menu.build_dock_menu import add_dock_widget

    panel = getattr(main_window, _PANEL_ATTRIBUTE, None)
    if isinstance(panel, DebugPanelWidget) and shiboken6.isValid(panel):
        dock = panel.parentWidget()
        if dock is not None:
            dock.show()
            dock.raise_()
        return
    add_dock_widget(main_window, DOCK_NAME)


def show_execution_line(main_window: object, path: str, line: int) -> bool:
    """
    開啟某個檔案並標出執行到的那一行
    Open a file and mark the line execution has reached.

    :param main_window: 主視窗 / the main window
    :param path: 檔案路徑，空字串表示那一層沒有原始碼 / the file path, empty when the frame has no source
    :param line: 1 起算的行號 / the 1-based line
    :return: 有標出來時為 ``True`` / ``True`` when a line was marked
    """
    clear_execution_lines(main_window)
    opener = getattr(main_window, "go_to_new_tab", None)
    if not path or not callable(opener):
        return False
    opener(path)
    wanted = to_uri(path)
    for code_edit in _editors(main_window):
        if code_edit.current_file and to_uri(str(code_edit.current_file)) == wanted:
            code_edit.set_execution_line(line)
            return True
    return False


def clear_execution_lines(main_window: object) -> None:
    """
    把每個編輯器裡「執行到這一行」的標記拿掉
    Remove the execution mark from every editor.

    :param main_window: 主視窗 / the main window
    """
    for code_edit in _editors(main_window):
        code_edit.set_execution_line(None)
