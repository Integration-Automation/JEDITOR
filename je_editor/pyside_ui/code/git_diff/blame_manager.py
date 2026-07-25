"""
管理編輯器的行內 blame 標註
Hold the inline blame annotations for one editor.

blame 要跑 git，因此在背景執行緒取得；只有使用者開啟顯示時才會去取。
Blame runs git, so it is fetched on a worker thread, and only once the user has
actually turned the display on.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from je_editor.git_client.file_blame import BlameLine, blame_lines


class BlameLoader(QThread):
    """
    在背景取得檔案的 blame 資訊
    Fetch a file's blame off the UI thread.
    """

    loaded = Signal(object)  # dict[int, BlameLine]

    def __init__(self, file_path: str | Path, parent=None) -> None:
        """
        :param file_path: 要取得 blame 的檔案 / the file to annotate
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._file_path = file_path

    def run(self) -> None:
        """取得並回報 blame 資訊 / Fetch the blame and report it."""
        self.loaded.emit(blame_lines(self._file_path))


class BlameManager:
    """
    追蹤行內 blame 的開關與內容
    Track whether inline blame is shown, and what it says.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 這些標註所屬的編輯器 / the editor being annotated
        """
        self._code_edit = code_edit
        self._annotations: dict[int, BlameLine] = {}
        self._enabled = False
        self._loader: BlameLoader | None = None

    @property
    def enabled(self) -> bool:
        """目前是否顯示 blame / Whether the annotations are being shown."""
        return self._enabled

    def annotation(self, line: int) -> str:
        """
        取得某行的標註文字
        The annotation text for one line.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 標註文字，關閉或該行無資料時為空字串 / the text, or an empty string
        """
        if not self._enabled:
            return ""
        blame = self._annotations.get(line)
        return blame.annotation if blame is not None else ""

    def set_annotations(self, annotations: dict[int, BlameLine]) -> None:
        """
        套用一組標註
        Apply a set of annotations.

        :param annotations: 行號對應的提交資訊 / line number -> commit information
        """
        self._annotations = dict(annotations)

    def clear(self) -> None:
        """清除標註並關閉顯示 / Drop the annotations and turn the display off."""
        self._annotations = {}
        self._enabled = False

    def toggle(self, file_path: str | Path | None) -> bool:
        """
        切換顯示；開啟時在背景取得資料
        Toggle the display, fetching the data in the background when turning on.

        :param file_path: 目前編輯的檔案 / the file being edited
        :return: 切換後是否為開啟 / whether the display is now on
        """
        self.stop()
        if self._enabled:
            self._enabled = False
            self._annotations = {}
            return False
        if file_path is None:
            return False
        self._enabled = True
        loader = BlameLoader(file_path)
        self._loader = loader
        loader.loaded.connect(lambda annotations: self._on_loaded(loader, annotations))
        loader.finished.connect(loader.deleteLater)
        loader.start()
        return True

    def _on_loaded(self, loader: BlameLoader, annotations: dict) -> None:
        """套用背景取得的結果 / Apply annotations that finished loading."""
        if loader is not self._loader:
            return
        self.set_annotations(annotations)
        self._code_edit.viewport().update()

    def stop(self) -> None:
        """結束仍在進行的取得 / Stop a fetch that is still running."""
        loader, self._loader = self._loader, None
        if loader is not None and loader.isRunning():
            loader.blockSignals(True)
            loader.wait()
