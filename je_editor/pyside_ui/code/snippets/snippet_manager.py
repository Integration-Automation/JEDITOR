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

from PySide6.QtCore import QObject
from PySide6.QtGui import QTextCursor

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.snippets.snippet_expand import (
    SnippetStop, expand_snippet, merge_snippets, positions_after_mirroring, shift_mirrors
)

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


def save_snippets(snippets: dict[str, str], path: Path | None = None) -> bool:
    """
    把片段寫回使用者的片段檔
    Write the snippets back to the user's snippet file.

    :param snippets: 要儲存的片段 / the snippets to store
    :param path: 片段檔路徑，``None`` 表示預設位置 / the file, or ``None`` for the default
    :return: 寫入成功時為 ``True`` / ``True`` when the file was written
    """
    target = path if path is not None else snippet_file_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(snippets, indent=4, ensure_ascii=False), encoding="utf-8")
    except OSError as error:
        jeditor_logger.error(f"snippet_manager: could not save snippets: {error!r}")
        return False
    return True


def load_snippets(path: Path | None = None, suffix: str = "") -> dict[str, str]:
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
        return merge_snippets(None, suffix)
    return merge_snippets(stored, suffix)


class SnippetManager(QObject):
    """
    管理一個編輯器的片段展開狀態
    Track one editor's snippet expansion.

    是編輯器的 QObject 子物件：要監看文件的變更訊號，接收者必須是 QObject，編輯器
    被銷毀時 Qt 才會自動斷開。
    A QObject child of the editor: watching the document's change signal needs a
    receiver Qt can disconnect when the editor goes away.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 要展開片段的編輯器 / the editor snippets expand into
        """
        super().__init__(code_edit)
        self._code_edit = code_edit
        self._snippets = load_snippets(suffix=self._suffix())
        # 尚未走訪的定位點（文件中的絕對位置）/ Stops not yet visited, as document positions
        self._pending: list[SnippetStop] = []
        # 目前定位點與它的複本；記成位置與長度而不是 QTextCursor，因為整段內容被
        # 取代時游標的選取範圍會塌掉，而使用者輸入第一個字就正是在取代整段預設值
        # The current stop and its mirrors, kept as positions and a length rather
        # than cursors: a cursor's selection collapses when its whole content is
        # replaced, which is exactly what the first keystroke over a default does
        self._stop_start = 0
        self._stop_length = 0
        self._mirror_starts: list[int] = []
        # 每個複本目前的長度；改寫後才會變 / Each mirror's current length
        self._mirror_length = 0
        # 自己在改複本時不要再處理一次變更 / Ignore the changes this makes itself
        self._mirroring = False
        code_edit.document().contentsChange.connect(self._on_contents_change)

    def snippets(self) -> dict[str, str]:
        """取得目前可用的片段 / The snippets currently available."""
        return dict(self._snippets)

    def _suffix(self) -> str:
        """目前檔案的副檔名 / The current file's suffix."""
        current = getattr(self._code_edit, "current_file", None)
        return Path(str(current)).suffix if current else ""

    def reload(self, path: Path | None = None) -> None:
        """
        重新載入使用者片段，並套用目前檔案的語言
        Reload the user's snippets, for the current file's language.

        :param path: 片段檔路徑，``None`` 表示預設位置 / the file, or ``None`` for the default
        """
        self._snippets = load_snippets(path, self._suffix())

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
        # 展開得到的是片段內的相對位置，這裡換算成文件中的絕對位置
        # Expansion gives offsets inside the snippet; these are document positions
        self._pending = [
            SnippetStop(
                position=start + stop.position,
                length=stop.length,
                mirrors=tuple(start + mirror for mirror in stop.mirrors))
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
        cursor.setPosition(self._clamp(stop.position))
        if stop.length:
            cursor.setPosition(
                self._clamp(stop.position + stop.length),
                QTextCursor.MoveMode.KeepAnchor)
        self._code_edit.setTextCursor(cursor)
        self._track_mirrors(stop)
        return True

    def _clamp(self, position: int) -> int:
        """把位置限制在文件範圍內 / Keep a position inside the document."""
        return max(0, min(position, self._code_edit.document().characterCount() - 1))

    def _track_mirrors(self, stop: SnippetStop) -> None:
        """
        記住這個定位點與它的複本，準備讓它們一起改
        Remember this stop and its mirrors so they can be kept in step.

        :param stop: 剛跳到的定位點 / the stop just moved to
        """
        self._stop_start = stop.position
        self._stop_length = stop.length
        self._mirror_length = stop.length
        self._mirror_starts = sorted(stop.mirrors)

    def _on_contents_change(self, position: int, removed: int, added: int) -> None:
        """
        文件變更時把目前定位點的內容複製到每個複本
        Copy the current stop's text into each mirror whenever the document changes.

        同一個編號在片段裡出現好幾次時，使用者只編輯第一個，其餘要跟著變；否則
        ``${1:name}`` 用兩次就得手動改兩遍。
        Where a number appears several times in a snippet the user only edits the
        first, and the rest have to follow; otherwise using ``${1:name}`` twice
        means typing the same thing twice.
        """
        if self._mirroring or not self._mirror_starts:
            return
        if not self._stop_start <= position <= self._stop_start + self._stop_length:
            # 在別處輸入代表使用者已經離開這個定位點，複本不該再跟著動
            # Typing elsewhere means the user has moved on, and the mirrors with them
            return
        delta = added - removed
        self._stop_length = max(0, self._stop_length + delta)
        self._mirror_starts = shift_mirrors(self._mirror_starts, position, delta)
        self._write_mirrors()

    def _write_mirrors(self) -> None:
        """
        把定位點目前的內容寫進每個複本
        Write the stop's current text into every mirror.

        由後往前改寫，前面的位置才不會因為後面的改寫而失效；改完再算出各自的新位置。
        The rewrite runs back to front so an earlier position is not invalidated by
        a later one, and the new positions are worked out afterwards.
        """
        text = self._text_between(self._stop_start, self._stop_start + self._stop_length)
        old_length = self._mirror_length
        cursor = QTextCursor(self._code_edit.document())
        self._mirroring = True
        try:
            cursor.beginEditBlock()
            for start in sorted(self._mirror_starts, reverse=True):
                cursor.setPosition(self._clamp(start))
                cursor.setPosition(self._clamp(start + old_length),
                                   QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(text)
            cursor.endEditBlock()
        finally:
            self._mirroring = False
        self._stop_start, self._mirror_starts = positions_after_mirroring(
            self._stop_start, self._mirror_starts, len(text) - old_length)
        self._mirror_length = len(text)

    def _text_between(self, start: int, end: int) -> str:
        """取得文件中一段範圍的文字 / The document text between two positions."""
        cursor = QTextCursor(self._code_edit.document())
        cursor.setPosition(self._clamp(start))
        cursor.setPosition(self._clamp(end), QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()

    def clear_stops(self) -> None:
        """放棄剩下的定位點 / Give up on the remaining stops."""
        self._pending = []
        self._mirror_starts = []
