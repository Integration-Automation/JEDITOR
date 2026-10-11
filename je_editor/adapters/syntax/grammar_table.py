"""
內建的 Tree-sitter 文法，以及查詢名稱到語法分類的對照
The built-in Tree-sitter grammars, and the mapping from capture names to categories.

多支援一種語言就是在這裡加一列、在 ``queries/<語言>/`` 放查詢檔，引擎與畫面層都
不用改。
Supporting one more language is a row here and query files under
``queries/<language>/``; neither the engine nor the widgets change.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from je_editor.core.syntax.syntax_model import SyntaxCategory

# 專案自己的查詢檔放在這裡 / Where the project's own query files live
QUERY_DIRECTORY = Path(__file__).parent / "queries"
# 接在文法自帶的高亮查詢之後 / Appended to the highlight query the grammar ships
HIGHLIGHTS_QUERY_FILE = "highlights.scm"
# 結構區塊的查詢 / The query for structural regions
REGIONS_QUERY_FILE = "regions.scm"


@dataclass(frozen=True)
class GrammarSpec:
    """
    一種語言的文法從哪裡來
    Where the grammar of one language comes from.

    :param language_id: 語言 ID / the language ID
    :param suffixes: 屬於這個語言的副檔名，小寫、含點
        the file suffixes of the language, lower case and with the dot
    :param load: 匯入文法套件並回傳它 / imports the grammar package and returns it
    """

    language_id: str
    suffixes: tuple[str, ...]
    load: Callable[[], ModuleType]


def _load_python() -> ModuleType:
    """匯入 Python 的文法 / Import the Python grammar."""
    import tree_sitter_python
    return tree_sitter_python


def _load_javascript() -> ModuleType:
    """匯入 JavaScript 的文法 / Import the JavaScript grammar."""
    import tree_sitter_javascript
    return tree_sitter_javascript


def _load_json() -> ModuleType:
    """匯入 JSON 的文法 / Import the JSON grammar."""
    import tree_sitter_json
    return tree_sitter_json


BUILTIN_GRAMMARS: tuple[GrammarSpec, ...] = (
    GrammarSpec("python", (".py", ".pyw", ".pyi"), _load_python),
    GrammarSpec("javascript", (".js", ".mjs", ".cjs", ".jsx"), _load_javascript),
    GrammarSpec("json", (".json",), _load_json),
)

# 查詢裡的名稱是有層次的（``function.builtin``）；找不到完整名稱時退回上一層。
# Capture names are hierarchical (``function.builtin``): a name with no entry of
# its own falls back to its parent.
CAPTURE_CATEGORIES: dict[str, SyntaxCategory] = {
    "comment": SyntaxCategory.COMMENT,
    "string": SyntaxCategory.STRING,
    "string.special.key": SyntaxCategory.KEY,
    "string.escape": SyntaxCategory.ESCAPE,
    "escape": SyntaxCategory.ESCAPE,
    "number": SyntaxCategory.NUMBER,
    "float": SyntaxCategory.NUMBER,
    "boolean": SyntaxCategory.LITERAL,
    "keyword": SyntaxCategory.KEYWORD,
    "operator": SyntaxCategory.OPERATOR,
    "punctuation": SyntaxCategory.PUNCTUATION,
    "function": SyntaxCategory.FUNCTION,
    "function.builtin": SyntaxCategory.BUILTIN,
    "method": SyntaxCategory.FUNCTION,
    "constructor": SyntaxCategory.TYPE,
    "type": SyntaxCategory.TYPE,
    "constant": SyntaxCategory.CONSTANT,
    "constant.builtin": SyntaxCategory.LITERAL,
    "variable": SyntaxCategory.VARIABLE,
    "variable.builtin": SyntaxCategory.SPECIAL_VARIABLE,
    "property": SyntaxCategory.PROPERTY,
    "attribute": SyntaxCategory.PROPERTY,
    "embedded": SyntaxCategory.EMBEDDED,
}


def category_for(capture_name: str) -> SyntaxCategory | None:
    """
    找出一個查詢名稱對應的語法分類
    The category a capture name stands for.

    :param capture_name: 查詢裡的名稱，例如 ``function.builtin``
        the name in the query, such as ``function.builtin``
    :return: 分類；這個名稱與它的每一層上層都沒有對應時為 ``None``
        the category, or ``None`` when neither the name nor any parent has one
    """
    name = capture_name
    while name:
        category = CAPTURE_CATEGORIES.get(name)
        if category is not None:
            return category
        name = name.rpartition(".")[0]
    return None


def own_query(directory: Path, language_id: str, file_name: str) -> str:
    """
    讀出專案為某個語言準備的查詢檔
    Read the query file the project keeps for a language.

    :param directory: 查詢檔的根目錄 / the directory holding the query files
    :param language_id: 語言 ID / the language ID
    :param file_name: 查詢檔名 / the query file's name
    :return: 查詢內容，沒有這個檔案時為空字串 / the query, empty when there is no such file
    """
    path = directory / language_id / file_name
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
