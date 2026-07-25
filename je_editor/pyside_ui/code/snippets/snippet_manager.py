"""
在編輯器中展開片段並在定位點之間移動
Expand snippets in the editor and step between their tab stops.

輸入觸發字後按 Tab 展開；展開後 Tab 會依序跳到下一個定位點，走完就恢復成一般的
Tab 縮排。
Type a trigger word and press Tab to expand it. After expanding, Tab moves to the
next stop, and once they are used up Tab goes back to indenting.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QTextCursor

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.snippets.snippet_expand import SnippetStop, expand_snippet, merge_snippets

# 使用者片段檔名（放在設定資料夾內）/ The user snippet file, kept beside the settings
SNIPPET_FILE_NAME = "snippets.json"
# 設定資料夾 / The settings directory
SETTING_DIR_NAME = ".jeditor"


def snippet_file_path() -> Path:
    """
    使用者片段檔的位置
    Where the user's snippet file lives.

    :return: 片段檔路徑 / the snippet file's path
    """
    return Path.cwd() / SETTING_DIR_NAME / SNIPPET_FILE_NAME


def load_snippets(path: Path | None = None) -> dict[str, str]:
    """
    載入片段：內建的加上使用者定義的
    Load the snippets: the built-in set plus anything the user defined.

    檔案不存在、不是 JSON、或內容不是物件時只回傳內建片段，因為片段損毀不該讓
    編輯器無法輸入。
    A missing file, invalid JSON, or a non-object all fall back to the built-in
    set: a broken snippet file must not stop the user typing.

    :param path: 片段檔路徑，``None`` 表示預設位置 / the file, or ``None`` for the default
    :return: 觸發字對應片段內容 / trigger word -> snippet body
    """
    target = path if path is not None else snippet_file_path()
    try:
        stored = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        jeditor_logger.debug(f"snippet_manager: using built-in snippets only: {error!r}")
        return merge_snippets(None)
    return merge_snippets(stored)


class SnippetManager:
    """
    管理一個編輯器的片段展開狀態
    Track one editor's snippet expansion.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 要展開片段的編輯器 / the editor snippets expand into
        """
        self._code_edit = code_edit
        self._snippets = load_snippets()
        # 尚未走訪的定位點（文件中的絕對位置）/ Stops not yet visited, as document positions
        self._pending: list[SnippetStop] = []

    def snippets(self) -> dict[str, str]:
        """取得目前可用的片段 / The snippets currently available."""
        return dict(self._snippets)

    def reload(self, path: Path | None = None) -> None:
        """
        重新載入使用者片段
        Reload the user's snippets from disk.

        :param path: 片段檔路徑，``None`` 表示預設位置 / the file, or ``None`` for the default
        """
        self._snippets = load_snippets(path)

    @property
    def has_pending_stops(self) -> bool:
        """是否還有沒走訪的定位點 / Whether any tab stop is still waiting."""
        return bool(self._pending)

    def trigger_word(self) -> str:
        """
        取得游標前的觸發字
        The trigger word immediately before the caret.

        :return: 觸發字，取不到時為空字串 / the word, or an empty string
        """
        cursor = self._code_edit.textCursor()
        if cursor.hasSelection():
            return ""
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def expand_at_cursor(self) -> bool:
        """
        若游標前是觸發字就展開對應片段
        Expand the snippet for the trigger word before the caret, if there is one.

        展開是單一復原步驟，因此一次 Ctrl+Z 就能取消整個片段。
        The expansion is one undo step, so a single Ctrl+Z removes the whole
        snippet.

        :return: 有展開時為 ``True`` / ``True`` when a snippet was expanded
        """
        word = self.trigger_word()
        body = self._snippets.get(word)
        if not body:
            return False
        text, stops = expand_snippet(body)
        cursor = self._code_edit.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        start = cursor.selectionStart()
        cursor.insertText(text)
        cursor.endEditBlock()
        self._pending = [
            SnippetStop(position=start + stop.position, length=stop.length)
            for stop in stops
        ]
        self.next_stop()
        return True

    def next_stop(self) -> bool:
        """
        移到下一個定位點，並選取它的預設值
        Move to the next tab stop, selecting its default value.

        :return: 有移動時為 ``True`` / ``True`` when the caret moved
        """
        if not self._pending:
            return False
        stop = self._pending.pop(0)
        cursor = self._code_edit.textCursor()
        cursor.setPosition(min(stop.position, self._code_edit.document().characterCount() - 1))
        if stop.length:
            cursor.setPosition(
                min(stop.position + stop.length,
                    self._code_edit.document().characterCount() - 1),
                QTextCursor.MoveMode.KeepAnchor)
        self._code_edit.setTextCursor(cursor)
        return True

    def clear_stops(self) -> None:
        """放棄剩下的定位點 / Give up on the remaining stops."""
        self._pending = []
