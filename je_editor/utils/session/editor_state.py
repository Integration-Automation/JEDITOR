"""
讀取與套用一個編輯分頁的游標、書籤與折疊狀態
Read and apply one editor tab's caret, bookmarks and folds.

工作階段還原原本只重新開檔，開起來的檔案永遠停在第一行、書籤與折疊全部消失。
Session restore used to only reopen files: every one came back at line one with
its bookmarks and folds gone.
"""
from __future__ import annotations

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.session.open_files_session import build_file_state


def editor_state(widget) -> dict:
    """
    取得一個編輯分頁目前的狀態
    Collect the current state of one editor tab.

    :param widget: 編輯分頁 / the editor tab
    :return: 可寫入設定的狀態 / the state, ready to store
    """
    code_edit = widget.code_edit
    return build_file_state(
        code_edit.textCursor().blockNumber(),
        list(code_edit.bookmark_manager.bookmarked_lines()),
        list(code_edit.folding_manager.folded_header_lines()),
    )


def restore_editor_state(widget, state: dict | None) -> bool:
    """
    把狀態套回一個編輯分頁
    Apply a stored state back onto an editor tab.

    還原是「盡力而為」：檔案在編輯器外被改短時，超出範圍的行號會被跳過，而不是
    讓整個還原失敗。
    Restoring is best-effort: if the file shrank outside the editor, lines beyond
    its end are skipped rather than failing the whole restore.

    :param widget: 編輯分頁，可為 ``None`` / the editor tab, may be ``None``
    :param state: 要套用的狀態，可為 ``None`` / the state to apply, may be ``None``
    :return: 有套用時為 ``True`` / ``True`` when the state was applied
    """
    if widget is None or not state:
        return False
    code_edit = getattr(widget, "code_edit", None)
    if code_edit is None:
        return False
    last_line = code_edit.blockCount() - 1
    try:
        for line in state.get("bookmarks", []):
            if line <= last_line:
                code_edit.bookmark_manager.toggle(line)
        for line in state.get("folds", []):
            if line <= last_line:
                code_edit.folding_manager.toggle_fold(line)
        caret = min(state.get("caret_line", 0), last_line)
        code_edit.jump_to_line(caret + 1)
    except (AttributeError, RuntimeError, ValueError) as error:
        jeditor_logger.warning(f"Restoring editor state failed: {error}")
        return False
    return True
