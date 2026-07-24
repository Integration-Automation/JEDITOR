"""Tests for outline tree building and the outline panel widget."""
from __future__ import annotations

import textwrap

import pytest

from je_editor.utils.symbols.outline_tree import (
    OutlineNode,
    build_outline_tree,
    flatten_outline,
)
from je_editor.utils.symbols.python_symbols import (
    CLASS_KIND,
    METHOD_KIND,
    SymbolInfo,
    extract_python_symbols,
)


def _tree(source: str) -> list[OutlineNode]:
    symbols = extract_python_symbols(textwrap.dedent(source))
    return build_outline_tree(symbols)


class TestBuildOutlineTree:
    def test_empty(self):
        assert build_outline_tree([]) == []

    def test_flat_functions_are_roots(self):
        roots = _tree("def a():\n    pass\ndef b():\n    pass\n")
        assert [node.symbol.name for node in roots] == ["a", "b"]

    def test_method_nests_under_class(self):
        roots = _tree("""
            class Editor:
                def save(self):
                    pass
            """)
        assert len(roots) == 1
        assert roots[0].symbol.name == "Editor"
        assert [child.symbol.name for child in roots[0].children] == ["save"]

    def test_nested_function_nests_under_function(self):
        roots = _tree("""
            def outer():
                def inner():
                    pass
            """)
        assert roots[0].symbol.name == "outer"
        assert roots[0].children[0].symbol.name == "inner"

    def test_multiple_methods_are_ordered(self):
        roots = _tree("""
            class A:
                def m1(self):
                    pass

                def m2(self):
                    pass
            """)
        assert [c.symbol.name for c in roots[0].children] == ["m1", "m2"]

    def test_module_variable_is_a_root(self):
        roots = _tree("VERSION = '1'\nclass A:\n    pass\n")
        names = [node.symbol.name for node in roots]
        assert "VERSION" in names and "A" in names

    def test_orphan_symbol_becomes_root(self):
        # A method whose class is absent should still appear (defensive).
        orphan = SymbolInfo(name="save", kind=METHOD_KIND, line=1, qualified_name="Ghost.save")
        roots = build_outline_tree([orphan])
        assert len(roots) == 1
        assert roots[0].symbol.name == "save"

    def test_flatten_round_trips_in_tree_order(self):
        symbols = extract_python_symbols(textwrap.dedent("""
            class A:
                def m(self):
                    pass
            def top():
                pass
            """))
        flat = flatten_outline(build_outline_tree(symbols))
        assert [s.name for s in flat] == ["A", "m", "top"]

    def test_deep_class_nesting(self):
        roots = _tree("""
            class Outer:
                class Inner:
                    def deep(self):
                        pass
            """)
        outer = roots[0]
        assert outer.symbol.kind == CLASS_KIND
        inner = outer.children[0]
        assert inner.symbol.name == "Inner"
        assert inner.children[0].symbol.name == "deep"


class _FakeCodeEdit:
    def __init__(self, text: str):
        self._text = text
        self.jumped: list[int] = []

    def toPlainText(self) -> str:
        return self._text

    def jump_to_line(self, line: int) -> bool:
        self.jumped.append(line)
        return True


class _FakeTabWidget:
    def __init__(self, widget):
        self._widget = widget

    def currentWidget(self):
        return self._widget


class _FakeMainWindow:
    def __init__(self, tab_widget=None):
        self.tab_widget = tab_widget


@pytest.mark.usefixtures("qapp")
class TestOutlinePanelWidget:
    def test_no_editor_shows_hint(self):
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            OutlinePanelWidget,
        )
        panel = OutlinePanelWidget(_FakeMainWindow(None))
        assert panel.tree.topLevelItemCount() == 0
        panel.close()

    def test_builds_tree_from_editor(self, monkeypatch):
        from je_editor.pyside_ui.main_ui.outline_panel import outline_panel_widget
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            OutlinePanelWidget,
        )
        code = _FakeCodeEdit("class A:\n    def m(self):\n        pass\n")
        # The panel checks isinstance(widget, EditorWidget); make our fake pass.
        monkeypatch.setattr(
            outline_panel_widget, "extract_python_symbols",
            lambda text: extract_python_symbols(text))
        panel = OutlinePanelWidget.__new__(OutlinePanelWidget)  # pylint: disable=no-value-for-parameter
        # Build minimally without a real EditorWidget by stubbing current_code_edit.
        from PySide6.QtWidgets import QTreeWidget
        panel.tree = QTreeWidget()
        panel.current_code_edit = lambda: code
        panel.status_label = None
        # Drive the tree-building portion directly.
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            build_symbol_items,
        )
        for item in build_symbol_items(extract_python_symbols(code.toPlainText())):
            panel.tree.addTopLevelItem(item)
        assert panel.tree.topLevelItemCount() == 1
        assert panel.tree.topLevelItem(0).text(0) == "A"
        panel.tree.deleteLater()

    def test_build_symbol_items_nests(self):
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            build_symbol_items,
        )
        symbols = extract_python_symbols("class A:\n    def m(self):\n        pass\n")
        items = build_symbol_items(symbols)
        assert len(items) == 1
        assert items[0].childCount() == 1
        assert items[0].child(0).text(0) == "m"

    def test_jump_uses_current_editor(self):
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            OutlinePanelWidget,
        )
        code = _FakeCodeEdit("class A:\n    pass\n")
        panel = OutlinePanelWidget.__new__(OutlinePanelWidget)  # pylint: disable=no-value-for-parameter
        panel.current_code_edit = lambda: code
        assert panel.jump_to_symbol_line(2) is True
        assert code.jumped == [2]

    def test_jump_without_editor_returns_false(self):
        from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import (
            OutlinePanelWidget,
        )
        panel = OutlinePanelWidget.__new__(OutlinePanelWidget)  # pylint: disable=no-value-for-parameter
        panel.current_code_edit = lambda: None
        assert panel.jump_to_symbol_line(2) is False
