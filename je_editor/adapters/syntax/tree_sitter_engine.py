"""
以 Tree-sitter 實作的語法引擎
The syntax engine, implemented with Tree-sitter.

這裡是唯一知道 Tree-sitter 的地方：把文字變成語法樹、用查詢檔把節點變成語法分類與
結構區塊，再以核心層的模型交出去。畫面層拿到的只有「第幾行的第幾欄到第幾欄是什麼」。
This is the only place that knows Tree-sitter: it turns text into a tree, uses
query files to turn nodes into categories and structural regions, and hands them
over in the core layer's model. All the widgets ever get is which columns of
which line are what.

文字每變一次就重新分析，但不是從頭來：先找出新舊文字不同的那一段、告訴舊的樹它被
改了哪裡，解析器就只重做受影響的部分，並回報哪幾行的語法因此不同。
The text is analysed again on every change, though not from scratch: the stretch
that differs between the old and the new text is found, the old tree is told
where it was edited, and the parser redoes only what that touches and reports
which lines came out different.

Tree-sitter 或某個文法沒有安裝時不會報錯，那個語言只是變成「不支援」，編輯器退回
原本的高亮器。
A missing Tree-sitter, or a missing grammar, is not an error: the language simply
counts as unsupported and the editor falls back to its older highlighter.
"""
from __future__ import annotations

import threading
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from je_editor.adapters.syntax.grammar_table import (
    BUILTIN_GRAMMARS, HIGHLIGHTS_QUERY_FILE, QUERY_DIRECTORY, REGIONS_QUERY_FILE, GrammarSpec,
    category_for, own_query
)
from je_editor.core.diagnostics.diagnostic_model import Position, TextRange
from je_editor.core.syntax.syntax_model import (
    LineSpan, RegionKind, StructuralRegion, SyntaxCategory, SyntaxSession, SyntaxSpan
)
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 解析器吃 UTF-8：換行位元組不會出現在多位元組字元裡，數行數才不會數錯
# The parser is fed UTF-8: a newline byte never occurs inside a multi-byte
# character, so counting rows cannot go wrong
_ENCODING = "utf-8"
_UTF16 = "utf-16-le"
_UTF16_UNIT_BYTES = 2
_NEWLINE = b"\n"
# UTF-8 的後續位元組是 10xxxxxx / A UTF-8 continuation byte is 10xxxxxx
_CONTINUATION_MASK = 0xC0
_CONTINUATION_BITS = 0x80
# 一次算這麼多行的分類：一行一行查太慢，整份文件一次查則每按一個鍵都要重做
# Categories are worked out this many lines at a time: one line per query is too
# slow, and the whole document per query would be redone on every keystroke
SPAN_CHUNK_LINES = 64
# 超過這個大小就不解析，文字保持沒有顏色 / Beyond this the text is not parsed and stays uncoloured
MAX_SOURCE_BYTES = 2_000_000
_REGION_PREFIX = "region."
_NAME_FIELD = "name"
# Tree-sitter 的位置是 (列, 欄)。一律用索引或解開來讀，不要用 ``.row`` 與 ``.column``：
# tree-sitter 0.26.0 的這兩個屬性每讀一次就少算那個整數一次參考，讀得夠多次之後
# 直譯器會當掉（Python 3.12 之前連 0 這種小整數都會）。
# A Tree-sitter point is (row, column). Read it by index or by unpacking, never
# through ``.row`` and ``.column``: in tree-sitter 0.26.0 each read of those
# attributes drops a reference to the integer, and after enough reads the
# interpreter crashes (before Python 3.12 even a small integer such as 0 does it).
_ROW = 0


def changed_bytes(old: bytes, new: bytes) -> tuple[int, int, int]:
    """
    找出把舊內容變成新內容的最小一段修改
    Find the smallest edit that turns the old content into the new.

    兩端都對齊到字元邊界，樹才不會被告知「修改從一個字的中間開始」。
    Both ends are moved onto character boundaries, so the tree is never told an
    edit starts in the middle of a character.

    :param old: 舊的 UTF-8 內容 / the old UTF-8 content
    :param new: 新的 UTF-8 內容 / the new UTF-8 content
    :return: ``(起點, 舊內容的終點, 新內容的終點)``，都是位元組位置
        ``(start, end in the old content, end in the new)``, all byte offsets
    """
    prefix = _common_prefix(old, new)
    while prefix and (_continues(old, prefix) or _continues(new, prefix)):
        prefix -= 1
    suffix = _common_suffix(old, new, min(len(old), len(new)) - prefix)
    while suffix and _continues(old, len(old) - suffix):
        suffix -= 1
    return prefix, len(old) - suffix, len(new) - suffix


def _continues(data: bytes, index: int) -> bool:
    """這個位置是不是在一個字元的中間 / Whether this offset is inside a character."""
    return index < len(data) and data[index] & _CONTINUATION_MASK == _CONTINUATION_BITS


def _common_prefix(first: bytes, second: bytes) -> int:
    """
    兩段內容開頭相同的位元組數
    How many leading bytes two contents share.

    以二分法比對整段，比對本身由 C 完成；逐一比較位元組在大檔案上慢得多。
    A binary search over slices, so the comparing is done in C. Walking the bytes
    one at a time is far slower on a large file.
    """
    low, high = 0, min(len(first), len(second))
    while low < high:
        middle = (low + high + 1) // 2
        if first[low:middle] == second[low:middle]:
            low = middle
        else:
            high = middle - 1
    return low


def _common_suffix(first: bytes, second: bytes, limit: int) -> int:
    """兩段內容結尾相同的位元組數，不超過上限 / How many trailing bytes two contents share, up to a limit."""
    low, high = 0, limit
    while low < high:
        middle = (low + high + 1) // 2
        if first[len(first) - middle:len(first) - low] == second[len(second) - middle:len(second) - low]:
            low = middle
        else:
            high = middle - 1
    return low


def point_at(source: bytes, offset: int) -> tuple[int, int]:
    """
    把位元組位置換成 Tree-sitter 的 (列, 欄)
    Turn a byte offset into Tree-sitter's (row, column).

    :param source: UTF-8 內容 / the UTF-8 content
    :param offset: 位元組位置 / the byte offset
    :return: 0 起算的列，以及那一列裡的位元組欄
        the 0-based row, and the byte column within it
    """
    return source.count(_NEWLINE, 0, offset), offset - (source.rfind(_NEWLINE, 0, offset) + 1)


def suffix_of(file_name: str) -> str:
    """
    取出檔名、路徑或 URI 的副檔名
    The suffix of a file name, path or URI.

    :param file_name: 檔名、路徑或 URI / the file name, path or URI
    :return: 小寫、含點的副檔名，沒有時為空字串 / the lower-case suffix with its dot, or empty
    """
    tail = file_name.replace("\\", "/").rsplit("/", 1)[-1]
    dot = tail.rfind(".")
    return tail[dot:].lower() if dot > 0 else ""


class _ColumnMap:
    """
    把 UTF-8 的位元組欄換成 UTF-16 的欄
    Turns byte columns of UTF-8 lines into UTF-16 columns.
    """

    def __init__(self, lines: list[str]) -> None:
        """
        :param lines: 文件的每一行 / the lines of the document
        """
        self._lines = lines
        # 只含 ASCII 的行記成 None：位元組欄就是 UTF-16 欄
        # A line of ASCII only is kept as None: its byte columns are its UTF-16 columns
        self._encoded: dict[int, bytes | None] = {}

    def units(self, row: int, byte_column: int | None) -> int:
        """
        :param row: 0 起算的列 / the 0-based row
        :param byte_column: 位元組欄，``None`` 表示行尾 / the byte column, or ``None``
            for the end of the line
        :return: 0 起算的 UTF-16 欄 / the 0-based UTF-16 column
        """
        if row >= len(self._lines):
            return 0
        line = self._lines[row]
        if row not in self._encoded:
            self._encoded[row] = None if line.isascii() else line.encode(_ENCODING, "replace")
        encoded = self._encoded[row]
        if encoded is None:
            return len(line) if byte_column is None else min(byte_column, len(line))
        before = encoded if byte_column is None else encoded[:byte_column]
        return len(before.decode(_ENCODING, "replace").encode(_UTF16)) // _UTF16_UNIT_BYTES


@dataclass(frozen=True)
class LoadedGrammar:
    """
    載入完成、可以拿來解析的文法
    A grammar that is loaded and ready to parse with.

    :param language_id: 語言 ID / the language ID
    :param language: Tree-sitter 的語言物件 / Tree-sitter's language object
    :param highlights: 高亮查詢 / the highlight query
    :param categories: 查詢裡每個有對應的名稱所代表的分類
        the category behind each capture name of the query that has one
    :param regions: 結構區塊的查詢，沒有時為 ``None`` / the region query, if any
    """

    language_id: str
    language: Any
    highlights: Any
    categories: dict[str, SyntaxCategory]
    regions: Any = None


def load_grammar(spec: GrammarSpec, query_directory: Path) -> LoadedGrammar:
    """
    匯入一個文法並編譯它的查詢
    Import a grammar and compile its queries.

    :param spec: 文法的來源 / where the grammar comes from
    :param query_directory: 專案自己的查詢檔所在的目錄
        the directory of the project's own query files
    :return: 載入完成的文法 / the loaded grammar
    :raises ImportError: Tree-sitter 或這個文法沒有安裝
        when Tree-sitter or the grammar is not installed
    :raises ValueError: 文法的版本不相容，或查詢寫錯了
        when the grammar's version is incompatible or a query is wrong
    :raises OSError: 查詢檔讀不出來 / when a query file cannot be read
    """
    from tree_sitter import Language, Query

    module = spec.load()
    language = Language(module.language())
    shipped = getattr(module, "HIGHLIGHTS_QUERY", "")
    extra = own_query(query_directory, spec.language_id, HIGHLIGHTS_QUERY_FILE)
    highlights = Query(language, f"{shipped}\n{extra}")
    names = (highlights.capture_name(index) for index in range(highlights.capture_count))
    categories = {name: category for name in names
                  if (category := category_for(name)) is not None}
    regions_text = own_query(query_directory, spec.language_id, REGIONS_QUERY_FILE)
    regions = Query(language, regions_text) if regions_text.strip() else None
    return LoadedGrammar(spec.language_id, language, highlights, categories, regions)


class TreeSitterSession:
    """
    一份文件的語法樹，文字每變一次就更新一次
    One document's syntax tree, brought up to date whenever its text changes.
    """

    def __init__(self, grammar: LoadedGrammar) -> None:
        """
        :param grammar: 這份文件的語言的文法 / the grammar of the document's language
        """
        from tree_sitter import Parser, QueryCursor

        self._grammar = grammar
        self._parser = Parser(grammar.language)
        self._highlight_cursor = QueryCursor(grammar.highlights)
        self._tree: Any = None
        self._parsed = False
        self._text = ""
        self._source = b""
        self._lines: list[str] = [""]
        self._span_cache: dict[int, tuple[SyntaxSpan, ...]] = {}
        self._regions: tuple[StructuralRegion, ...] | None = None

    @property
    def language_id(self) -> str:
        """這個 session 解析的語言 / The language this session parses."""
        return self._grammar.language_id

    @property
    def has_errors(self) -> bool:
        """目前的文字是否有語法錯誤 / Whether the current text has a syntax error."""
        return self._tree is not None and self._tree.root_node.has_error

    @property
    def line_count(self) -> int:
        """目前的文字有幾行 / How many lines the current text has."""
        return len(self._lines)

    def update(self, text: str) -> LineSpan | None:
        """
        換成新的文字並重新分析
        Take the new text and analyse it again.

        :param text: 整份文件的文字，以 ``\\n`` 分行 / the whole text, lines
            separated by ``\\n``
        :return: 分類可能變了的那幾行；文字沒變時為 ``None``
            the lines whose categories may have changed, or ``None`` when the
            text is the same
        """
        if self._parsed and text == self._text:
            return None
        source = text.encode(_ENCODING, "replace")
        rows = self._reparse(source)
        self._parsed, self._text, self._source = True, text, source
        self._lines = text.split("\n")
        self._span_cache.clear()
        self._regions = None
        last = len(self._lines)
        if rows is None:
            return LineSpan(1, last)
        return LineSpan(min(rows[0] + 1, last), min(rows[1] + 1, last))

    def _reparse(self, source: bytes) -> tuple[int, int] | None:
        """
        解析新的內容，能沿用舊的樹就沿用
        Parse the new content, reusing the old tree where there is one.

        :return: 語法變了的列（0 起算，頭尾包含）；整份都要重看時為 ``None``
            the rows whose syntax changed, 0-based and inclusive, or ``None``
            when the whole document has to be looked at again
        """
        old_tree = self._tree
        if len(source) > MAX_SOURCE_BYTES:
            self._tree = None
            # 本來就沒有樹的話沒有顏色可以清，只回報第一列
            # With no tree before there are no colours to clear: report the first row only
            return None if old_tree is not None or not self._parsed else (0, 0)
        if old_tree is None:
            self._tree = self._parser.parse(source)
            return None
        start, old_end, new_end = changed_bytes(self._source, source)
        start_point = point_at(source, start)
        new_end_point = point_at(source, new_end)
        old_tree.edit(start_byte=start, old_end_byte=old_end, new_end_byte=new_end,
                      start_point=start_point, old_end_point=point_at(self._source, old_end),
                      new_end_point=new_end_point)
        self._tree = self._parser.parse(source, old_tree)
        first, last = start_point[_ROW], new_end_point[_ROW]
        for changed in old_tree.changed_ranges(self._tree):
            first = min(first, changed.start_point[_ROW])
            last = max(last, changed.end_point[_ROW])
        return first, last

    def spans(self, line: int) -> tuple[SyntaxSpan, ...]:
        """
        取得一行的分類，外層的在前、內層的在後
        The categories of one line, outer spans before the spans inside them.

        :param line: 1 起算的行號 / the 1-based line
        :return: 那一行的每一段；行號不存在時為空
            the spans on that line, none when there is no such line
        """
        if self._tree is None or not 1 <= line <= len(self._lines):
            return ()
        row = line - 1
        if row not in self._span_cache:
            self._fill_chunk(row - row % SPAN_CHUNK_LINES)
        return self._span_cache.get(row, ())

    def _fill_chunk(self, first_row: int) -> None:
        """算出從某一列開始的一整塊的分類 / Work out the categories of the chunk starting at a row."""
        end_row = min(first_row + SPAN_CHUNK_LINES, len(self._lines))
        rows: dict[int, list[SyntaxSpan]] = {row: [] for row in range(first_row, end_row)}
        columns = _ColumnMap(self._lines)
        for category, node in self._captured(first_row, end_row):
            (start_row, start_column), (last_row, end_column) = node.start_point, node.end_point
            for row in range(max(start_row, first_row), min(last_row, end_row - 1) + 1):
                begin = columns.units(row, start_column if row == start_row else 0)
                finish = columns.units(row, end_column if row == last_row else None)
                if finish > begin:
                    rows[row].append(SyntaxSpan(begin + 1, finish - begin, category))
        for row, found in rows.items():
            self._span_cache[row] = tuple(found)

    def _captured(self, first_row: int, end_row: int) -> list[tuple[SyntaxCategory, Any]]:
        """
        查出一段列數裡被分類的節點，外層的在前
        The categorised nodes within some rows, outer nodes first.

        同一個節點被好幾條規則抓到時，查詢裡寫在後面的那一條算數；這是 Tree-sitter
        的慣例，文法自帶的查詢也是照這個順序寫的。
        When several patterns capture one node, the pattern written later in the
        query counts. That is Tree-sitter's convention, and the queries the
        grammars ship are ordered for it.
        """
        self._highlight_cursor.set_point_range((first_row, 0), (end_row, 0))
        best: dict[tuple[int, int], tuple[int, SyntaxCategory, Any]] = {}
        for pattern, captures in self._highlight_cursor.matches(self._tree.root_node):
            for name, nodes in captures.items():
                category = self._grammar.categories.get(name)
                if category is None:
                    continue
                for node in nodes:
                    key = (node.start_byte, node.end_byte)
                    if key not in best or pattern >= best[key][0]:
                        best[key] = (pattern, category, node)
        ordered = sorted(best.items(), key=lambda item: (item[0][0], -item[0][1]))
        return [(category, node) for _key, (_pattern, category, node) in ordered]

    def regions(self) -> tuple[StructuralRegion, ...]:
        """
        取得文件的結構區塊
        The structural regions of the document.

        :return: 依起點排序，外層的在前 / ordered by start, outer regions first
        """
        if self._regions is None:
            self._regions = tuple(self._find_regions())
        return self._regions

    def _find_regions(self) -> list[StructuralRegion]:
        """用區塊查詢從樹裡找出結構區塊 / Find the structural regions in the tree with the region query."""
        if self._tree is None or self._grammar.regions is None:
            return []
        from tree_sitter import QueryCursor

        columns = _ColumnMap(self._lines)
        found: list[tuple[int, int, StructuralRegion]] = []
        captures = QueryCursor(self._grammar.regions).captures(self._tree.root_node)
        for name, nodes in captures.items():
            kind = _region_kind(name)
            if kind is None:
                continue
            for node in nodes:
                found.append((node.start_byte, -node.end_byte, self._region(kind, node, columns)))
        found.sort(key=lambda item: item[:2])
        return [region for _start, _end, region in found]

    def _region(self, kind: RegionKind, node: Any, columns: _ColumnMap) -> StructuralRegion:
        """把一個節點變成結構區塊 / Turn one node into a structural region."""
        (start_row, start_column), (end_row, end_column) = node.start_point, node.end_point
        text_range = TextRange(
            Position(start_row + 1, columns.units(start_row, start_column) + 1),
            Position(end_row + 1, columns.units(end_row, end_column) + 1))
        name_node = node.child_by_field_name(_NAME_FIELD)
        name = "" if name_node is None else (
            self._source[name_node.start_byte:name_node.end_byte].decode(_ENCODING, "replace"))
        return StructuralRegion(kind, text_range, name)


def _region_kind(capture_name: str) -> RegionKind | None:
    """``region.class`` 這樣的名稱代表哪一種區塊 / The kind a name such as ``region.class`` stands for."""
    if not capture_name.startswith(_REGION_PREFIX):
        return None
    try:
        return RegionKind(capture_name[len(_REGION_PREFIX):])
    except ValueError:
        jeditor_logger.warning("unknown structural region capture: %s", capture_name)
        return None


class TreeSitterEngine:
    """
    以 Tree-sitter 分析語法的引擎
    The engine that analyses syntax with Tree-sitter.

    文法在第一次用到時才載入，之後共用；每份文件各自有 session。
    A grammar is loaded the first time it is needed and shared from then on. Each
    document has a session of its own.
    """

    def __init__(self, grammars: Iterable[GrammarSpec] = BUILTIN_GRAMMARS,
                 query_directory: str | Path = QUERY_DIRECTORY) -> None:
        """
        :param grammars: 要提供的文法 / the grammars to offer
        :param query_directory: 專案自己的查詢檔所在的目錄
            the directory of the project's own query files
        """
        self._specs = {spec.language_id: spec for spec in grammars}
        self._suffixes = {suffix: spec.language_id
                          for spec in self._specs.values() for suffix in spec.suffixes}
        self._query_directory = Path(query_directory)
        self._loaded: dict[str, LoadedGrammar | None] = {}
        self._lock = threading.Lock()

    def language_ids(self) -> tuple[str, ...]:
        """
        這個引擎目前能分析的語言
        The languages this engine can analyse right now.

        :return: 語言 ID；文法沒裝好的不算 / language IDs, leaving out any whose
            grammar is not usable
        """
        return tuple(language_id for language_id in self._specs
                     if self._grammar(language_id) is not None)

    def language_for(self, file_name: str) -> str | None:
        """
        依檔名判斷語言
        The language of a file, going by its name.

        :param file_name: 檔名、路徑或 URI / a file name, path or URI
        :return: 語言 ID，不認得或文法不能用時為 ``None``
            the language ID, or ``None`` when it is unknown or its grammar is not usable
        """
        language_id = self._suffixes.get(suffix_of(file_name))
        if language_id is None or self._grammar(language_id) is None:
            return None
        return language_id

    def open_session(self, language_id: str) -> SyntaxSession | None:
        """
        為一份文件開一個分析 session
        Open an analysis session for one document.

        :param language_id: 語言 ID / the language ID
        :return: 空的 session，不能分析這個語言時為 ``None``
            an empty session, or ``None`` when the language cannot be analysed
        """
        grammar = self._grammar(language_id)
        return None if grammar is None else TreeSitterSession(grammar)

    def _grammar(self, language_id: str) -> LoadedGrammar | None:
        """取得載入好的文法，載入失敗的只試一次 / The loaded grammar; a failed load is tried only once."""
        with self._lock:
            if language_id not in self._loaded:
                self._loaded[language_id] = self._load(language_id)
            return self._loaded[language_id]

    def _load(self, language_id: str) -> LoadedGrammar | None:
        """載入一個文法，載不起來時記錄原因 / Load a grammar, logging why when it will not load."""
        spec = self._specs.get(language_id)
        if spec is None:
            return None
        try:
            return load_grammar(spec, self._query_directory)
        except (ImportError, ValueError, OSError) as error:
            jeditor_logger.warning("syntax grammar %s is unavailable: %s", language_id, error)
            return None


@lru_cache(maxsize=1)
def shared_syntax_engine() -> TreeSitterEngine:
    """
    整個程序共用的語法引擎
    The syntax engine the whole process shares.

    載入好的文法是不會變的資料，沒有理由每個視窗各載一次；文件各自的狀態在 session
    裡，不在引擎裡。
    A loaded grammar is data that never changes, so there is no reason for every
    window to load its own. What belongs to a document lives in its session, not
    in the engine.

    :return: 內建文法的引擎 / the engine for the built-in grammars
    """
    return TreeSitterEngine()
