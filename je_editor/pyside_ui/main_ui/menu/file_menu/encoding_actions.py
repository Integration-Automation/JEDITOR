"""
套用編碼與行尾設定到目前的編輯分頁
Apply an encoding or line-ending choice to the current editor tab.

編碼選單原本只把選擇存進設定檔，讀寫檔案時並沒有用到；這裡讓它真的生效。
The encoding menu used to only record the choice in the settings without it
reaching the read or write path; this makes the choice take effect.
"""
from __future__ import annotations

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
