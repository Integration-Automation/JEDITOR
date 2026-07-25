"""Tests for persisting and restoring per-file editor state in the session."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.session.editor_state import editor_state, restore_editor_state
from je_editor.utils.session.open_files_session import (
    MAX_STATE_LINES,
    build_file_state,
    collect_file_states,
    restorable_file_state,
)


class TestBuildFileState:
    def test_keeps_caret_bookmarks_and_folds(self):
        state = build_file_state(4, [2, 7], [1])
        assert state == {"caret_line": 4, "bookmarks": [2, 7], "folds": [1]}

    def test_lines_are_sorted_and_deduplicated(self):
        assert build_file_state(0, [5, 1, 5], [])["bookmarks"] == [1, 5]

    def test_negative_lines_are_dropped(self):
        assert build_file_state(0, [-3, 2], [])["bookmarks"] == [2]

    def test_booleans_are_not_treated_as_lines(self):
        assert build_file_state(0, [True, 3], [])["bookmarks"] == [3]

    def test_negative_caret_is_clamped(self):
        assert build_file_state(-5, [], [])["caret_line"] == 0

    def test_non_list_values_become_empty(self):
        assert build_file_state(0, "nonsense", None)["bookmarks"] == []

    def test_line_count_is_capped(self):
        state = build_file_state(0, list(range(MAX_STATE_LINES + 50)), [])
        assert len(state["bookmarks"]) == MAX_STATE_LINES


class TestCollectFileStates:
    def test_collects_each_file(self):
        collected = collect_file_states({
            "a.py": {"caret_line": 3, "bookmarks": [1], "folds": []},
            "b.py": {"caret_line": 0, "bookmarks": [], "folds": [2]},
        })
        assert collected["a.py"]["caret_line"] == 3
        assert collected["b.py"]["folds"] == [2]

    def test_entries_without_a_path_are_dropped(self):
        assert collect_file_states({"": {"caret_line": 1}}) == {}

    def test_entries_that_are_not_dicts_are_dropped(self):
        assert collect_file_states({"a.py": "nonsense"}) == {}


class TestRestorableFileState:
    def test_reads_back_a_stored_state(self):
        stored = {"a.py": {"caret_line": 5, "bookmarks": [2], "folds": [1]}}
        assert restorable_file_state(stored, "a.py") == {
            "caret_line": 5, "bookmarks": [2], "folds": [1]}

    def test_unknown_file(self):
        assert restorable_file_state({"a.py": {}}, "b.py") is None

    def test_stored_value_of_the_wrong_type(self):
        assert restorable_file_state("nonsense", "a.py") is None

    def test_hand_edited_entry_is_cleaned_rather_than_trusted(self):
        stored = {"a.py": {"caret_line": "top", "bookmarks": ["x", 4], "folds": None}}
        assert restorable_file_state(stored, "a.py") == {
            "caret_line": 0, "bookmarks": [4], "folds": []}


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
    code_editor.setPlainText("\n".join(f"line {index}" for index in range(20)))
    yield code_editor
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.blame_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


@pytest.fixture()
def tab(editor):
    widget = MagicMock()
    widget.code_edit = editor
    return widget


class TestEditorStateRoundTrip:
    def test_state_records_the_caret_line(self, editor, tab):
        editor.jump_to_line(6)
        assert editor_state(tab)["caret_line"] == 5

    def test_state_records_bookmarks(self, editor, tab):
        editor.bookmark_manager.toggle(3)
        assert 3 in editor_state(tab)["bookmarks"]

    def test_restoring_moves_the_caret(self, editor, tab):
        restore_editor_state(tab, {"caret_line": 8, "bookmarks": [], "folds": []})
        assert editor.textCursor().blockNumber() == 8

    def test_restoring_brings_bookmarks_back(self, editor, tab):
        restore_editor_state(tab, {"caret_line": 0, "bookmarks": [2, 5], "folds": []})
        assert set(editor.bookmark_manager.bookmarked_lines()) >= {2, 5}

    def test_round_trip_through_the_session_format(self, editor, tab):
        editor.bookmark_manager.toggle(4)
        editor.jump_to_line(7)
        stored = collect_file_states({"a.py": editor_state(tab)})
        state = restorable_file_state(stored, "a.py")
        # A fresh editor state, then restore into it
        editor.bookmark_manager.toggle(4)
        editor.jump_to_line(1)
        restore_editor_state(tab, state)
        assert editor.textCursor().blockNumber() == 6
        assert 4 in editor.bookmark_manager.bookmarked_lines()

    def test_lines_past_the_end_are_skipped(self, editor, tab):
        assert restore_editor_state(
            tab, {"caret_line": 999, "bookmarks": [900], "folds": []}) is True
        assert editor.textCursor().blockNumber() <= editor.blockCount() - 1

    def test_no_state_is_a_no_op(self, tab):
        assert restore_editor_state(tab, None) is False
        assert restore_editor_state(tab, {}) is False

    def test_no_widget_is_a_no_op(self):
        assert restore_editor_state(None, {"caret_line": 1}) is False

    def test_a_widget_without_an_editor_is_a_no_op(self):
        assert restore_editor_state(object(), {"caret_line": 1}) is False
