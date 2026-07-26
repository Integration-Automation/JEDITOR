"""Tests for highlighting languages other than Python."""
from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from je_editor.utils.syntax.language_rules import LANGUAGE_RULES, rules_for, supported_suffixes


class TestKeywordPattern:
    """
    All the keywords go into one alternation. Running a pattern per keyword cost
    four times as much per line, which a large file feels on open.
    """

    @staticmethod
    def _matches(pattern: str, text: str) -> list[str]:
        return re.findall(pattern, text)

    def test_a_keyword_matches(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        assert self._matches(keyword_pattern(("if", "else")), "if x") == ["if"]

    def test_every_keyword_is_covered(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        pattern = keyword_pattern(("if", "else", "return"))
        assert self._matches(pattern, "if a else return b") == ["if", "else", "return"]

    def test_a_keyword_inside_a_word_does_not_match(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        assert self._matches(keyword_pattern(("in",)), "printing") == []

    def test_a_longer_keyword_wins_over_its_prefix(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        pattern = keyword_pattern(("in", "instanceof"))
        assert self._matches(pattern, "a instanceof B") == ["instanceof"]

    def test_a_regex_character_in_a_keyword_is_literal(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        assert self._matches(keyword_pattern(("c++",)), "c++ code") == []

    def test_duplicates_do_not_repeat(self):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        assert keyword_pattern(("if", "if")).count("if") == 1

    @pytest.mark.parametrize("suffix", sorted(LANGUAGE_RULES))
    def test_every_language_builds_a_usable_pattern(self, suffix):
        from je_editor.pyside_ui.code.syntax.generic_syntax import keyword_pattern
        rules = rules_for(suffix)
        # A pattern that does not compile would break highlighting for the language.
        assert re.compile(keyword_pattern(rules.keywords)) is not None


class TestLanguageRules:
    @pytest.mark.parametrize("suffix", [".ts", ".js", ".rs", ".go", ".c", ".cpp", ".java"])
    def test_common_languages_have_rules(self, suffix):
        assert rules_for(suffix) is not None

    def test_python_is_left_to_its_own_highlighter(self):
        assert rules_for(".py") is None

    def test_suffix_matching_ignores_case(self):
        assert rules_for(".TS") is rules_for(".ts")

    def test_an_unknown_suffix_has_no_rules(self):
        assert rules_for(".unknown") is None

    def test_shell_uses_a_hash_comment_and_no_block(self):
        rules = rules_for(".sh")
        assert rules.line_comment == "#"
        assert rules.block_comment is None

    def test_sql_uses_a_double_dash_comment(self):
        assert rules_for(".sql").line_comment == "--"

    def test_template_literals_count_as_strings_in_js(self):
        assert "`" in rules_for(".js").string_delimiters

    def test_every_rule_set_names_its_language(self):
        assert all(rules.name for rules in LANGUAGE_RULES.values())

    def test_supported_suffixes_are_sorted(self):
        suffixes = supported_suffixes()
        assert list(suffixes) == sorted(suffixes)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _highlighted(suffix: str, text: str):
    """Return (highlighter, document) with *text* already highlighted."""
    from je_editor.pyside_ui.code.syntax.generic_syntax import highlighter_for
    document = QTextDocument()
    highlighter = highlighter_for(document, suffix)
    document.setPlainText(text)
    highlighter.rehighlight()
    return highlighter, document


def _formats_at(document: QTextDocument, line: int) -> list:
    block = document.findBlockByNumber(line)
    layout = block.layout()
    if layout is None:
        return []
    return [(fmt.start, fmt.length) for fmt in layout.formats()]


class TestGenericHighlighter:
    def test_a_keyword_is_coloured(self, app):
        highlighter, document = _highlighted(".ts", "const value = 1;")
        assert _formats_at(document, 0) != []
        highlighter.setDocument(None)

    def test_an_unknown_suffix_gets_no_highlighter(self, app):
        from je_editor.pyside_ui.code.syntax.generic_syntax import highlighter_for
        assert highlighter_for(QTextDocument(), ".unknown") is None

    def test_a_line_comment_is_coloured_to_the_end(self, app):
        line = "value := 1 // explain"
        highlighter, document = _highlighted(".go", line)
        assert any(start + length == len(line) for start, length in _formats_at(document, 0))
        highlighter.setDocument(None)

    def test_a_block_comment_spans_lines(self, app):
        highlighter, document = _highlighted(".c", "/* first\nstill inside\n*/ after")
        assert _formats_at(document, 1) != []
        highlighter.setDocument(None)

    def test_a_language_without_block_comments_is_safe(self, app):
        highlighter, document = _highlighted(".sh", "echo hi # comment\n")
        assert _formats_at(document, 0) != []
        highlighter.setDocument(None)

    def test_plain_text_gets_no_colouring(self, app):
        highlighter, document = _highlighted(".ts", "plainwords here\n")
        assert _formats_at(document, 0) == []
        highlighter.setDocument(None)

    def test_every_syntax_colour_is_defined(self, app):
        from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
            actually_color_dict
        )
        for key in (
            "syntax_keyword_color", "syntax_string_color",
            "syntax_comment_color", "syntax_number_color",
        ):
            assert actually_color_dict.get(key) is not None


@pytest.fixture()
def editor(app):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.close()
    code_editor.deleteLater()


class TestHighlighterSelection:
    def test_a_typescript_file_uses_the_generic_highlighter(self, editor):
        from je_editor.pyside_ui.code.syntax.generic_syntax import GenericHighlighter
        editor.current_file = "app.ts"
        editor.reset_highlighter()
        assert isinstance(editor.highlighter, GenericHighlighter)

    def test_a_python_file_keeps_its_own_highlighter(self, editor):
        from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
        editor.current_file = "module.py"
        editor.reset_highlighter()
        assert isinstance(editor.highlighter, PythonHighlighter)

    def test_an_unknown_suffix_falls_back_to_python(self, editor):
        from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
        editor.current_file = "notes.unknown"
        editor.reset_highlighter()
        assert isinstance(editor.highlighter, PythonHighlighter)

    def test_a_file_without_a_name_falls_back_to_python(self, editor):
        from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
        editor.current_file = None
        editor.reset_highlighter()
        assert isinstance(editor.highlighter, PythonHighlighter)
