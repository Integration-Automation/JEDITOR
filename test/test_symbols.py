"""Tests for Python symbol extraction and the go-to-symbol picker."""
from __future__ import annotations


import textwrap

import pytest

from je_editor.pyside_ui.main_ui.command_palette.go_to_symbol_dialog import (
    build_symbol_entries,
    make_symbol_jumper,
)
from je_editor.utils.symbols.outline_tree import build_outline_tree
from je_editor.utils.symbols.python_symbols import (
    CLASS_KIND,
    FUNCTION_KIND,
    METHOD_KIND,
    VARIABLE_KIND,
    SymbolInfo,
    extract_python_symbols,
    symbols_from_server,
)


class TestSymbolsFromServer:
    """
    The outline only ever parsed Python, so every other language showed nothing.
    A language server reports the same thing for the languages it handles.
    """

    def test_a_symbol_keeps_its_name_and_line(self):
        symbols = symbols_from_server([{"name": "main", "kind": 12, "line": 4, "depth": 0}])
        assert (symbols[0].name, symbols[0].line) == ("main", 4)

    def test_a_known_kind_is_named(self):
        symbols = symbols_from_server([{"name": "Thing", "kind": 5, "line": 1, "depth": 0}])
        assert symbols[0].kind == "class"

    def test_an_unknown_kind_falls_back(self):
        symbols = symbols_from_server([{"name": "x", "kind": 99, "line": 1, "depth": 0}])
        assert symbols[0].kind == "variable"

    def test_nesting_becomes_a_qualified_name(self):
        symbols = symbols_from_server([
            {"name": "Thing", "kind": 5, "line": 1, "depth": 0},
            {"name": "method", "kind": 6, "line": 2, "depth": 1},
        ])
        assert symbols[1].qualified_name == "Thing.method"

    def test_returning_to_the_top_level_drops_the_enclosing_name(self):
        symbols = symbols_from_server([
            {"name": "Thing", "kind": 5, "line": 1, "depth": 0},
            {"name": "method", "kind": 6, "line": 2, "depth": 1},
            {"name": "helper", "kind": 12, "line": 9, "depth": 0},
        ])
        assert symbols[2].qualified_name == "helper"

    def test_the_outline_nests_them(self):
        roots = build_outline_tree(symbols_from_server([
            {"name": "Thing", "kind": 5, "line": 1, "depth": 0},
            {"name": "method", "kind": 6, "line": 2, "depth": 1},
        ]))
        assert len(roots) == 1 and roots[0].children[0].symbol.name == "method"

    def test_an_entry_without_a_name_is_skipped(self):
        assert symbols_from_server([{"kind": 12, "line": 1, "depth": 0}]) == []

    def test_nothing_reported_gives_nothing(self):
        assert symbols_from_server([]) == []

    def test_a_line_below_one_is_clamped(self):
        assert symbols_from_server([{"name": "x", "line": 0, "depth": 0}])[0].line == 1


def _symbols(source: str) -> list[SymbolInfo]:
    return extract_python_symbols(textwrap.dedent(source))


class TestExtractPythonSymbols:
    """AST-based symbol extraction."""

    def test_empty_source_yields_nothing(self):
        assert extract_python_symbols("") == []

    def test_syntax_error_yields_nothing(self):
        # A half-typed file must not raise while the user is editing.
        assert extract_python_symbols("def broken(:\n") == []

    def test_finds_module_level_function(self):
        found = _symbols("def run():\n    pass\n")
        assert (found[0].name, found[0].kind, found[0].line) == ("run", FUNCTION_KIND, 1)

    def test_finds_class(self):
        found = _symbols("class Editor:\n    pass\n")
        assert (found[0].name, found[0].kind) == ("Editor", CLASS_KIND)

    def test_class_body_function_is_a_method(self):
        found = _symbols("""
            class Editor:
                def save(self):
                    pass
            """)
        method = [symbol for symbol in found if symbol.name == "save"][0]
        assert method.kind == METHOD_KIND

    def test_method_qualified_name_includes_class(self):
        found = _symbols("""
            class Editor:
                def save(self):
                    pass
            """)
        method = [symbol for symbol in found if symbol.name == "save"][0]
        assert method.qualified_name == "Editor.save"

    def test_async_method_is_collected(self):
        found = _symbols("""
            class Client:
                async def fetch(self):
                    pass
            """)
        assert [symbol.name for symbol in found] == ["Client", "fetch"]

    def test_nested_function_is_a_function_not_a_method(self):
        found = _symbols("""
            class Editor:
                def save(self):
                    def helper():
                        pass
            """)
        helper = [symbol for symbol in found if symbol.name == "helper"][0]
        assert helper.kind == FUNCTION_KIND

    def test_nested_function_qualified_name(self):
        found = _symbols("""
            class Editor:
                def save(self):
                    def helper():
                        pass
            """)
        helper = [symbol for symbol in found if symbol.name == "helper"][0]
        assert helper.qualified_name == "Editor.save.helper"

    def test_class_nested_in_function_still_yields_methods(self):
        found = _symbols("""
            def factory():
                class Inner:
                    def run(self):
                        pass
            """)
        run = [symbol for symbol in found if symbol.name == "run"][0]
        assert run.kind == METHOD_KIND

    def test_module_level_assignment_is_collected(self):
        found = _symbols("VERSION = '1.0'\n")
        assert (found[0].name, found[0].kind) == ("VERSION", VARIABLE_KIND)

    def test_annotated_module_level_assignment_is_collected(self):
        found = _symbols("VERSION: str = '1.0'\n")
        assert (found[0].name, found[0].kind) == ("VERSION", VARIABLE_KIND)

    def test_local_variables_are_not_collected(self):
        found = _symbols("""
            def run():
                local_value = 1
            """)
        assert [symbol.name for symbol in found] == ["run"]

    def test_class_attributes_are_not_collected(self):
        found = _symbols("""
            class Editor:
                attribute = 1
            """)
        assert [symbol.name for symbol in found] == ["Editor"]

    def test_symbols_are_ordered_by_line(self):
        found = _symbols("""
            def first():
                pass

            def second():
                pass
            """)
        assert [symbol.line for symbol in found] == sorted(symbol.line for symbol in found)

    def test_multiple_targets_in_one_assignment(self):
        found = _symbols("FIRST = SECOND = 1\n")
        assert {symbol.name for symbol in found} == {"FIRST", "SECOND"}


class _FakeCodeEdit:
    """Records the lines go-to-symbol asked to jump to."""

    def __init__(self):
        self.jumped: list[int] = []

    def jump_to_line(self, line: int) -> bool:
        self.jumped.append(line)
        return True


class TestSymbolJumper:
    """The jump closure must survive the dialog it came from."""

    def test_jump_forwards_the_line(self):
        editor = _FakeCodeEdit()
        make_symbol_jumper(editor, 12)()
        assert editor.jumped == [12]

    def test_jump_tolerates_no_editor(self):
        make_symbol_jumper(None, 12)()

    def test_jump_tolerates_editor_without_the_api(self):
        make_symbol_jumper(object(), 12)()


class TestBuildSymbolEntries:
    """Entry shaping for the fuzzy picker."""

    @staticmethod
    def _entry():
        symbol = SymbolInfo(name="save", kind=METHOD_KIND, line=7, qualified_name="Editor.save")
        return build_symbol_entries([symbol], _FakeCodeEdit())[0]

    def test_title_is_the_symbol_name(self):
        assert self._entry().title == "save"

    def test_path_shows_kind_qualified_name_and_line(self):
        path = self._entry().path
        assert METHOD_KIND in path and "Editor.save" in path and ":7" in path

    def test_payload_jumps_to_the_symbol_line(self):
        editor = _FakeCodeEdit()
        symbol = SymbolInfo(name="save", kind=METHOD_KIND, line=7, qualified_name="Editor.save")
        build_symbol_entries([symbol], editor)[0].payload()
        assert editor.jumped == [7]

    def test_empty_symbol_list_yields_no_entries(self):
        assert build_symbol_entries([], _FakeCodeEdit()) == []


@pytest.mark.usefixtures("qapp")
class TestGoToSymbolPicker:
    """End-to-end filtering through the shared picker dialog."""

    def test_typing_filters_to_one_symbol(self):
        from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import (
            CommandPaletteDialog
        )
        symbols = _symbols("""
            class Editor:
                def save(self):
                    pass

                def load(self):
                    pass
            """)
        dialog = CommandPaletteDialog(None, build_symbol_entries(symbols, _FakeCodeEdit()))
        dialog.search_input.setText("save")
        assert dialog.result_list.count() == 1
        dialog.close()
