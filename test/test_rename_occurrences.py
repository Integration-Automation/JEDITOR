"""Tests for whole-word replace and the in-file rename command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.occurrence.word_occurrences import replace_whole_word


class TestReplaceWholeWord:
    def test_replaces_all_occurrences(self):
        assert replace_whole_word("x = x + x", "x", "y") == "y = y + y"

    def test_whole_word_only(self):
        assert replace_whole_word("value values old_value", "value", "v") == "v values old_value"

    def test_no_match_unchanged(self):
        assert replace_whole_word("abc def", "xyz", "q") == "abc def"

    def test_non_identifier_word_unchanged(self):
        assert replace_whole_word("a.b a.b", "a.b", "q") == "a.b a.b"

    def test_replacement_backslashes_are_literal(self):
        # A replacement containing backslashes must not be treated as backrefs.
        assert replace_whole_word("path", "path", r"a\1b") == r"a\1b"

    def test_multiline(self):
        assert replace_whole_word("foo\nfoo\nbar", "foo", "baz") == "baz\nbaz\nbar"

    def test_replacement_equal_creates_no_change(self):
        assert replace_whole_word("foo", "foo", "foo") == "foo"


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


class TestEditorRename:
    @staticmethod
    def _patch_dialog(new_word, accepted=True):
        return patch(
            "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.QInputDialog.getText",
            return_value=(new_word, accepted),
        )

    def test_rename_all_occurrences(self, editor):
        editor.setPlainText("total = total + 1\nprint(total)")
        _caret(editor, 0)
        with self._patch_dialog("count"):
            assert editor.rename_word_under_cursor() is True
        assert editor.toPlainText() == "count = count + 1\nprint(count)"

    def test_rename_is_single_undo_step(self, editor):
        editor.setPlainText("x = x")
        _caret(editor, 0)
        with self._patch_dialog("y"):
            editor.rename_word_under_cursor()
        editor.undo()
        assert editor.toPlainText() == "x = x"

    def test_cancelled_dialog_is_noop(self, editor):
        editor.setPlainText("x = x")
        _caret(editor, 0)
        with self._patch_dialog("y", accepted=False):
            assert editor.rename_word_under_cursor() is False
        assert editor.toPlainText() == "x = x"

    def test_same_name_is_noop(self, editor):
        editor.setPlainText("x = x")
        _caret(editor, 0)
        with self._patch_dialog("x"):
            assert editor.rename_word_under_cursor() is False

    def test_empty_name_is_noop(self, editor):
        editor.setPlainText("x = x")
        _caret(editor, 0)
        with self._patch_dialog("   "):
            assert editor.rename_word_under_cursor() is False

    def test_not_on_identifier_is_noop(self, editor):
        editor.setPlainText("+ + +")
        _caret(editor, 0)
        assert editor.rename_word_under_cursor() is False

    def test_only_whole_words_renamed(self, editor):
        editor.setPlainText("val = value + val")
        _caret(editor, 0)  # caret on "val"
        with self._patch_dialog("v"):
            editor.rename_word_under_cursor()
        assert editor.toPlainText() == "v = value + v"
