"""Tests for hover, rename and formatting through the language server."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.lsp.lsp_protocol import file_uri, hover_text, text_edits


class TestHoverText:
    def test_plain_string_contents(self):
        assert hover_text({"contents": "a function"}) == "a function"

    def test_marked_string_contents(self):
        assert hover_text({"contents": {"value": "def run()"}}) == "def run()"

    def test_a_list_joins_every_part(self):
        text = hover_text({"contents": ["first", {"value": "second"}]})
        assert text == "first\nsecond"

    def test_empty_parts_are_dropped(self):
        assert hover_text({"contents": ["  ", {"value": ""}]}) == ""

    def test_unusable_result(self):
        assert hover_text(None) == ""
        assert hover_text({"other": 1}) == ""


class TestTextEdits:
    def test_formatting_returns_a_plain_list(self):
        edits = text_edits([{
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 3}},
            "newText": "xyz",
        }])
        assert edits == [{
            "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 4,
            "new_text": "xyz"}]

    def test_rename_returns_changes_keyed_by_uri(self):
        uri = file_uri("/project/app.ts")
        edits = text_edits({"changes": {uri: [{
            "range": {"start": {"line": 2, "character": 4}, "end": {"line": 2, "character": 9}},
            "newText": "renamed",
        }]}}, uri)
        assert edits[0]["new_text"] == "renamed"
        assert edits[0]["start_line"] == 3

    def test_rename_falls_back_to_the_only_file_present(self):
        edits = text_edits({"changes": {"file:///other.ts": [{
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
            "newText": "z",
        }]}}, "file:///not-there.ts")
        assert len(edits) == 1

    def test_document_changes_form(self):
        edits = text_edits({"documentChanges": [{"edits": [{
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 2}},
            "newText": "ab",
        }]}]})
        assert edits[0]["new_text"] == "ab"

    def test_entries_without_a_range_are_skipped(self):
        assert text_edits([{"newText": "x"}]) == []

    def test_unusable_result(self):
        assert text_edits(None) == []
        assert text_edits({"unexpected": True}) == []


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


class TestApplyingEdits:
    def test_a_single_edit_replaces_its_range(self, editor):
        editor.setPlainText("old value\n")
        assert editor.apply_server_edits([{
            "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 4,
            "new_text": "new"}]) is True
        assert editor.toPlainText() == "new value\n"

    def test_several_edits_do_not_disturb_each_other(self, editor):
        editor.setPlainText("aaa bbb ccc\n")
        editor.apply_server_edits([
            {"start_line": 1, "start_column": 1, "end_line": 1, "end_column": 4,
             "new_text": "111"},
            {"start_line": 1, "start_column": 9, "end_line": 1, "end_column": 12,
             "new_text": "333"},
        ])
        assert editor.toPlainText() == "111 bbb 333\n"

    def test_edits_of_different_lengths_still_land_correctly(self, editor):
        editor.setPlainText("one two\n")
        editor.apply_server_edits([
            {"start_line": 1, "start_column": 1, "end_line": 1, "end_column": 4,
             "new_text": "a-much-longer-word"},
            {"start_line": 1, "start_column": 5, "end_line": 1, "end_column": 8,
             "new_text": "x"},
        ])
        assert editor.toPlainText() == "a-much-longer-word x\n"

    def test_edits_are_one_undo_step(self, editor):
        editor.setPlainText("aaa bbb\n")
        editor.apply_server_edits([
            {"start_line": 1, "start_column": 1, "end_line": 1, "end_column": 4,
             "new_text": "111"},
            {"start_line": 1, "start_column": 5, "end_line": 1, "end_column": 8,
             "new_text": "222"},
        ])
        editor.undo()
        assert editor.toPlainText() == "aaa bbb\n"

    def test_an_edit_on_a_missing_line_is_skipped(self, editor):
        editor.setPlainText("only one line\n")
        editor.apply_server_edits([{
            "start_line": 99, "start_column": 1, "end_line": 99, "end_column": 2,
            "new_text": "x"}])
        assert editor.toPlainText() == "only one line\n"

    def test_no_edits(self, editor):
        assert editor.apply_server_edits([]) is False


class TestEditorRequests:
    def test_hover_without_a_server_is_refused(self, editor):
        assert editor.request_hover() is False

    def test_formatting_without_a_server_is_refused(self, editor):
        assert editor.format_with_language_server() is False

    def test_hover_text_becomes_the_tooltip(self, editor):
        editor.show_hover_text("def run() -> None")
        assert editor.toolTip() == "def run() -> None"

    def test_rename_without_a_server_falls_back_to_word_replace(self, editor):
        editor.setPlainText("value = value + 1\n")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        with patch.object(editor, "rename_word_under_cursor", return_value=True) as fallback:
            assert editor.rename_symbol() is True
        fallback.assert_called_once()

    def test_definition_in_the_same_file_jumps(self, editor):
        editor.current_file = "app.ts"
        editor.setPlainText("one\ntwo\nthree\n")
        assert editor.go_to_definition_location(
            {"path": "app.ts", "line": 3, "column": 1}) is True
        assert editor.textCursor().blockNumber() == 2
