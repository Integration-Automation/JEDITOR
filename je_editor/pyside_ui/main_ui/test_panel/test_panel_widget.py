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
    QCheckBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.test_runner.pytest_output import (
    PytestResult, failure_for_result, parse_coverage, parse_failures, parse_results,
    parse_summary, parse_tracebacks, traceback_for_result
)

# 樹狀清單欄位索引 / Column indexes in the tree
COLUMN_OUTCOME = 0
COLUMN_TEST = 1
COLUMN_FILE = 2
# 測試名稱欄的預設寬度 / Default width of the test column
TEST_COLUMN_WIDTH = 360
# 單次測試執行的逾時（秒）/ Timeout for one test run
RUN_TIMEOUT_SECONDS = 600
# 清單與追蹤訊息的高度比例 / How the list and the traceback share the height
_RESULT_STRETCH = 3
_TRACEBACK_STRETCH = 2


def pytest_command(node_ids: list[str] | None = None,
                   with_coverage: bool = False) -> list[str]:
    """
    組出執行測試的指令
    Build the command that runs the tests.

    ``-v`` 才會逐項列出結果；``--tb=short`` 每個失敗印出足夠閱讀的追蹤訊息，同時
    仍然保留「檔案:行號」那一行，跳轉才有得用。
    ``-v`` is what lists each test, and ``--tb=short`` prints a traceback worth
    reading while still carrying the ``file:line`` the jump needs.

    :param node_ids: 只跑這些測試，``None`` 表示全部 / run only these, or all when ``None``
    :param with_coverage: 是否一併量測覆蓋率 / whether to measure coverage too
    :return: 引數清單（不經過 shell）/ the argument list, never a shell string
    """
    command = [sys.executable, "-m", "pytest", "-v", "--tb=short", "-p", "no:cacheprovider"]
    if with_coverage:
        # 需要目標專案裝有 pytest-cov；沒有的話 pytest 會直接說不認得這個參數
        # This needs pytest-cov in the target project; without it pytest simply
        # reports that it does not recognise the argument
        command.extend(["--cov=.", "--cov-report=term"])
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

    def __init__(self, working_dir: str, node_ids: list[str] | None = None,
                 with_coverage: bool = False, parent=None) -> None:
        """
        :param working_dir: 執行測試的目錄 / the directory to run the tests in
        :param node_ids: 只跑這些測試 / run only these tests
        :param with_coverage: 是否一併量測覆蓋率 / whether to measure coverage too
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self.setObjectName("PytestRunThread")
        self._working_dir = working_dir
        self._node_ids = node_ids
        self._with_coverage = with_coverage

    def run(self) -> None:
        """執行測試並回報輸出 / Run the tests and report their output."""
        try:
            completed = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
                pytest_command(self._node_ids, self._with_coverage),
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
        self._tracebacks: dict[str, str] = {}
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
        self.coverage_check = QCheckBox(word.get("test_panel_coverage"))
        self.status_label = QLabel(word.get("test_panel_ready"))

        # 失敗的追蹤訊息：選到某個測試就顯示它的那一段
        # The failing traceback: selecting a test shows the block belonging to it
        self.traceback_view = QPlainTextEdit()
        self.traceback_view.setReadOnly(True)
        self.traceback_view.setPlaceholderText(word.get("test_panel_traceback_placeholder"))

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
        self.result_tree.itemSelectionChanged.connect(self._show_selected_traceback)

        controls = QHBoxLayout()
        controls.addWidget(self.run_button)
        controls.addWidget(self.run_selected_button)
        controls.addWidget(self.rerun_failures_button)
        controls.addWidget(self.filter_edit)
        controls.addWidget(self.coverage_check)
        controls.addWidget(self.status_label)
        controls.addStretch()

        # 清單與追蹤訊息上下並排，中間可以拖動
        # The list and the traceback sit one above the other, with a draggable split
        split = QSplitter(Qt.Orientation.Vertical)
        split.addWidget(self.result_tree)
        split.addWidget(self.traceback_view)
        split.setStretchFactor(0, _RESULT_STRETCH)
        split.setStretchFactor(1, _TRACEBACK_STRETCH)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(split)
        self.setLayout(layout)

    def results(self) -> list[PytestResult]:
        """取得目前顯示的結果 / The results currently listed."""
        return list(self._results)

    def retranslate(self) -> None:
        """
        換語言後重新標示自己
        Relabel after the language changes.

        面板記著上一次的測試結果，因此只換文字再重畫清單，不重建整個面板。
        The panel is holding the last run's results, so it relabels and redraws
        rather than being rebuilt.
        """
        word = language_wrapper.language_word_dict
        self.run_button.setText(word.get("test_panel_run"))
        self.run_selected_button.setText(word.get("test_panel_run_selected"))
        self.rerun_failures_button.setText(word.get("test_panel_rerun_failures"))
        self.filter_edit.setPlaceholderText(word.get("test_panel_filter_placeholder"))
        self.coverage_check.setText(word.get("test_panel_coverage"))
        self.traceback_view.setPlaceholderText(word.get("test_panel_traceback_placeholder"))
        self.result_tree.setHeaderLabels([
            word.get("test_panel_col_outcome"),
            word.get("test_panel_col_test"),
            word.get("test_panel_col_file"),
        ])
        if not self._results:
            self.status_label.setText(word.get("test_panel_ready"))
        self._render_items()

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
        self._thread = PytestRunThread(
            self._working_dir, node_ids, self.coverage_check.isChecked())
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
        self._tracebacks = parse_tracebacks(output)
        summary = parse_summary(output)
        coverage = parse_coverage(output)
        self.run_button.setEnabled(True)
        self._render_items()
        self.traceback_view.setPlainText("")
        if summary:
            self.status_label.setText(
                f"{summary} — {coverage}" if coverage else summary)
        elif not self._results:
            self.status_label.setText(
                language_wrapper.language_word_dict.get("test_panel_no_results"))

    def traceback_for(self, result: PytestResult) -> str:
        """
        取得某個測試的追蹤訊息
        The traceback reported for one test.

        :param result: 測試結果 / the test result
        :return: 追蹤訊息，沒有時為空字串 / the traceback, or an empty string
        """
        return traceback_for_result(result, self._tracebacks)

    def _show_selected_traceback(self) -> None:
        """把選取測試的追蹤訊息顯示出來 / Show the selected test's traceback."""
        items = self.result_tree.selectedItems()
        if not items:
            self.traceback_view.setPlainText("")
            return
        result = items[0].data(COLUMN_OUTCOME, Qt.ItemDataRole.UserRole)
        self.traceback_view.setPlainText(
            self.traceback_for(result) if result is not None else "")

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
