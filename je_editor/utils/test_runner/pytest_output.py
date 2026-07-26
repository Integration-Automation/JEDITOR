"""
解析 pytest 的輸出成測試結果
Turn pytest's output into test results.

面板用這些結果列出每個測試，並讓失敗的項目可以直接跳到出錯的那一行。
The panel lists each test from these results and jumps to the failing line.

純邏輯：不執行 pytest，因此可以用固定的輸出樣本測試。
Pure logic: it does not run pytest, so it can be tested against fixed output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 比對 ``path::test_name PASSED [ 50%]`` 這類結果行
# Matches a result line such as ``path::test_name PASSED [ 50%]``
_RESULT_PATTERN = re.compile(
    r"^(?P<node>\S+::\S+)\s+(?P<outcome>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b")
# 比對 ``--tb=line`` 的失敗位置，例如 ``D:\p\test_x.py:42: AssertionError``
# Matches a ``--tb=line`` failure location, e.g. ``D:\p\test_x.py:42: AssertionError``
_FAILURE_PATTERN = re.compile(r"^(?P<path>.+?):(?P<line>\d+): (?P<message>.+)$")
# 比對結尾統計行，例如 ``3 failed, 5 passed in 0.42s``
# Matches the summary line, e.g. ``3 failed, 5 passed in 0.42s``
_SUMMARY_PATTERN = re.compile(r"^=+\s*(?P<summary>.*?(?:passed|failed|error|no tests ran).*?)\s*=+$")

# 比對區段標題：pytest 用等號或連字號把標題包起來，覆蓋率報告與結尾統計都算
# Matches a section banner: pytest fences its titles in equals signs or dashes,
# which covers the coverage report and the closing summary as well
_SECTION_BANNER = re.compile(r"^(?P<fence>[=-]){2,}\s*(?P<title>.*?)\s*(?P=fence){2,}$")
# 比對追蹤訊息的標題，例如 ``____ TestThing.test_case ____``
# Matches a traceback heading such as ``____ TestThing.test_case ____``
_FAILURE_HEADER = re.compile(r"^_{2,}\s*(?P<name>.+?)\s*_{2,}$")
# 比對覆蓋率報告的總計行，例如 ``TOTAL   1200   84   93%``
# Matches a coverage report's total, e.g. ``TOTAL   1200   84   93%``
_COVERAGE_TOTAL = re.compile(r"^TOTAL\s+\d+\s+\d+\s+(?P<percent>\d+)%")

# 帶有追蹤訊息的區段 / The sections that carry tracebacks
_FAILURE_SECTIONS = frozenset({"FAILURES", "ERRORS"})

# 視為失敗的結果 / Outcomes that count as a failure
FAILING_OUTCOMES = frozenset({"FAILED", "ERROR"})


@dataclass(frozen=True)
class PytestResult:
    """
    一個測試的結果
    One test's result.

    :param node_id: pytest 的節點名稱 / pytest's node id
    :param outcome: 結果，例如 ``PASSED`` / the outcome, such as ``PASSED``
    """

    node_id: str
    outcome: str

    @property
    def failed(self) -> bool:
        """這個結果是否算失敗 / Whether this result counts as a failure."""
        return self.outcome in FAILING_OUTCOMES

    @property
    def file_path(self) -> str:
        """節點所屬的檔案 / The file the node belongs to."""
        return self.node_id.split("::", 1)[0]

    @property
    def name(self) -> str:
        """節點的測試名稱 / The test's name within its file."""
        return self.node_id.split("::", 1)[1] if "::" in self.node_id else self.node_id


@dataclass(frozen=True)
class FailureLocation:
    """
    一個失敗的位置
    Where a failure happened.

    :param path: 檔案路徑 / the file's path
    :param line: 行號（1 起算）/ the 1-based line number
    :param message: 錯誤訊息 / the error message
    """

    path: str
    line: int
    message: str


def parse_results(output: str) -> list[PytestResult]:
    """
    解析每個測試的結果
    Parse each test's result.

    :param output: pytest 的輸出（需要 ``-v``）/ pytest's output, as produced with ``-v``
    :return: 測試結果，依出現順序 / the results, in the order they were reported
    """
    results: list[PytestResult] = []
    for line in output.splitlines():
        match = _RESULT_PATTERN.match(line.strip())
        if match is not None:
            results.append(
                PytestResult(node_id=match.group("node"), outcome=match.group("outcome")))
    return results


def parse_failures(output: str) -> list[FailureLocation]:
    """
    解析失敗的位置
    Parse the reported failure locations.

    :param output: pytest 的輸出（需要 ``--tb=line``）/ pytest's output, with ``--tb=line``
    :return: 失敗位置，依出現順序且不重複 / the locations, in order, without repeats
    """
    failures: list[FailureLocation] = []
    seen: set[tuple[str, int]] = set()
    for line in output.splitlines():
        stripped = line.strip()
        match = _FAILURE_PATTERN.match(stripped)
        if match is None:
            continue
        try:
            line_number = int(match.group("line"))
        except ValueError:
            continue
        path = match.group("path").strip()
        # 結果行本身也含有冒號，排除掉才不會被誤認成失敗位置
        # A result line also contains a colon; skipping those avoids reading one
        # as a failure location
        if "::" in path or not path:
            continue
        key = (path, line_number)
        if key in seen:
            continue
        seen.add(key)
        failures.append(
            FailureLocation(path=path, line=line_number, message=match.group("message")))
    return failures


def parse_tracebacks(output: str) -> dict[str, str]:
    """
    解析每個失敗測試的追蹤訊息
    Parse the traceback reported for each failing test.

    pytest 會在 ``FAILURES`` 區段裡，以一行底線包住測試名稱作為每一段的開頭。
    In its ``FAILURES`` section pytest starts each block with the test's name
    fenced by underscores.

    :param output: pytest 的輸出（需要 ``--tb=short`` 或更詳細）
        pytest's output, with ``--tb=short`` or longer
    :return: 測試名稱對應追蹤訊息 / test name -> its traceback
    """
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    in_failures = False
    for line in output.splitlines():
        stripped = line.rstrip()
        banner = _SECTION_BANNER.match(stripped.strip())
        if banner is not None:
            title = banner.group("title").strip().upper()
            in_failures = title in _FAILURE_SECTIONS
            current = None
            continue
        if not in_failures:
            continue
        header = _FAILURE_HEADER.match(stripped.strip())
        if header is not None:
            current = header.group("name").strip()
            blocks.setdefault(current, [])
            continue
        if current is not None:
            blocks[current].append(stripped)
    return {name: "\n".join(lines).strip() for name, lines in blocks.items() if lines}


def traceback_name(node_id: str) -> str:
    """
    把節點名稱換成 pytest 在追蹤訊息標題用的寫法
    Turn a node id into the name pytest heads its traceback with.

    ``test/x.py::TestThing::test_case`` 的標題是 ``TestThing.test_case``。
    ``test/x.py::TestThing::test_case`` is headed ``TestThing.test_case``.

    :param node_id: pytest 的節點名稱 / pytest's node id
    :return: 追蹤訊息的標題 / the traceback's heading
    """
    parts = node_id.split("::")
    return ".".join(parts[1:]) if len(parts) > 1 else node_id


def traceback_for_result(result: PytestResult, tracebacks: dict[str, str]) -> str:
    """
    取得某個測試的追蹤訊息
    The traceback belonging to one test.

    :param result: 測試結果 / the test result
    :param tracebacks: :func:`parse_tracebacks` 的結果 / what :func:`parse_tracebacks` returned
    :return: 追蹤訊息，沒有時為空字串 / the traceback, or an empty string
    """
    return tracebacks.get(traceback_name(result.node_id), "")


def parse_coverage(output: str) -> str:
    """
    取得覆蓋率報告的總計
    The total from a coverage report.

    :param output: pytest 的輸出 / pytest's output
    :return: 總計百分比，例如 ``87%``；沒有報告時為空字串
        the total percentage such as ``87%``, or an empty string
    """
    for line in reversed(output.splitlines()):
        match = _COVERAGE_TOTAL.match(line.strip())
        if match is not None:
            return f"{match.group('percent')}%"
    return ""


def parse_summary(output: str) -> str:
    """
    取得結尾的統計文字
    The summary line pytest finished with.

    :param output: pytest 的輸出 / pytest's output
    :return: 統計文字，找不到時為空字串 / the summary, or an empty string
    """
    for line in reversed(output.splitlines()):
        match = _SUMMARY_PATTERN.match(line.strip())
        if match is not None:
            return match.group("summary").strip()
    return ""


def failure_for_result(
        result: PytestResult, failures: list[FailureLocation]) -> FailureLocation | None:
    """
    找出某個失敗測試對應的位置
    Find the failure location belonging to a failed test.

    以檔案路徑比對，因為 ``--tb=line`` 只報位置不報節點名稱。
    Matching is by file path, since ``--tb=line`` reports a location without the
    node it belongs to.

    :param result: 測試結果 / the test result
    :param failures: 所有失敗位置 / every reported failure location
    :return: 對應的位置，找不到時為 ``None`` / the location, or ``None``
    """
    if not result.failed:
        return None
    file_name = result.file_path.replace("\\", "/").split("/")[-1]
    for failure in failures:
        if failure.path.replace("\\", "/").split("/")[-1] == file_name:
            return failure
    return None
