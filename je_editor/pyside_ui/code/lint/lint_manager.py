"""
管理一個編輯器的 lint 診斷狀態
Hold the lint state for one editor.

檢查在背景執行緒進行（那是子程序呼叫），完成後把診斷交回主執行緒。
The check runs on a worker thread because it spawns a subprocess, and hands the
diagnostics back to the UI thread when it finishes.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from je_editor.code_scan.ruff_lint import is_lintable, lint_text
from je_editor.utils.lint.ruff_diagnostics import Diagnostic, message_for_line


class LintWorker(QThread):
    """
    在背景對緩衝區內容執行 ruff
    Run ruff over a buffer's text off the UI thread.
    """

    linted = Signal(object)  # list[Diagnostic]

    def __init__(self, text: str, file_path: str | Path, parent=None) -> None:
        """
        :param text: 要檢查的內容 / the text to lint
        :param file_path: 內容對應的檔名 / the name the text is saved under
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._text = text
        self._file_path = file_path

    def run(self) -> None:
        """執行檢查並回報結果 / Lint and report the result."""
        self.linted.emit(lint_text(self._text, self._file_path))


class LintManager(QObject):
    """
    追蹤編輯器目前的診斷
    Track the diagnostics currently reported for an editor.

    是編輯器的 QObject 子物件：worker 的訊號要接到「有接收者」的槽，編輯器被銷毀
    時 Qt 才會自動斷開。用 lambda 接收會讓 Qt 找不到接收者，佇列中的訊號之後就會
    打到已經釋放的編輯器上。
    A QObject child of the editor: a worker's signal must reach a slot that has a
    receiver, so Qt disconnects it when the editor is destroyed. A lambda gives Qt
    no receiver, which lets a queued signal arrive at an editor that is already
    gone.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 這些診斷所屬的編輯器 / the editor being linted
        """
        super().__init__(code_edit)
        self._code_edit = code_edit
        self._diagnostics: list[Diagnostic] = []
        self._worker: LintWorker | None = None

    def diagnostics(self) -> list[Diagnostic]:
        """取得目前診斷的副本 / A copy of the current diagnostics."""
        return list(self._diagnostics)

    def for_line(self, line: int) -> list[Diagnostic]:
        """
        取得某行的診斷
        The diagnostics reported on one line.

        :param line: 1 起算的行號 / the 1-based line number
        :return: 該行的診斷 / the diagnostics on that line
        """
        return [item for item in self._diagnostics if item.line == line]

    def message_for_line(self, line: int) -> str | None:
        """
        取得某行診斷的說明文字
        The messages reported on one line, joined for display.

        :param line: 1 起算的行號 / the 1-based line number
        :return: 說明文字，沒有診斷時為 ``None`` / the text, or ``None``
        """
        return message_for_line(self._diagnostics, line)

    def clear(self) -> bool:
        """
        清除所有診斷
        Drop every diagnostic.

        :return: 是否真的有東西被清掉 / whether anything was actually dropped
        """
        if not self._diagnostics:
            return False
        self._diagnostics = []
        return True

    def set_diagnostics(self, diagnostics: list[Diagnostic]) -> bool:
        """
        套用一組診斷
        Apply a set of diagnostics.

        :param diagnostics: 新的診斷清單 / the diagnostics to apply
        :return: 內容是否改變（未改變時呼叫端可省下重繪）
            whether they differ from the previous set, so a repaint can be skipped
        """
        if diagnostics == self._diagnostics:
            return False
        self._diagnostics = list(diagnostics)
        return True

    def request(self, file_path: str | Path | None) -> bool:
        """
        對目前緩衝區內容排一次檢查
        Start one check of the buffer's current text.

        :param file_path: 目前編輯的檔案 / the file being edited
        :return: 是否真的啟動了檢查 / whether a check was actually started
        """
        self.stop()
        if not is_lintable(file_path):
            return False
        worker = LintWorker(self._code_edit.toPlainText(), file_path, self)
        self._worker = worker
        worker.linted.connect(self._on_linted)
        # 先放掉參考再刪除，避免之後對已刪除的物件呼叫方法
        # Drop the reference before deleting, so nothing calls a deleted object
        worker.finished.connect(self._on_worker_finished)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        return True

    def _on_worker_finished(self) -> None:
        """檢查結束後放掉參考 / Let go of the worker once it has finished."""
        if self.sender() is self._worker:
            self._worker = None

    def _on_linted(self, diagnostics: list) -> None:
        """
        套用背景檢查的結果
        Apply diagnostics that finished arriving.

        只接受目前這個 worker 的結果；換檔或再次輸入都會讓舊結果過期。
        Only the current worker's result is accepted: switching files or typing
        again makes an in-flight check stale.
        """
        if self.sender() is not self._worker:
            return
        if self.set_diagnostics(diagnostics):
            self._code_edit.refresh_lint_display()

    def stop(self) -> None:
        """結束仍在執行的檢查 / Stop a check that is still running."""
        worker, self._worker = self._worker, None
        if worker is None:
            return
        try:
            if worker.isRunning():
                worker.blockSignals(True)
                worker.wait()
        except RuntimeError:
            # 它已經跑完並被刪除了 / It already finished and was deleted
            return
