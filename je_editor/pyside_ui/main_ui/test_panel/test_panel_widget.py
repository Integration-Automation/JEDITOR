"""
測試面板：執行 pytest 並列出結果
Test panel: run pytest and list what it reported.

測試在背景執行緒中執行（那是子程序），結束後把輸出解析成一列一列的結果；雙擊
失敗的項目會跳到出錯的那一行。
The run happens on a worker thread because it spawns a subprocess; its output is
then parsed into one row per test, and double-clicking a failure jumps to the
line it failed on.
"""
from __future__ import annotations

import os
import subprocess  # nosec B404 - 以引數清單執行 pytest，未使用 shell
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.test_runner.pytest_output import (
    PytestResult, failure_for_result, parse_failures, parse_results, parse_summary
)

# 樹狀清單欄位索引 / Column indexes in the tree
COLUMN_OUTCOME = 0
COLUMN_TEST = 1
COLUMN_FILE = 2
# 測試名稱欄的預設寬度 / Default width of the test column
TEST_COLUMN_WIDTH = 360
# 單次測試執行的逾時（秒）/ Timeout for one test run
RUN_TIMEOUT_SECONDS = 600


def pytest_command(node_ids: list[str] | None = None) -> list[str]:
    """
    組出執行測試的指令
    Build the command that runs the tests.

    ``-v`` 才會逐項列出結果，``--tb=line`` 讓每個失敗只印一行位置，剛好夠面板用。
    ``-v`` is what lists each test, and ``--tb=line`` prints one location per
    failure, which is exactly what the panel needs.

    :param node_ids: 只跑這些測試，``None`` 表示全部 / run only these, or all when ``None``
    :return: 引數清單（不經過 shell）/ the argument list, never a shell string
    """
    command = [sys.executable, "-m", "pytest", "-v", "--tb=line", "-p", "no:cacheprovider"]
    # 節點名稱是 pytest 自己印出來的，原樣傳回去；仍然是獨立引數，不經過 shell
    # The node ids came from pytest itself and go straight back as separate
    # arguments, never through a shell
    command.extend(node_ids or [])
    return command


class PytestRunThread(QThread):
    """
    在背景執行 pytest
    Run pytest off the UI thread.
    """

    finished_output = Signal(str)

    def __init__(self, working_dir: str, node_ids: list[str] | None = None, parent=None) -> None:
        """
        :param working_dir: 執行測試的目錄 / the directory to run the tests in
        :param node_ids: 只跑這些測試 / run only these tests
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._working_dir = working_dir
        self._node_ids = node_ids

    def run(self) -> None:
        """執行測試並回報輸出 / Run the tests and report their output."""
        try:
            completed = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
                pytest_command(self._node_ids),
                cwd=self._working_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=RUN_TIMEOUT_SECONDS,
                check=False,
            )
            output = f"{completed.stdout or ''}\n{completed.stderr or ''}"
        except (OSError, subprocess.SubprocessError) as error:
            jeditor_logger.error(f"test_panel_widget.py could not run pytest: {error!r}")
            output = ""
        self.finished_output.emit(output)


class TestPanelWidget(QWidget):
    """
    執行專案測試並顯示結果
    Run the project's tests and show what they reported.
    """

    def __init__(self, main_window=None, working_dir: str | None = None) -> None:
        """
        :param main_window: 用來開檔跳行的主視窗 / the window used to open files
        :param working_dir: 執行測試的目錄，``None`` 時自動判斷 / where to run; auto when ``None``
        """
        super().__init__()
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        self._working_dir = working_dir or resolve_working_dir(main_window)
        self._results: list[PytestResult] = []
        self._failures: list = []
        self._thread: PytestRunThread | None = None

        self.run_button = QPushButton(word.get("test_panel_run"))
        self.run_button.clicked.connect(self.start_run)
        self.run_selected_button = QPushButton(word.get("test_panel_run_selected"))
        self.run_selected_button.clicked.connect(self.start_selected_run)
        self.rerun_failures_button = QPushButton(word.get("test_panel_rerun_failures"))
        self.rerun_failures_button.clicked.connect(self.start_failure_run)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(word.get("test_panel_filter_placeholder"))
        self.filter_edit.textChanged.connect(self._render_items)
        self.status_label = QLabel(word.get("test_panel_ready"))

        self.result_tree = QTreeWidget()
        self.result_tree.setColumnCount(3)
        self.result_tree.setHeaderLabels([
            word.get("test_panel_col_outcome"),
            word.get("test_panel_col_test"),
            word.get("test_panel_col_file"),
        ])
        self.result_tree.setColumnWidth(COLUMN_TEST, TEST_COLUMN_WIDTH)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemDoubleClicked.connect(self._open_item)

        controls = QHBoxLayout()
        controls.addWidget(self.run_button)
        controls.addWidget(self.run_selected_button)
        controls.addWidget(self.rerun_failures_button)
        controls.addWidget(self.filter_edit)
        controls.addWidget(self.status_label)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.result_tree)
        self.setLayout(layout)

    def results(self) -> list[PytestResult]:
        """取得目前顯示的結果 / The results currently listed."""
        return list(self._results)

    def start_run(self, node_ids: list[str] | None = None) -> bool:
        """
        啟動一次測試執行
        Start one test run.

        已經在執行時會忽略重複觸發，避免覆寫仍在跑的執行緒。
        A re-entrant trigger is ignored so a still-running thread is never dropped.

        :param node_ids: 只跑這些測試，``None`` 表示全部 / run only these, or all
        :return: 是否真的啟動 / whether a run actually started
        """
        if self._thread is not None and self._thread.isRunning():
            return False
        self.run_button.setEnabled(False)
        self.status_label.setText(language_wrapper.language_word_dict.get("test_panel_running"))
        self._thread = PytestRunThread(self._working_dir, node_ids)
        self._thread.finished_output.connect(self.apply_output)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        return True

    def selected_node_ids(self) -> list[str]:
        """
        取得清單中被選取的測試
        The tests currently selected in the list.

        :return: 節點名稱 / their node ids
        """
        node_ids: list[str] = []
        for item in self.result_tree.selectedItems():
            result = item.data(COLUMN_OUTCOME, Qt.ItemDataRole.UserRole)
            if result is not None:
                node_ids.append(result.node_id)
        return node_ids

    def failed_node_ids(self) -> list[str]:
        """
        取得上一輪失敗的測試
        The tests that failed in the last run.

        :return: 節點名稱 / their node ids
        """
        return [result.node_id for result in self._results if result.failed]

    def start_selected_run(self) -> bool:
        """
        只重跑選取的測試
        Re-run only the selected tests.

        :return: 是否真的啟動 / whether a run actually started
        """
        selected = self.selected_node_ids()
        return self.start_run(selected) if selected else False

    def start_failure_run(self) -> bool:
        """
        只重跑上一輪失敗的測試
        Re-run only the tests that failed last time.

        修一個失敗之後不必等整輪跑完，這是這個面板最常用的動作。
        After fixing one failure there is no need to wait for the whole suite,
        which makes this the panel's most used action.

        :return: 是否真的啟動 / whether a run actually started
        """
        failures = self.failed_node_ids()
        return self.start_run(failures) if failures else False

    def apply_output(self, output: str) -> None:
        """
        解析輸出並更新清單
        Parse the output and rebuild the list.

        :param output: pytest 的輸出 / pytest's output
        """
        self._results = parse_results(output)
        self._failures = parse_failures(output)
        summary = parse_summary(output)
        self.run_button.setEnabled(True)
        self._render_items()
        if summary:
            self.status_label.setText(summary)
        elif not self._results:
            self.status_label.setText(
                language_wrapper.language_word_dict.get("test_panel_no_results"))

    def visible_results(self) -> list[PytestResult]:
        """
        取得符合篩選條件的結果，失敗的排在最前面
        The results matching the filter, failures first.

        :return: 要顯示的結果 / the results to show
        """
        needle = self.filter_edit.text().strip().lower()
        matching = [
            result for result in self._results
            if not needle or needle in result.node_id.lower()
        ]
        return sorted(matching, key=lambda result: not result.failed)

    def _render_items(self) -> None:
        """依目前結果與篩選條件重建清單 / Rebuild the tree for the current filter."""
        self.result_tree.clear()
        for result in self.visible_results():
            row = QTreeWidgetItem([result.outcome, result.name, result.file_path])
            row.setData(COLUMN_OUTCOME, Qt.ItemDataRole.UserRole, result)
            self.result_tree.addTopLevelItem(row)

    def _open_item(self, row: QTreeWidgetItem, _column: int) -> None:
        """開啟被雙擊的測試 / Open the double-clicked test."""
        result = row.data(COLUMN_OUTCOME, Qt.ItemDataRole.UserRole)
        if result is not None:
            self.open_result(result)

    def open_result(self, result: PytestResult) -> bool:
        """
        在編輯器開啟一個測試，失敗的話跳到出錯的行
        Open a test in the editor, jumping to its failing line when it failed.

        :param result: 要開啟的測試結果 / the result to open
        :return: 成功要求開檔時為 ``True`` / ``True`` when the open was requested
        """
        if self._main_window is None or not hasattr(self._main_window, "go_to_new_tab"):
            return False
        failure = failure_for_result(result, self._failures)
        path = Path(failure.path) if failure is not None else Path(self._working_dir) / result.file_path
        self._main_window.go_to_new_tab(path)
        if failure is not None:
            jump_to_line(self._main_window, failure.line)
        return True

    def closeEvent(self, event) -> None:
        """
        關閉前先停掉仍在執行的測試
        Stop a run that is still going before the panel goes away.
        """
        thread = self._thread
        if thread is not None and thread.isRunning():
            thread.blockSignals(True)
            thread.wait()
        super().closeEvent(event)


def resolve_working_dir(main_window) -> str:
    """
    取得執行測試的目錄
    Resolve the directory the tests should run in.

    :param main_window: 主編輯器視窗，可為 ``None`` / the main window, may be ``None``
    :return: 目錄路徑 / the directory path
    """
    working_dir = getattr(main_window, "working_dir", None)
    if working_dir and Path(str(working_dir)).is_dir():
        return str(working_dir)
    return os.getcwd()


def jump_to_line(main_window, line: int) -> bool:
    """
    把目前分頁的游標移到指定行
    Move the current tab's caret to a line.

    :param main_window: 主編輯器視窗 / the main editor window
    :param line: 1 起算的行號 / the 1-based line number
    :return: 成功跳轉時為 ``True`` / ``True`` when the caret moved
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return False
    widget = tab_widget.currentWidget()
    if not isinstance(widget, EditorWidget):
        return False
    return widget.code_edit.jump_to_line(line)
