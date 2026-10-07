"""
統一的診斷模型
One model for every diagnostic.

ruff 與語言伺服器各有自己的欄位與嚴重度寫法。這裡定義所有來源共用的形式：誰報的、
多嚴重、在哪個資源的哪一段、有沒有相關位置與可套用的修正。
ruff and a language server each have their own fields and their own way of
spelling a severity. This defines the shape every source shares: who reported
it, how severe it is, which span of which resource it is on, and whether it
carries related locations or a fix that can be applied.

行與欄都是 1 起算，跟編輯器畫面上的一致。
Lines and columns count from one, as the editor shows them.

純邏輯：不執行任何檢查，也不碰 Qt。
Pure logic: it runs no check and touches no Qt.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import IntEnum
from threading import Lock

from je_editor.core.events.event_hook import EventHook
from je_editor.core.uri.resource_uri import uri_key

# 行與欄的起算值 / What lines and columns count from
FIRST_LINE = 1
FIRST_COLUMN = 1


class Severity(IntEnum):
    """
    診斷的嚴重度
    How severe a diagnostic is.

    數值跟 LSP 的 ``DiagnosticSeverity`` 相同，所以伺服器給的數字可以直接轉換；
    數值越小越嚴重。
    The numbers are LSP's ``DiagnosticSeverity``, so a server's number converts
    directly, and a smaller number is more severe.
    """

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass(frozen=True, order=True)
class Position:
    """
    文件裡的一個位置
    One position in a document.

    :param line: 1 起算的行號 / the 1-based line
    :param column: 1 起算的欄號 / the 1-based column
    """

    line: int = FIRST_LINE
    column: int = FIRST_COLUMN


@dataclass(frozen=True)
class TextRange:
    """
    文件裡的一段範圍
    A span of a document.

    :param start: 起點 / where it starts
    :param end: 終點 / where it ends
    """

    start: Position
    end: Position

    @classmethod
    def from_lines(cls, line: int, column: int = FIRST_COLUMN,
                   end_line: int | None = None, end_column: int | None = None) -> TextRange:
        """
        由行列數字建立範圍，不合理的數字會被修正
        Build a range from line and column numbers, correcting nonsense.

        工具的輸出偶爾會有小於一的行號或在起點之前的終點；診斷仍然要能顯示，所以
        這裡修正而不是報錯。
        A tool's output now and then has a line below one or an end before the
        start. The diagnostic still has to be shown, so this corrects rather
        than raises.

        :param line: 起始行 / the start line
        :param column: 起始欄 / the start column
        :param end_line: 結束行，沒給時同起始行 / the end line, the start line when omitted
        :param end_column: 結束欄，沒給時同起始欄 / the end column, the start column
            when omitted
        :return: 範圍 / the range
        """
        start = Position(max(FIRST_LINE, line), max(FIRST_COLUMN, column))
        end = Position(
            start.line if end_line is None else end_line,
            start.column if end_column is None else max(FIRST_COLUMN, end_column),
        )
        return cls(start, max(start, end))


@dataclass(frozen=True)
class RelatedInformation:
    """
    跟一筆診斷有關的另一個位置
    Another location that has to do with a diagnostic.

    :param uri: 那個位置所在的資源 / the resource that location is in
    :param range: 那個位置的範圍 / the span of that location
    :param message: 說明 / what it has to do with the diagnostic
    """

    uri: str
    range: TextRange
    message: str


@dataclass(frozen=True)
class TextEdit:
    """
    一筆文字替換
    One replacement of text.

    :param range: 要換掉的範圍 / the span to replace
    :param new_text: 換上去的文字 / the text to put there
    """

    range: TextRange
    new_text: str


@dataclass(frozen=True)
class QuickFix:
    """
    一筆診斷可以套用的修正
    A fix that can be applied for a diagnostic.

    :param title: 給使用者看的名稱 / the name to show the user
    :param edits: 套用時要做的替換 / the replacements that apply it
    """

    title: str
    edits: tuple[TextEdit, ...] = ()


@dataclass(frozen=True)
class Diagnostic:
    """
    一筆診斷
    One diagnostic.

    :param message: 說明文字 / the human-readable message
    :param range: 所在範圍 / the span it is on
    :param severity: 嚴重度 / how severe it is
    :param source: 誰報的，例如 ``ruff`` 或語言伺服器的名稱 / who reported it,
        such as ``ruff`` or a language server's name
    :param code: 規則代碼 / the rule code
    :param uri: 所在資源的 URI / the URI of the resource it is in
    :param related: 相關的其他位置 / other locations that relate to it
    :param fixes: 可以套用的修正 / the fixes that can be applied
    """

    message: str
    range: TextRange
    severity: Severity = Severity.ERROR
    source: str = ""
    code: str = ""
    uri: str = ""
    related: tuple[RelatedInformation, ...] = ()
    fixes: tuple[QuickFix, ...] = ()

    @property
    def label(self) -> str:
        """給面板顯示的一行說明 / A single line for a panel."""
        return f"{self.code} {self.message}" if self.code else self.message

    @property
    def sort_key(self) -> tuple[str, Position, int, str, str, str]:
        """讓清單順序固定的排序鍵 / The key that gives a list one fixed order."""
        return (uri_key(self.uri), self.range.start, int(self.severity),
                self.source, self.code, self.message)


def filter_diagnostics(diagnostics: Iterable[Diagnostic],
                       severities: Iterable[Severity] | None = None,
                       sources: Iterable[str] | None = None) -> list[Diagnostic]:
    """
    依嚴重度與來源篩選診斷
    Filter diagnostics by severity and by source.

    結果一律依資源、位置、嚴重度排序，所以同一組診斷不管怎麼篩，順序都相同。
    The result is always ordered by resource, position and severity, so one set
    of diagnostics comes out in the same order however it is filtered.

    :param diagnostics: 要篩選的診斷 / the diagnostics to filter
    :param severities: 要保留的嚴重度，``None`` 表示全部 / the severities to keep,
        ``None`` for all of them
    :param sources: 要保留的來源，``None`` 表示全部 / the sources to keep, ``None``
        for all of them
    :return: 符合條件的診斷 / the diagnostics that match
    """
    wanted_severities = None if severities is None else set(severities)
    wanted_sources = None if sources is None else set(sources)
    kept = [
        item for item in diagnostics
        if (wanted_severities is None or item.severity in wanted_severities)
        and (wanted_sources is None or item.source in wanted_sources)
    ]
    return sorted(kept, key=lambda item: item.sort_key)


class DiagnosticStore:
    """
    所有來源回報的診斷
    The diagnostics every source has reported.

    每個來源對每個資源各有一組診斷，重新回報時整組換掉——這是 LSP
    ``publishDiagnostics`` 的語意，ruff 每檢查一次也是整份重來。
    Each source holds one set of diagnostics per resource and a new report
    replaces that set, which is what LSP's ``publishDiagnostics`` means and what
    a ruff run amounts to as well.
    """

    def __init__(self) -> None:
        # (來源, 資源的鍵) -> 診斷 / (source, resource key) -> diagnostics
        self._reports: dict[tuple[str, str], tuple[Diagnostic, ...]] = {}
        self._lock = Lock()
        # 某個資源的診斷變了之後發出，引數是它的 URI
        # Fired after a resource's diagnostics change, with its URI
        self.changed = EventHook("diagnostics changed")

    def publish(self, source: str, uri: str, diagnostics: Iterable[Diagnostic]) -> bool:
        """
        回報某個來源對某個資源的整組診斷
        Report everything one source has to say about one resource.

        :param source: 來源名稱 / the source's name
        :param uri: 資源的 URI / the resource's URI
        :param diagnostics: 這個來源目前對它的所有診斷；空的表示沒有問題
            everything this source now reports for it; empty means no findings
        :return: 內容是否改變（沒變時訂閱者不會被通知）/ whether anything changed;
            subscribers are not told when nothing did
        """
        report = tuple(replace(item, source=source, uri=uri) for item in diagnostics)
        key = (source, uri_key(uri))
        with self._lock:
            if self._reports.get(key, ()) == report:
                return False
            if report:
                self._reports[key] = report
            else:
                del self._reports[key]
        self.changed.emit(uri)
        return True

    def clear(self, source: str | None = None, uri: str | None = None) -> bool:
        """
        清掉診斷
        Drop diagnostics.

        :param source: 只清這個來源的；``None`` 表示所有來源 / only this source's,
            or every source's when ``None``
        :param uri: 只清這個資源的；``None`` 表示所有資源 / only this resource's,
            or every resource's when ``None``
        :return: 是否真的清掉了什麼 / whether anything was dropped
        """
        wanted_key = None if uri is None else uri_key(uri)
        with self._lock:
            doomed = [
                key for key in self._reports
                if (source is None or key[0] == source)
                and (wanted_key is None or key[1] == wanted_key)
            ]
            affected = {self._reports.pop(key)[0].uri for key in doomed}
        for affected_uri in sorted(affected):
            self.changed.emit(affected_uri)
        return bool(doomed)

    def select(self, severities: Iterable[Severity] | None = None,
               sources: Iterable[str] | None = None, uri: str | None = None) -> list[Diagnostic]:
        """
        取出符合條件的診斷
        The diagnostics that match.

        :param severities: 要保留的嚴重度，``None`` 表示全部 / the severities to
            keep, ``None`` for all of them
        :param sources: 要保留的來源，``None`` 表示全部 / the sources to keep,
            ``None`` for all of them
        :param uri: 只看這個資源，``None`` 表示全部 / only this resource, ``None``
            for all of them
        :return: 排序好的診斷 / the diagnostics, in a fixed order
        """
        wanted_key = None if uri is None else uri_key(uri)
        with self._lock:
            gathered = [
                item for key, report in self._reports.items()
                if wanted_key is None or key[1] == wanted_key
                for item in report
            ]
        return filter_diagnostics(gathered, severities, sources)

    def counts(self) -> dict[Severity, int]:
        """
        各嚴重度的診斷數量
        How many diagnostics there are at each severity.

        :return: 每一種嚴重度的數量，沒有的也列為零 / the count for every severity,
            zero included
        """
        totals = {severity: 0 for severity in Severity}
        for item in self.select():
            totals[item.severity] += 1
        return totals

    def sources(self) -> list[str]:
        """目前有回報診斷的來源，依名稱排序 / The sources with findings, sorted by name."""
        with self._lock:
            return sorted({key[0] for key in self._reports})

    def __len__(self) -> int:
        with self._lock:
            return sum(len(report) for report in self._reports.values())
