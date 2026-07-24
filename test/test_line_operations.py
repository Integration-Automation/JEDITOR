"""Tests for pure line-operation transforms and their editor wiring."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.line_ops.line_operations import (
    delete_line,
    join_lines,
    natural_sort,
    natural_sort_key,
    remove_blank_lines,
    sort_lines,
    unique_lines,
)


class TestSortLines:
    def test_alphabetical(self):
        assert sort_lines(["banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]

    def test_reverse(self):
        assert sort_lines(["a", "c", "b"], reverse=True) == ["c", "b", "a"]

    def test_case_sensitive_default(self):
        # Uppercase sorts before lowercase by code point.
        assert sort_lines(["banana", "Apple"]) == ["Apple", "banana"]

    def test_case_insensitive(self):
        assert sort_lines(["banana", "Apple"], case_sensitive=False) == ["Apple", "banana"]

    def test_does_not_mutate_input(self):
        original = ["b", "a"]
        sort_lines(original)
        assert original == ["b", "a"]

    def test_empty(self):
        assert sort_lines([]) == []


class TestNaturalSort:
    def test_numbers_sort_numerically(self):
        assert natural_sort(["item10", "item2", "item1"]) == ["item1", "item2", "item10"]

    def test_falls_back_to_text(self):
        assert natural_sort(["banana", "apple"]) == ["apple", "banana"]

    def test_mixed(self):
        assert natural_sort(["a10", "a2", "b1"]) == ["a2", "a10", "b1"]

    def test_key_is_case_insensitive(self):
        assert natural_sort_key("Item2")[0] == "item"

    def test_does_not_mutate_input(self):
        original = ["b2", "b10"]
        natural_sort(original)
        assert original == ["b2", "b10"]


class TestRemoveBlankLines:
    def test_removes_empty_and_whitespace_lines(self):
        assert remove_blank_lines(["a", "", "  ", "b"]) == ["a", "b"]

    def test_keeps_content_lines(self):
        assert remove_blank_lines(["x", "y"]) == ["x", "y"]

    def test_all_blank_yields_empty(self):
        assert remove_blank_lines(["", "  ", "\t"]) == []


class TestUniqueLines:
    def test_removes_duplicates(self):
        assert unique_lines(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_preserves_first_order(self):
        assert unique_lines(["z", "a", "z"]) == ["z", "a"]

    def test_empty(self):
        assert unique_lines([]) == []


class TestJoinLines:
    def test_default_space(self):
        assert join_lines(["a", "b", "c"]) == "a b c"

    def test_strips_each_line(self):
        assert join_lines(["  a  ", "  b  "]) == "a b"

    def test_skips_blank_lines(self):
        assert join_lines(["a", "   ", "b"]) == "a b"

    def test_custom_separator(self):
        assert join_lines(["a", "b"], separator=", ") == "a, b"

    def test_all_blank_yields_empty(self):
        assert join_lines(["  ", ""]) == ""


class TestDeleteLine:
    def test_deletes_middle(self):
        assert delete_line(["a", "b", "c"], 1) == ["a", "c"]

    def test_out_of_range_returns_copy(self):
        original = ["a", "b"]
        result = delete_line(original, 5)
        assert result == ["a", "b"]
        assert result is not original

    def test_negative_index_returns_copy(self):
        assert delete_line(["a", "b"], -1) == ["a", "b"]

    def test_delete_only_line(self):
        assert delete_line(["only"], 0) == []


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


def _select_lines(editor, start_line: int, end_line: int) -> None:
    document = editor.document()
    cursor = editor.textCursor()
    cursor.setPosition(document.findBlockByNumber(start_line).position())
    end_block = document.findBlockByNumber(end_line)
    cursor.setPosition(
        end_block.position() + end_block.length() - 1, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestEditorLineOperations:
    def test_delete_current_line(self, editor):
        editor.setPlainText("aaa\nbbb\nccc")
        cursor = editor.textCursor()
        cursor.setPosition(editor.document().findBlockByNumber(1).position())
        editor.setTextCursor(cursor)
        editor.delete_current_line()
        assert editor.toPlainText() == "aaa\nccc"

    def test_delete_last_line(self, editor):
        editor.setPlainText("aaa\nbbb")
        cursor = editor.textCursor()
        cursor.setPosition(editor.document().findBlockByNumber(1).position())
        editor.setTextCursor(cursor)
        editor.delete_current_line()
        assert editor.toPlainText() == "aaa"

    def test_sort_selected_lines(self, editor):
        editor.setPlainText("cherry\napple\nbanana")
        _select_lines(editor, 0, 2)
        editor.sort_selected_lines()
        assert editor.toPlainText() == "apple\nbanana\ncherry"

    def test_sort_single_line_is_noop(self, editor):
        editor.setPlainText("only")
        editor.sort_selected_lines()
        assert editor.toPlainText() == "only"

    def test_join_selected_lines(self, editor):
        editor.setPlainText("a\nb\nc")
        _select_lines(editor, 0, 2)
        editor.join_selected_lines()
        assert editor.toPlainText() == "a b c"

    def test_delete_selection_removes_all_touched_lines(self, editor):
        editor.setPlainText("l0\nl1\nl2\nl3")
        _select_lines(editor, 1, 2)
        editor.delete_current_line()
        assert editor.toPlainText() == "l0\nl3"

    def test_line_ops_are_single_undo_steps(self, editor):
        editor.setPlainText("cherry\napple\nbanana")
        _select_lines(editor, 0, 2)
        editor.sort_selected_lines()
        editor.undo()
        assert editor.toPlainText() == "cherry\napple\nbanana"
