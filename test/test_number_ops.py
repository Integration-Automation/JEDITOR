"""Tests for number detection/adjustment and its editor command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.number_ops.number_ops import (
    adjust_number_at,
    find_number_at,
    parse_int,
    to_base,
)


class TestFindNumberAt:
    def test_inside_number(self):
        assert find_number_at("x = 42", 4) == (4, 6, 42)

    def test_just_past_number(self):
        assert find_number_at("42 items", 2) == (0, 2, 42)

    def test_not_on_number(self):
        assert find_number_at("hello", 1) is None

    def test_negative_number_with_sign(self):
        assert find_number_at("x = -5", 5) == (4, 6, -5)

    def test_minus_as_operator_is_excluded(self):
        # In "3-5" the minus is subtraction; the number at pos 2 is just 5.
        assert find_number_at("3-5", 2) == (2, 3, 5)

    def test_multi_digit(self):
        assert find_number_at("value1234end", 5) == (5, 9, 1234)

    def test_empty(self):
        assert find_number_at("", 0) is None

    def test_out_of_range_clamps_to_end(self):
        # A position past the end clamps to the end, landing just past "42".
        assert find_number_at("42", 99) == (0, 2, 42)

    def test_position_past_non_number_end(self):
        assert find_number_at("abc", 99) is None


class TestAdjustNumberAt:
    def test_increment(self):
        assert adjust_number_at("x = 42", 4, 1) == ("43", 4, 6)

    def test_decrement(self):
        assert adjust_number_at("x = 42", 4, -1) == ("41", 4, 6)

    def test_increment_negative(self):
        assert adjust_number_at("x = -1", 5, 1) == ("0", 4, 6)

    def test_not_on_number(self):
        assert adjust_number_at("hello", 1, 1) is None

    def test_large_delta(self):
        assert adjust_number_at("9", 0, 100) == ("109", 0, 1)


class TestParseInt:
    def test_plain_decimal(self):
        assert parse_int("42") == 42

    def test_hex_prefix(self):
        assert parse_int("0x2a") == 42

    def test_binary_prefix(self):
        assert parse_int("0b101010") == 42

    def test_octal_prefix(self):
        assert parse_int("0o52") == 42

    def test_leading_zero_decimal(self):
        # "08" is not valid with base 0 (looks octal) but falls back to base 10.
        assert parse_int("08") == 8

    def test_whitespace_ignored(self):
        assert parse_int("  42  ") == 42

    def test_invalid_returns_none(self):
        assert parse_int("hello") is None

    def test_empty_returns_none(self):
        assert parse_int("") is None


class TestToBase:
    def test_to_hex(self):
        assert to_base("42", 16) == "0x2a"

    def test_to_binary(self):
        assert to_base("42", 2) == "0b101010"

    def test_to_decimal_from_hex(self):
        assert to_base("0x2a", 10) == "42"

    def test_to_octal(self):
        assert to_base("42", 8) == "0o52"

    def test_invalid_input_returns_none(self):
        assert to_base("nope", 16) is None

    def test_unsupported_base_returns_none(self):
        assert to_base("42", 7) is None

    def test_round_trip(self):
        assert to_base(to_base("255", 16), 10) == "255"


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


def _caret(editor, position: int) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(position)
    editor.setTextCursor(cursor)


class TestEditorAdjustNumber:
    def test_increment_number(self, editor):
        editor.setPlainText("count = 41")
        _caret(editor, 8)
        assert editor.adjust_number(1) is True
        assert editor.toPlainText() == "count = 42"

    def test_decrement_number(self, editor):
        editor.setPlainText("count = 42")
        _caret(editor, 8)
        editor.adjust_number(-1)
        assert editor.toPlainText() == "count = 41"

    def test_not_on_number_is_noop(self, editor):
        editor.setPlainText("hello world")
        _caret(editor, 2)
        assert editor.adjust_number(1) is False
        assert editor.toPlainText() == "hello world"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("x = 5")
        _caret(editor, 4)
        editor.adjust_number(1)
        editor.undo()
        assert editor.toPlainText() == "x = 5"

    def test_caret_ends_after_number(self, editor):
        editor.setPlainText("x = 99")
        _caret(editor, 4)
        editor.adjust_number(1)  # 99 -> 100, width grows
        assert editor.textCursor().position() == 7  # end of "100"


def _select(editor, start: int, end: int) -> None:
    from PySide6.QtGui import QTextCursor
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestEditorNumberBase:
    def test_to_hex_selection(self, editor):
        editor.setPlainText("42")
        _select(editor, 0, 2)
        editor.number_to_hex_selection()
        assert editor.toPlainText() == "0x2a"

    def test_to_binary_selection(self, editor):
        editor.setPlainText("42")
        _select(editor, 0, 2)
        editor.number_to_binary_selection()
        assert editor.toPlainText() == "0b101010"

    def test_hex_to_decimal_selection(self, editor):
        editor.setPlainText("0x2a")
        _select(editor, 0, 4)
        editor.number_to_decimal_selection()
        assert editor.toPlainText() == "42"

    def test_invalid_number_is_noop(self, editor):
        editor.setPlainText("hello")
        _select(editor, 0, 5)
        editor.number_to_hex_selection()
        assert editor.toPlainText() == "hello"
