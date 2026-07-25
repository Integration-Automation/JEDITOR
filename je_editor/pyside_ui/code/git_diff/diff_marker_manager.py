"""
管理編輯器的 git 變更標記狀態
Hold the git change-marker state for one editor.

基準文字（HEAD 版本）由背景執行緒讀取，因為那是 git 與檔案 I/O；
之後每次重算都只是記憶體內的比對，因此可以在輸入時便宜地重算。
The baseline (the HEAD version) is read on a background thread because that is
git and file I/O; recomputing against it afterwards is a pure in-memory
comparison, cheap enough to redo while typing.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from je_editor.git_client.file_baseline import baseline_text
from je_editor.utils.file_diff.line_status import (
    Hunk,
    baseline_lines_of,
    hunk_at_line,
    line_statuses,
    next_changed_line,
    previous_changed_line,
)


class BaselineLoader(QThread):
    """
    在背景讀取檔案的 HEAD 內容
    Read a file's HEAD content off the UI thread.
    """

    loaded = Signal(object)  # str | None

    def __init__(self, file_path: str | Path, parent=None) -> None:
        """
        :param file_path: 要讀取基準的檔案 / the file whose baseline to read
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._file_path = file_path

    def run(self) -> None:
        """讀取並回報基準文字 / Read the baseline and report it."""
        self.loaded.emit(baseline_text(self._file_path))


class DiffMarkerManager(QObject):
    """
    追蹤緩衝區相對於已提交版本的逐行差異
    Track how the buffer differs, line by line, from its committed version.

    是編輯器的 QObject 子物件，讀取執行緒的訊號才有接收者可斷開；否則編輯器銷毀
    後，佇列中的結果會打到已經釋放的物件上。
    A QObject child of the editor, so the loader's signal has a receiver Qt can
    disconnect; otherwise a queued result would arrive at an editor that is
    already gone.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 這些標記所屬的編輯器 / the editor these markers belong to
        """
        super().__init__(code_edit)
        self._code_edit = code_edit
        self._baseline: str | None = None
        self._statuses: dict[int, str] = {}
        self._loader: BaselineLoader | None = None

    @property
    def has_baseline(self) -> bool:
        """是否已取得基準（檔案在 git 中且有提交過）/ Whether a baseline is known."""
        return self._baseline is not None

    def baseline(self) -> str | None:
        """
        取得目前的基準文字
        Return the baseline the markers are computed against.

        :return: HEAD 版本的內容，沒有基準時為 ``None`` / the committed text, or ``None``
        """
        return self._baseline

    def set_baseline(self, text: str | None) -> None:
        """
        設定基準文字並重算標記
        Set the baseline and recompute the markers.

        :param text: HEAD 版本的內容，``None`` 表示沒有基準
            the committed content, or ``None`` when there is none
        """
        self._baseline = text
        self.refresh()

    def clear(self) -> None:
        """清除基準與標記 / Forget the baseline and every marker."""
        self._baseline = None
        self._statuses = {}

    def refresh(self) -> bool:
        """
        依目前緩衝區內容重算標記
        Recompute the markers from the buffer's current text.

        :return: 標記是否改變（未改變時呼叫端可省下重繪）
            whether the markers changed, so the caller can skip a repaint
        """
        if self._baseline is None:
            changed = bool(self._statuses)
            self._statuses = {}
            return changed
        statuses = line_statuses(self._baseline, self._code_edit.toPlainText())
        if statuses == self._statuses:
            return False
        self._statuses = statuses
        return True

    def status(self, line: int) -> str | None:
        """
        取得某一行的狀態
        Return one line's status.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 狀態字串，未變更時為 ``None`` / the status, or ``None``
        """
        return self._statuses.get(line)

    def statuses(self) -> dict[int, str]:
        """取得所有變更行的狀態副本 / A copy of every changed line's status."""
        return dict(self._statuses)

    def next_change(self, line: int) -> int | None:
        """下一個變更行 / The next changed line, wrapping around."""
        return next_changed_line(self._statuses, line)

    def previous_change(self, line: int) -> int | None:
        """上一個變更行 / The previous changed line, wrapping around."""
        return previous_changed_line(self._statuses, line)

    def hunk_at(self, line: int) -> Hunk | None:
        """
        取得包含指定行的變更區塊
        Return the hunk of change containing *line*.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 變更區塊，該行沒有變更時為 ``None`` / the hunk, or ``None``
        """
        if self._baseline is None:
            return None
        return hunk_at_line(self._baseline, self._code_edit.toPlainText(), line)

    def baseline_lines(self, hunk: Hunk) -> list[str]:
        """
        取得一段變更在基準中的原始內容
        The baseline lines a hunk replaced.

        :param hunk: 目標變更區塊 / the hunk to look up
        :return: 原始行 / the original lines
        """
        if self._baseline is None:
            return []
        return baseline_lines_of(self._baseline, hunk)

    def load_baseline(self, file_path: str | Path | None) -> None:
        """
        在背景重新讀取基準；沒有檔案時直接清除
        Reload the baseline in the background, or clear it when there is no file.

        :param file_path: 目前編輯的檔案 / the file being edited
        """
        self.stop()
        if file_path is None:
            self.clear()
            return
        loader = BaselineLoader(file_path, self)
        self._loader = loader
        loader.loaded.connect(self._on_loaded)
        # 先放掉參考再刪除：留著已被刪除的 wrapper，之後呼叫它就會拋 RuntimeError
        # Drop the reference before deleting: keeping a wrapper whose C++ object
        # is gone makes the next call on it raise RuntimeError
        loader.finished.connect(self._on_loader_finished)
        loader.finished.connect(loader.deleteLater)
        loader.start()

    def _on_loader_finished(self) -> None:
        """讀取結束後放掉參考 / Let go of the loader once it has finished."""
        if self.sender() is self._loader:
            self._loader = None

    def _on_loaded(self, text: str | None) -> None:
        """
        套用背景讀取的結果
        Apply a baseline that finished loading.

        只接受目前這個 loader 的結果，換檔案時舊結果就過期了。
        Only the current loader's result is accepted; switching files makes an
        in-flight read stale.
        """
        if self.sender() is not self._loader:
            return
        self.set_baseline(text)
        self._code_edit.line_number.update()

    def stop(self) -> None:
        """
        結束仍在進行的背景讀取
        Stop a baseline read that is still running.
        """
        loader, self._loader = self._loader, None
        if loader is None:
            return
        try:
            if loader.isRunning():
                loader.quit()
                loader.wait()
        except RuntimeError:
            # 它已經跑完並被刪除了，沒有東西要停
            # It already finished and was deleted, so there is nothing to stop
            return
