import time
from pathlib import Path
from threading import Thread, Event
from typing import Callable

from PySide6.QtCore import QObject, Qt, Signal, Slot

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.utils.encodings.text_codec import DEFAULT_ENCODING, LINE_ENDING_LF
from je_editor.utils.file.save.save_file import write_file_with_encoding
from je_editor.utils.logging.loggin_instance import jeditor_logger


class _TextFetcher(QObject):
    """
    輔助 QObject，在主執行緒中安全取得編輯器文字。
    Helper QObject that safely fetches editor text on the main thread.
    """
    text_fetched = Signal(str)
    fetch_requested = Signal()

    def __init__(self, editor: CodeEditor, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        self._pending_text: str | None = None
        self._ready = Event()
        self.fetch_requested.connect(self._do_fetch, type=Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _do_fetch(self) -> None:
        try:
            if self._editor is not None:
                self._pending_text = self._editor.toPlainText()
            else:
                self._pending_text = None
        except RuntimeError:
            self._pending_text = None
        finally:
            self._ready.set()

    def fetch(self) -> str | None:
        """從背景執行緒呼叫，安全取得文字 / Call from background thread to safely get text"""
        self._pending_text = None
        self._ready.clear()
        self.fetch_requested.emit()
        if not self._ready.wait(timeout=5):
            return None
        return self._pending_text


class CodeEditSaveThread(Thread):
    """
    This thread is used to auto save current file.
    這個執行緒用來自動儲存當前檔案。
    """

    def __init__(
            self, file_to_save: str | None = None, editor: CodeEditor | None = None,
            before_write_callback: Callable | None = None) -> None:
        jeditor_logger.info(f"Init CodeEditSaveThread "
                            f"file_to_save: {file_to_save} "
                            f"editor: {editor}")
        super().__init__()
        self.file: str = file_to_save
        self.editor: CodeEditor | None = editor
        self.still_run: bool = True
        self.daemon = True
        self.skip_this_round: bool = False
        self.before_write_callback = before_write_callback
        # 自動儲存要沿用該檔案原本的編碼與行尾，否則背景存檔會悄悄改寫整份檔案
        # Auto-save keeps the file's own encoding and line ending, or a background
        # save would quietly rewrite the whole file
        self.encoding: str = DEFAULT_ENCODING
        self.line_ending: str = LINE_ENDING_LF
        # 建立主執行緒上的文字提取器 / Create text fetcher on main thread
        self._text_fetcher: _TextFetcher | None = None
        if editor is not None:
            self._text_fetcher = _TextFetcher(editor)

    def _get_editor_text(self) -> str | None:
        """
        透過 Qt 主執行緒安全取得編輯器文字
        Safely get editor text via Qt main thread
        """
        if self._text_fetcher is None:
            return None
        try:
            return self._text_fetcher.fetch()
        except RuntimeError:
            return None

    def _attempt_save(self) -> None:
        """執行一次儲存動作；錯誤只記錄不中斷 / Run one save attempt; log errors instead of raising."""
        try:
            text = self._get_editor_text()
            if text is None:
                return
            if self.before_write_callback is not None:
                self.before_write_callback()
            write_file_with_encoding(self.file, text, self.encoding, self.line_ending)
        except (OSError, RuntimeError) as e:
            jeditor_logger.error(f"Auto-save failed for {self.file}: {e}")

    def run(self) -> None:
        """迴圈自動儲存當前編輯檔案 / Loop and save the current editor file periodically."""
        jeditor_logger.info("CodeEditSaveThread run")
        if self.file is None:
            return
        path = Path(self.file)
        while path.is_file() and self.editor is not None:
            time.sleep(5)
            if not self.still_run:
                break
            if self.skip_this_round:
                continue
            self._attempt_save()
