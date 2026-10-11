"""
語法分析結果的模型，以及語法引擎的介面
What syntax analysis yields, and the interface of the engine that produces it.

編輯器要的是「這一行哪幾段是字串、哪幾段是關鍵字」以及「這份文件有哪些類別、函式
與區塊」，而不是語法樹本身。這裡只定義這兩種答案與取得它們的介面；用什麼解析器、
樹長什麼樣子，是轉接器的事，畫面層看不到。
An editor wants to know which parts of a line are a string or a keyword, and
which classes, functions and blocks a document has. It does not want the syntax
tree. Only those two answers and the way to ask for them are defined here; which
parser is used and what its tree looks like is the adapter's business, and the
widgets never see it.

行號與欄號跟診斷模型一樣從 1 起算。欄號以 UTF-16 的單位計，也就是 Qt 與語言伺服器
協定用的單位，所以一個 emoji 佔兩欄。
Lines and columns are 1-based, as in the diagnostics model. A column counts
UTF-16 units, which is what Qt and the language server protocol count, so an
emoji takes two.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from je_editor.core.diagnostics.diagnostic_model import TextRange


class SyntaxCategory(Enum):
    """
    一段文字在語法上是什麼
    What a piece of text is, syntactically.

    分類只說「是什麼」，不說「什麼顏色」；顏色由畫面層依主題決定，沒有顏色的分類
    照樣回報，內層的插值才蓋得掉外層字串的顏色。
    A category says what something is, never what colour it has: the widgets pick
    colours from the theme. Categories that get no colour are reported all the
    same, which is how an interpolation resets the colour of the string around it.
    """

    COMMENT = "comment"
    STRING = "string"
    ESCAPE = "escape"
    NUMBER = "number"
    KEYWORD = "keyword"
    OPERATOR = "operator"
    PUNCTUATION = "punctuation"
    FUNCTION = "function"
    BUILTIN = "builtin"
    TYPE = "type"
    CONSTANT = "constant"
    LITERAL = "literal"
    VARIABLE = "variable"
    SPECIAL_VARIABLE = "special_variable"
    PROPERTY = "property"
    KEY = "key"
    EMBEDDED = "embedded"


@dataclass(frozen=True)
class SyntaxSpan:
    """
    一行裡屬於同一個分類的一段
    A stretch of one line that belongs to one category.

    :param column: 1 起算的起始欄 / the 1-based column it starts at
    :param length: 長度，UTF-16 單位 / its length in UTF-16 units
    :param category: 分類 / the category
    """

    column: int
    length: int
    category: SyntaxCategory


@dataclass(frozen=True)
class LineSpan:
    """
    連續的幾行，頭尾都包含
    A run of lines, both ends included.

    :param first: 1 起算的第一行 / the 1-based first line
    :param last: 最後一行 / the last line
    """

    first: int
    last: int


class RegionKind(Enum):
    """
    結構區塊的種類
    The kinds of structural region.
    """

    CLASS = "class"
    FUNCTION = "function"
    BLOCK = "block"
    COLLECTION = "collection"


@dataclass(frozen=True)
class StructuralRegion:
    """
    文件裡的一個結構區塊：類別、函式、控制流程區塊或集合字面值
    One structural region of a document: a class, a function, a control-flow
    block or a collection literal.

    :param kind: 種類 / its kind
    :param range: 涵蓋的範圍 / the range it covers
    :param name: 名稱，沒有名稱時為空字串 / its name, empty when it has none
    """

    kind: RegionKind
    range: TextRange
    name: str = ""

    @property
    def is_multiline(self) -> bool:
        """是否跨越一行以上，也就是能不能摺疊 / Whether it spans lines, and so can fold."""
        return self.range.end.line > self.range.start.line


@runtime_checkable
class SyntaxSession(Protocol):
    """
    一份文件的語法分析，文字每變一次就更新一次
    The syntax analysis of one document, brought up to date as its text changes.

    一個 session 只屬於一份文件，也只在擁有那份文件的執行緒上使用。
    A session belongs to one document and is used only on the thread that owns
    that document.
    """

    @property
    def language_id(self) -> str:
        """這個 session 解析的語言 / The language this session parses."""

    @property
    def has_errors(self) -> bool:
        """目前的文字是否有語法錯誤 / Whether the current text has a syntax error."""

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

    def spans(self, line: int) -> tuple[SyntaxSpan, ...]:
        """
        取得一行的分類
        The categories of one line.

        外層的在前、內層的在後，所以照順序套用時內層會蓋過外層。
        Outer spans come before the spans inside them, so applying them in order
        lets the inner ones win.

        :param line: 1 起算的行號 / the 1-based line
        :return: 那一行的每一段；行號不存在時為空
            the spans on that line, none when there is no such line
        """

    def regions(self) -> tuple[StructuralRegion, ...]:
        """
        取得文件的結構區塊
        The structural regions of the document.

        :return: 依起點排序，外層的在前 / ordered by start, outer regions first
        """


@runtime_checkable
class SyntaxEngine(Protocol):
    """
    能分析某些語言的語法引擎
    A syntax engine that can analyse some languages.
    """

    def language_ids(self) -> tuple[str, ...]:
        """
        這個引擎目前能分析的語言
        The languages this engine can analyse right now.

        :return: 語言 ID，例如 ``python`` / language IDs such as ``python``
        """

    def language_for(self, file_name: str) -> str | None:
        """
        依檔名判斷語言
        The language of a file, going by its name.

        :param file_name: 檔名、路徑或 URI / a file name, path or URI
        :return: 語言 ID，引擎不認得時為 ``None``
            the language ID, or ``None`` when the engine does not know it
        """

    def open_session(self, language_id: str) -> SyntaxSession | None:
        """
        為一份文件開一個分析 session
        Open an analysis session for one document.

        :param language_id: 語言 ID / the language ID
        :return: 空的 session，引擎不能分析這個語言時為 ``None``
            an empty session, or ``None`` when the engine cannot analyse it
        """


class NoSyntaxEngine:
    """
    什麼語言都不會的引擎，是還沒有接上解析器時的預設值
    An engine that knows no language: the default until a parser is plugged in.
    """

    def language_ids(self) -> tuple[str, ...]:
        """沒有任何語言 / No languages at all."""
        return ()

    def language_for(self, file_name: str) -> str | None:
        """
        任何檔名都不認得
        No file name is recognised.

        :param file_name: 檔名 / the file name
        :return: 一律為 ``None`` / always ``None``
        """
        del file_name
        return None

    def open_session(self, language_id: str) -> SyntaxSession | None:
        """
        不開任何 session
        No session is ever opened.

        :param language_id: 語言 ID / the language ID
        :return: 一律為 ``None`` / always ``None``
        """
        del language_id
        return None
