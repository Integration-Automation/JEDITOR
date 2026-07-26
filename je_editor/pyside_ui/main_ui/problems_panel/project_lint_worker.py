"""
在背景檢查整個專案
Lint a whole project off the UI thread.

專案檢查會開一個 ruff 子程序走遍所有檔案，大專案要跑上好幾秒。在 UI 執行緒做這件
事會讓整個視窗在這段時間內完全沒有反應，因此改由工作執行緒執行，完成後再把診斷交
回主執行緒。單檔檢查早就是這樣做的（見 ``lint_manager``），這裡採用同樣的做法。
A project check spawns one ruff subprocess that walks every file, which takes
seconds on a large tree. Doing that on the UI thread freezes the whole window
for the duration, so it runs on a worker thread and hands the diagnostics back
when it finishes. The single-file check already works this way (see
``lint_manager``); this follows the same shape.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from je_editor.code_scan.ruff_lint import lint_project


class ProjectLintWorker(QThread):
    """
    在背景對一個目錄執行 ruff
    Run ruff over a directory without blocking the UI.
    """

    linted = Signal(object)  # list[Diagnostic]

    def __init__(self, root: str | Path, parent=None) -> None:
        """
        :param root: 要檢查的專案根目錄 / the project root to check
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._root = str(root)

    @property
    def root(self) -> str:
        """這次檢查的目錄 / The directory being checked."""
        return self._root

    def run(self) -> None:
        """執行檢查並回報結果 / Lint and report the result."""
        self.linted.emit(lint_project(self._root))
