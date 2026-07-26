"""
從 Python 原始碼萃取符號（純邏輯，不含 Qt）
Extract symbols from Python source (pure logic, no Qt imports).

使用標準函式庫的 ``ast``，不執行任何使用者程式碼。
Built on the standard library ``ast`` module, so user code is never executed.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

# 符號種類 / Symbol kinds
CLASS_KIND = "class"
FUNCTION_KIND = "function"
METHOD_KIND = "method"
VARIABLE_KIND = "variable"

# 限定名稱的分隔字元 / Separator used in qualified names
QUALIFIED_SEPARATOR = "."

# LSP 的 SymbolKind 編號對應的種類名稱；只列大綱看得到的那幾種
# The kind name for each LSP SymbolKind number, for the ones an outline shows
SERVER_SYMBOL_KINDS: dict[int, str] = {
    5: CLASS_KIND, 6: METHOD_KIND, 9: METHOD_KIND, 11: CLASS_KIND,
    12: FUNCTION_KIND, 13: VARIABLE_KIND, 14: VARIABLE_KIND, 23: CLASS_KIND,
}
# 認不得的種類 / What an unrecognised kind is called
SERVER_SYMBOL_FALLBACK = VARIABLE_KIND


@dataclass(frozen=True)
class SymbolInfo:
    """
    原始碼中的一個符號
    One symbol found in a source file.

    :param name: 符號名稱 / The symbol name
    :param kind: 符號種類，例如 ``class`` 或 ``method`` / The kind, e.g. ``class``
    :param line: 1 起算的行號 / The 1-based line number
    :param qualified_name: 含外層範圍的完整名稱 / The name including enclosing scopes
    """

    name: str
    kind: str
    line: int
    qualified_name: str


def symbols_from_server(entries: list) -> list[SymbolInfo]:
    """
    把語言伺服器回報的符號轉成大綱用的形式
    Turn the symbols a language server reported into what the outline draws.

    伺服器給的是「名稱、種類、行號、巢狀深度」，大綱靠限定名稱決定巢狀關係，因此
    這裡依深度維護一個外層名稱的堆疊，把限定名稱組回來。
    A server gives a name, a kind, a line and a nesting depth, while the outline
    nests by qualified name, so this keeps a stack of enclosing names by depth and
    rebuilds the qualified name from it.

    :param entries: ``{"name", "kind", "line", "depth"}`` 的清單 / the reported symbols
    :return: 大綱用的符號 / the symbols the outline draws
    """
    symbols: list[SymbolInfo] = []
    enclosing: list[str] = []
    for entry in entries or []:
        name = str(entry.get("name", "")).strip()
        if not name:
            continue
        depth = max(0, int(entry.get("depth", 0) or 0))
        del enclosing[depth:]
        qualified = QUALIFIED_SEPARATOR.join([*enclosing, name])
        enclosing.append(name)
        symbols.append(SymbolInfo(
            name=name,
            kind=SERVER_SYMBOL_KINDS.get(entry.get("kind"), SERVER_SYMBOL_FALLBACK),
            line=max(1, int(entry.get("line", 1) or 1)),
            qualified_name=qualified,
        ))
    return symbols


class _SymbolCollector(ast.NodeVisitor):
    """走訪語法樹並收集符號 / Walk the AST and collect symbols."""

    def __init__(self) -> None:
        self.symbols: list[SymbolInfo] = []
        self._scope: list[str] = []
        # 是否位於類別內，用來區分 function 與 method
        # Whether we are inside a class, which separates functions from methods
        self._class_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add(node.name, CLASS_KIND, node.lineno)
        self._scope.append(node.name)
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # 只收模組層級的指派，避免區域變數把清單淹沒
        # Only module-level assignments, so local variables cannot flood the list
        if not self._scope:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._add(target.id, VARIABLE_KIND, target.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if not self._scope and isinstance(node.target, ast.Name):
            self._add(node.target.id, VARIABLE_KIND, node.target.lineno)
        self.generic_visit(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """類別內的函式視為 method / A function inside a class counts as a method."""
        kind = METHOD_KIND if self._class_depth > 0 else FUNCTION_KIND
        self._add(node.name, kind, node.lineno)
        self._scope.append(node.name)
        # 函式內的巢狀類別不應讓其方法被誤判，class_depth 由 visit_ClassDef 維護
        # Nested classes keep their own depth via visit_ClassDef
        previous_class_depth = self._class_depth
        self._class_depth = 0
        self.generic_visit(node)
        self._class_depth = previous_class_depth
        self._scope.pop()

    def _add(self, name: str, kind: str, line: int) -> None:
        """記錄一個符號 / Record one symbol."""
        qualified = QUALIFIED_SEPARATOR.join([*self._scope, name])
        self.symbols.append(
            SymbolInfo(name=name, kind=kind, line=line, qualified_name=qualified))


def extract_python_symbols(source: str) -> list[SymbolInfo]:
    """
    從 Python 原始碼萃取類別、函式、方法與模組層級變數
    Extract classes, functions, methods and module-level variables from source.

    語法錯誤的檔案會回傳空清單，讓呼叫端在使用者仍在編輯時不會出錯。
    A file that fails to parse yields an empty list, so callers stay usable while
    the user is still typing.

    :param source: Python 原始碼 / The Python source text
    :return: 依行號排序的符號清單 / Symbols ordered by line number
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return []
    collector = _SymbolCollector()
    collector.visit(tree)
    collector.symbols.sort(key=lambda symbol: (symbol.line, symbol.qualified_name))
    return collector.symbols
