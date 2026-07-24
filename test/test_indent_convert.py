"""Tests for indentation conversion transforms and editor commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.indentation.indent_convert import (
    convert_leading_spaces_to_tabs,
    convert_leading_tabs_to_spaces,
    detect_indentation_uses_tabs,
)


class TestTabsToSpaces:
    def test_leading_tab_becomes_spaces(self):
        assert convert_leading_tabs_to_spaces("\tx = 1", tab_size=4) == "    x = 1"

    def test_two_tabs(self):
        assert convert_leading_tabs_to_spaces("\t\tx", tab_size=2) == "    x"

    def test_inline_tab_is_preserved(self):
        # A tab inside a string literal must not be converted.
        assert convert_leading_tabs_to_spaces("x = '\\t'", tab_size=4) == "x = '\\t'"

    def test_tab_stop_alignment(self):
        # "a" then tab -> tab advances to column 4, not +4.
        assert convert_leading_tabs_to_spaces(" \tx", tab_size=4) == "    x"

    def test_multiline(self):
        assert convert_leading_tabs_to_spaces("\ta\n\tb", tab_size=2) == "  a\n  b"

    def test_no_tabs_unchanged(self):
        assert convert_leading_tabs_to_spaces("    x = 1", tab_size=4) == "    x = 1"


class TestSpacesToTabs:
    def test_leading_spaces_become_tab(self):
        assert convert_leading_spaces_to_tabs("    x = 1", tab_size=4) == "\tx = 1"

    def test_partial_remainder_stays_spaces(self):
        assert convert_leading_spaces_to_tabs("      x", tab_size=4) == "\t  x"

    def test_inline_spaces_preserved(self):
        assert convert_leading_spaces_to_tabs("    a = b + c", tab_size=4) == "\ta = b + c"

    def test_no_leading_spaces_unchanged(self):
        assert convert_leading_spaces_to_tabs("x = 1", tab_size=4) == "x = 1"

    def test_round_trip_tabs_spaces_tabs(self):
        original = "\t\tx = 1"
        spaces = convert_leading_tabs_to_spaces(original, 4)
        assert convert_leading_spaces_to_tabs(spaces, 4) == original


class TestDetectIndentation:
    def test_detects_tabs(self):
        assert detect_indentation_uses_tabs("\tx\n\ty") is True

    def test_detects_spaces(self):
        assert detect_indentation_uses_tabs("    x\n    y") is False

    def test_no_indentation_returns_none(self):
        assert detect_indentation_uses_tabs("x\ny") is None

    def test_blank_lines_ignored(self):
        assert detect_indentation_uses_tabs("\n\n    x") is False

    def test_majority_wins(self):
        assert detect_indentation_uses_tabs("\tx\n    y\n\tz") is True


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


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


class TestEditorIndentCommands:
    def test_convert_to_spaces(self, editor):
        editor.setPlainText("\tx = 1\n\ty = 2")
        assert editor.convert_indentation_to_spaces(4) is True
        assert editor.toPlainText() == "    x = 1\n    y = 2"

    def test_convert_to_tabs(self, editor):
        editor.setPlainText("    x = 1\n    y = 2")
        assert editor.convert_indentation_to_tabs(4) is True
        assert editor.toPlainText() == "\tx = 1\n\ty = 2"

    def test_no_change_returns_false(self, editor):
        editor.setPlainText("x = 1")
        assert editor.convert_indentation_to_spaces(4) is False

    def test_convert_is_single_undo_step(self, editor):
        editor.setPlainText("\tx = 1")
        editor.convert_indentation_to_spaces(4)
        editor.undo()
        assert editor.toPlainText() == "\tx = 1"
