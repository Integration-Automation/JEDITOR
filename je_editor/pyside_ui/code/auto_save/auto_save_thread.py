import time
from pathlib import Path
from threading import Thread, Event
from typing import Callable, Union

from PySide6.QtCore import QObject, Qt, Signal, Slot

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.utils.file.save.save_file import write_file
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
        self._pending_text: Union[str, None] = None
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

    def fetch(self) -> Union[str, None]:
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
            self, file_to_save: Union[str, None] = None, editor: Union[None, CodeEditor] = None,
            before_write_callback: Callable | None = None) -> None:
        jeditor_logger.info(f"Init CodeEditSaveThread "
                            f"file_to_save: {file_to_save} "
                            f"editor: {editor}")
        super().__init__()
        self.file: str = file_to_save
        self.editor: Union[None, CodeEditor] = editor
        self.still_run: bool = True
        self.daemon = True
        self.skip_this_round: bool = False
        self.before_write_callback = before_write_callback
        # 建立主執行緒上的文字提取器 / Create text fetcher on main thread
        self._text_fetcher: Union[_TextFetcher, None] = None
        if editor is not None:
            self._text_fetcher = _TextFetcher(editor)

    def _get_editor_text(self) -> Union[str, None]:
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

    def run(self) -> None:
        """
        loop and save current edit file
        持續迴圈，每隔一段時間自動儲存當前編輯檔案
        """
        jeditor_logger.info("CodeEditSaveThread run")
        if self.file is not None:
            path = Path(self.file)
            while path.is_file() and self.editor is not None:
                time.sleep(5)
                if not self.still_run:
                    break
                if self.skip_this_round:
                    continue
                try:
                    text = self._get_editor_text()
                    if text is not None:
                        if self.before_write_callback is not None:
                            self.before_write_callback()
                        write_file(self.file, text)
                except Exception as e:
                    jeditor_logger.error(f"Auto-save failed for {self.file}: {e}")
