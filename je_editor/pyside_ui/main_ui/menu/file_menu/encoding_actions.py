"""
套用編碼與行尾設定到目前的編輯分頁
Apply an encoding or line-ending choice to the current editor tab.

編碼選單原本只把選擇存進設定檔，讀寫檔案時並沒有用到；這裡讓它真的生效。
The encoding menu used to only record the choice in the settings without it
reaching the read or write path; this makes the choice take effect.
"""
from __future__ import annotations

from pathlib import Path

from je_editor.utils.encodings.text_codec import LINE_ENDING_LF
from je_editor.utils.exception.exceptions import JEditorOpenFileException
from je_editor.utils.file.open.open_file import read_file_with_encoding
from je_editor.utils.logging.loggin_instance import jeditor_logger


def current_editor_tab(ui_we_want_to_set):
    """
    取得目前的編輯分頁
    Return the current editor tab.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 編輯分頁，目前分頁不是編輯器時為 ``None`` / the editor tab, or ``None``
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return None
    widget = tab_widget.currentWidget()
    return widget if isinstance(widget, EditorWidget) else None


def _update_auto_save(widget) -> None:
    """讓自動儲存沿用同樣的編碼與行尾 / Keep auto-save on the same encoding and ending."""
    thread = getattr(widget, "code_save_thread", None)
    if thread is not None:
        thread.encoding = widget.file_encoding
        thread.line_ending = widget.line_ending


def apply_encoding(ui_we_want_to_set, encoding: str) -> bool:
    """
    以指定編碼重新解讀目前檔案，並用它存檔
    Re-read the current file with *encoding*, and save with it from now on.

    只有在沒有未儲存修改時才重新讀取，否則改個編碼就會把使用者正在編輯的內容
    丟掉；有修改時仍會改用新編碼存檔。
    The file is only re-read when nothing is unsaved, since re-reading would
    otherwise throw away what the user is editing; the new encoding still
    applies to the next save either way.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :param encoding: 要使用的編碼 / the encoding to use
    :return: 有套用到某個分頁時為 ``True`` / ``True`` when a tab was updated
    """
    widget = current_editor_tab(ui_we_want_to_set)
    if widget is None:
        return False
    widget.file_encoding = encoding
    _update_auto_save(widget)
    if widget.current_file is None or getattr(widget, "_is_modified", False):
        return True
    try:
        result = read_file_with_encoding(str(widget.current_file), encoding)
    except JEditorOpenFileException:
        # 這個編碼解不開這個檔案：保留畫面上的內容，讓使用者再選一次
        # The file does not decode as that encoding: leave the text alone so the
        # user can simply choose another
        jeditor_logger.info(f"encoding_actions: {encoding} cannot decode {widget.current_file}")
        return True
    if result is not None:
        _path, content, used_encoding, line_ending = result
        widget.code_edit.setPlainText(content)
        widget.file_encoding = used_encoding
        widget.line_ending = line_ending
        _update_auto_save(widget)
    return True


def format_before_save(widget) -> bool:
    """
    存檔前套用格式化（若已開啟該設定）
    Format the buffer before saving, when the setting is on.

    只格式化 Python 檔；格式化失敗（例如程式碼還沒寫完）時保持原內容。
    Only Python files are formatted, and source that cannot be formatted — half
    -written code, say — is left exactly as it is.

    :param widget: 要格式化的編輯分頁 / the editor tab to format
    :return: 內容有被改寫時為 ``True`` / ``True`` when the text was rewritten
    """
    from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
    from je_editor.utils.format_code.yapf_format import format_python_source
    if not user_setting_dict.get("format_on_save", False):
        return False
    file_path = getattr(widget, "current_file", None)
    if file_path is None or Path(str(file_path)).suffix.lower() != ".py":
        return False
    source = widget.code_edit.toPlainText()
    formatted = format_python_source(source)
    if formatted == source:
        return False
    # 保留游標所在行，格式化後才不會跳到檔頭
    # Keep the caret's line so formatting does not throw it back to the top
    cursor = widget.code_edit.textCursor()
    line = cursor.blockNumber()
    widget.code_edit.setPlainText(formatted)
    widget.code_edit.jump_to_line(line + 1)
    return True


def save_all_tabs(ui_we_want_to_set) -> int:
    """
    儲存每個有未存修改的編輯分頁
    Save every editor tab that has unsaved changes.

    只存已經有檔名的分頁；沒有檔名的需要「另存新檔」對話框，不能默默決定位置。
    Only tabs that already have a file name are saved: one without needs the
    Save As dialog, and its location must not be decided silently.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 實際存檔的分頁數 / how many tabs were written
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from je_editor.utils.encodings.text_codec import DEFAULT_ENCODING
    from je_editor.utils.file.save.save_file import write_file_with_encoding
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return 0
    saved = 0
    for index in range(tab_widget.count()):
        widget = tab_widget.widget(index)
        if not isinstance(widget, EditorWidget) or not widget.current_file:
            continue
        format_before_save(widget)
        write_file_with_encoding(
            str(widget.current_file), widget.code_edit.toPlainText(),
            getattr(widget, "file_encoding", DEFAULT_ENCODING),
            getattr(widget, "line_ending", LINE_ENDING_LF))
        saved += 1
    return saved


def apply_line_ending_choice(ui_we_want_to_set, line_ending: str = LINE_ENDING_LF) -> bool:
    """
    設定目前檔案存檔時使用的行尾
    Set the line ending the current file is saved with.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :param line_ending: 要使用的行尾 / the line ending to write
    :return: 有套用到某個分頁時為 ``True`` / ``True`` when a tab was updated
    """
    widget = current_editor_tab(ui_we_want_to_set)
    if widget is None:
        return False
    widget.line_ending = line_ending
    _update_auto_save(widget)
    return True
