"""
把符號清單組成大綱樹（純邏輯，不含 Qt）
Assemble a symbol list into an outline tree (pure logic, no Qt imports).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from je_editor.utils.symbols.python_symbols import QUALIFIED_SEPARATOR, SymbolInfo


@dataclass
class OutlineNode:
    """
    大綱樹的一個節點
    One node in the outline tree.

    :param symbol: 此節點對應的符號 / The symbol this node represents
    :param children: 巢狀於此節點下的子節點 / Child nodes nested under this one
    """

    symbol: SymbolInfo
    children: list["OutlineNode"] = field(default_factory=list)


def _parent_qualified_name(qualified_name: str) -> str | None:
    """取得上一層的限定名稱 / Return the enclosing scope's qualified name."""
    if QUALIFIED_SEPARATOR not in qualified_name:
        return None
    return qualified_name.rsplit(QUALIFIED_SEPARATOR, 1)[0]


def build_outline_tree(symbols: list[SymbolInfo]) -> list[OutlineNode]:
    """
    依限定名稱把符號組成巢狀大綱樹
    Nest symbols into an outline tree by their qualified names.

    方法會掛在其所屬類別之下，巢狀函式掛在外層函式之下。若某個符號的上層不存在
    （例如巢狀範圍內的模組層級變數不會發生，但防禦性處理），則視為根節點。
    A method nests under its class and a nested function under its outer function.
    A symbol whose parent scope is absent is treated as a root node.

    :param symbols: :func:`extract_python_symbols` 的結果 / Symbols to nest
    :return: 根節點清單，保持原本的行號順序 / Root nodes, keeping line order
    """
    nodes: dict[str, OutlineNode] = {}
    roots: list[OutlineNode] = []
    for symbol in symbols:
        node = OutlineNode(symbol=symbol)
        # 同名限定名稱重複時以最後一個為準，仍不會遺失任何節點的父子關聯
        # A duplicate qualified name keeps the latest; no node loses its linkage
        nodes[symbol.qualified_name] = node
        parent_name = _parent_qualified_name(symbol.qualified_name)
        parent = nodes.get(parent_name) if parent_name is not None else None
        if parent is None:
            roots.append(node)
        else:
            parent.children.append(node)
    return roots


def flatten_outline(nodes: list[OutlineNode]) -> list[SymbolInfo]:
    """
    以深度優先把大綱樹攤平回符號清單
    Flatten the outline tree back into a symbol list, depth-first.

    :param nodes: 大綱樹的根節點 / The outline tree roots
    :return: 依樹狀順序排列的符號 / Symbols in tree order
    """
    ordered: list[SymbolInfo] = []
    for node in nodes:
        ordered.append(node.symbol)
        ordered.extend(flatten_outline(node.children))
    return ordered
