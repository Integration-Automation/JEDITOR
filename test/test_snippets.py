"""Tests for snippet expansion and its tab stops."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.code.snippets.snippet_manager import load_snippets
from je_editor.utils.snippets.snippet_expand import (
    default_snippets,
    expand_snippet,
    merge_snippets,
)


class TestExpandSnippet:
    def test_plain_text_has_no_stops(self):
        text, stops = expand_snippet("print('hello')")
        assert text == "print('hello')"
        assert stops == []

    def test_numbered_stop_is_removed_from_the_text(self):
        text, stops = expand_snippet("def $1():")
        assert text == "def ():"
        assert [stop.position for stop in stops] == [4]

    def test_default_value_is_kept_and_selectable(self):
        text, stops = expand_snippet("def ${1:name}():")
        assert text == "def name():"
        assert stops[0].position == 4
        assert stops[0].length == len("name")

    def test_stops_come_back_in_order(self):
        _text, stops = expand_snippet("${2:second} ${1:first}")
        # $1 is visited before $2 even though it appears later.
        assert stops[0].position > stops[1].position

    def test_final_stop_sorts_last(self):
        _text, stops = expand_snippet("$0 ${1:first}")
        assert stops[-1].position == 0

    def test_repeated_number_keeps_the_first(self):
        text, stops = expand_snippet("$1 and $1")
        assert text == " and "
        assert len(stops) == 1

    def test_multiline_body(self):
        text, stops = expand_snippet("for ${1:item} in ${2:rows}:\n    $0")
        assert text == "for item in rows:\n    "
        assert len(stops) == 3


class TestSnippetSets:
    def test_defaults_cover_common_python(self):
        assert {"def", "class", "for", "if", "main"} <= set(default_snippets())

    def test_user_snippets_are_merged_over_the_defaults(self):
        merged = merge_snippets({"def": "custom $0", "mine": "body"})
        assert merged["def"] == "custom $0"
        assert merged["mine"] == "body"
        assert "class" in merged

    def test_a_hand_edited_file_cannot_break_the_set(self):
        merged = merge_snippets({"ok": "body", 5: "bad key", "bad value": 7})
        assert merged["ok"] == "body"
        assert "class" in merged

    def test_non_dict_falls_back_to_the_defaults(self):
        assert merge_snippets("nonsense") == default_snippets()

    def test_loading_a_missing_file_uses_the_defaults(self, tmp_path):
        assert load_snippets(tmp_path / "absent.json") == default_snippets()

    def test_loading_invalid_json_uses_the_defaults(self, tmp_path):
        broken = tmp_path / "snippets.json"
        broken.write_text("{not json", encoding="utf-8")
        assert load_snippets(broken) == default_snippets()

    def test_loading_a_user_file(self, tmp_path):
        path = tmp_path / "snippets.json"
        path.write_text(json.dumps({"log": "print($0)"}), encoding="utf-8")
        assert load_snippets(path)["log"] == "print($0)"


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
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.blame_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


def _press_tab(editor) -> None:
    editor.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier, "\t"))


class TestSnippetExpansionInEditor:
    def test_tab_expands_a_trigger_word(self, editor):
        editor.setPlainText("for")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)
        assert "in" in editor.toPlainText()
        assert "for" in editor.toPlainText()

    def test_the_first_default_value_is_selected(self, editor):
        editor.setPlainText("for")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)
        assert editor.textCursor().selectedText() == "item"

    def test_tab_moves_to_the_next_stop(self, editor):
        editor.setPlainText("for")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)
        _press_tab(editor)
        assert editor.textCursor().selectedText() == "iterable"

    def test_an_unknown_word_is_left_alone(self, editor):
        editor.setPlainText("notasnippet")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        assert editor.snippet_manager.expand_at_cursor() is False

    def test_expansion_is_one_undo_step(self, editor):
        editor.setPlainText("if")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)
        editor.undo()
        assert editor.toPlainText() == "if"

    def test_stops_run_out_after_the_last_one(self, editor):
        editor.setPlainText("if")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)
        while editor.snippet_manager.has_pending_stops:
            editor.snippet_manager.next_stop()
        assert editor.snippet_manager.next_stop() is False

    def test_tab_still_indents_a_selection(self, editor):
        editor.setPlainText("alpha\nbeta\n")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(9, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        _press_tab(editor)
        assert editor.toPlainText().startswith(" ")

    def test_reloading_picks_up_user_snippets(self, editor, tmp_path):
        path = tmp_path / "snippets.json"
        path.write_text(json.dumps({"zzz": "expanded $0"}), encoding="utf-8")
        editor.snippet_manager.reload(path)
        assert "zzz" in editor.snippet_manager.snippets()
