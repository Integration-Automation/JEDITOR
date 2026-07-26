"""Tests for snippet expansion and its tab stops."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.code.snippets.snippet_manager import load_snippets
from je_editor.utils.snippets.snippet_expand import (
    default_snippets,
    expand_snippet,
    merge_snippets,
    positions_after_mirroring,
    shift_mirrors,
)


class TestExpandingRepeatedStops:
    def test_a_repeat_is_not_a_separate_stop(self):
        _text, stops = expand_snippet("${1:name} = ${1:name}")
        assert len(stops) == 1

    def test_the_repeat_is_recorded_as_a_mirror(self):
        # "name = name" -- the second copy starts at index 7.
        _text, stops = expand_snippet("${1:name} = ${1:name}")
        assert stops[0].mirrors == (7,)

    def test_the_repeat_carries_the_first_default(self):
        text, _stops = expand_snippet("${1:name} = $1")
        assert text == "name = name"

    def test_several_repeats_are_all_recorded(self):
        _text, stops = expand_snippet("$1 $1 $1")
        assert len(stops[0].mirrors) == 2

    def test_a_stop_used_once_has_no_mirrors(self):
        _text, stops = expand_snippet("${1:one} ${2:two}")
        assert all(stop.mirrors == () for stop in stops)


class TestShiftingMirrors:
    def test_a_mirror_after_the_change_moves(self):
        assert shift_mirrors([10], 4, 3) == [13]

    def test_a_mirror_before_the_change_stays(self):
        assert shift_mirrors([2], 4, 3) == [2]

    def test_a_deletion_pulls_it_back(self):
        assert shift_mirrors([10], 4, -2) == [8]

    def test_a_mirror_exactly_at_the_change_moves(self):
        assert shift_mirrors([4], 4, 3) == [7]


class TestPositionsAfterMirroring:
    def test_nothing_moves_when_the_length_is_unchanged(self):
        assert positions_after_mirroring(0, [10], 0) == (0, [10])

    def test_a_later_mirror_absorbs_every_earlier_rewrite(self):
        _start, mirrors = positions_after_mirroring(0, [10, 20], 2)
        assert mirrors == [10, 22]

    def test_the_stop_moves_for_mirrors_ahead_of_it(self):
        start, _mirrors = positions_after_mirroring(30, [10, 20], 2)
        assert start == 34

    def test_the_stop_ignores_mirrors_behind_it(self):
        start, _mirrors = positions_after_mirroring(0, [10, 20], 2)
        assert start == 0

    def test_mirrors_are_handled_in_position_order(self):
        _start, mirrors = positions_after_mirroring(0, [20, 10], 5)
        assert mirrors == [10, 25]


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

    def test_language_snippets_are_added_for_their_suffix(self):
        assert "iferr" in merge_snippets(None, ".go")
        assert "iferr" not in merge_snippets(None, ".py")

    def test_a_user_group_for_a_suffix_is_applied(self):
        merged = merge_snippets({".go": {"mine": "body"}}, ".go")
        assert merged["mine"] == "body"

    def test_a_group_for_another_suffix_is_ignored(self):
        assert "mine" not in merge_snippets({".ts": {"mine": "body"}}, ".go")

    def test_a_user_definition_beats_the_language_set(self):
        merged = merge_snippets({"iferr": "custom"}, ".go")
        assert merged["iferr"] == "custom"


class TestSaveSnippets:
    def test_round_trip_through_the_file(self, tmp_path):
        from je_editor.pyside_ui.code.snippets.snippet_manager import save_snippets
        path = tmp_path / "snippets.json"
        assert save_snippets({"mine": "body $0"}, path) is True
        assert load_snippets(path)["mine"] == "body $0"

    def test_saving_creates_the_directory(self, tmp_path):
        from je_editor.pyside_ui.code.snippets.snippet_manager import save_snippets
        path = tmp_path / "nested" / "snippets.json"
        assert save_snippets({"a": "b"}, path) is True
        assert path.is_file()

    def test_an_unwritable_path_is_reported(self, tmp_path):
        from je_editor.pyside_ui.code.snippets.snippet_manager import save_snippets
        # A directory where the file should be cannot be written to.
        target = tmp_path / "snippets.json"
        target.mkdir()
        assert save_snippets({"a": "b"}, target) is False


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
    # Sent through QTest so Qt owns the event object; a QKeyEvent built here
    # could be collected while Qt still holds it.
    QTest.keyClick(editor, Qt.Key.Key_Tab)


class TestMirroredStops:
    """
    A number used more than once in a snippet should only be typed once. The
    repeats used to be plain text, so `${1:name}` twice meant typing it twice.
    """

    @staticmethod
    def _expand(editor, body: str) -> None:
        editor.snippet_manager._snippets["mirror"] = body
        editor.setPlainText("mirror")
        editor.moveCursor(editor.textCursor().MoveOperation.End)
        _press_tab(editor)

    def test_a_repeat_starts_with_the_same_default(self, editor):
        self._expand(editor, "${1:name} = ${1:name}")
        assert editor.toPlainText() == "name = name"

    def test_typing_updates_the_repeat(self, editor):
        self._expand(editor, "${1:name} = ${1:name}")
        editor.textCursor().insertText("total")
        assert editor.toPlainText() == "total = total"

    def test_every_repeat_follows(self, editor):
        self._expand(editor, "${1:x}, ${1:x}, ${1:x}")
        editor.textCursor().insertText("ab")
        assert editor.toPlainText() == "ab, ab, ab"

    def test_a_repeat_after_other_text_follows(self, editor):
        self._expand(editor, "def ${1:name}():\n    return ${1:name}")
        editor.textCursor().insertText("run")
        assert editor.toPlainText() == "def run():\n    return run"

    def test_typing_elsewhere_leaves_the_repeat_alone(self, editor):
        self._expand(editor, "${1:name} = ${1:name}")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText("  # note")
        assert editor.toPlainText() == "name = name  # note"

    def test_a_stop_without_repeats_still_works(self, editor):
        self._expand(editor, "${1:one} ${2:two}")
        editor.textCursor().insertText("first")
        assert editor.toPlainText() == "first two"

    def test_moving_on_stops_the_mirroring(self, editor):
        self._expand(editor, "${1:name} = ${1:name}$0")
        _press_tab(editor)
        editor.textCursor().insertText("!")
        assert editor.toPlainText() == "name = name!"


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

    def test_a_typescript_file_gets_typescript_snippets(self, editor):
        editor.current_file = "app.ts"
        editor.snippet_manager.reload()
        snippets = editor.snippet_manager.snippets()
        assert "log" in snippets and "console.log" in snippets["log"]

    def test_a_python_file_keeps_the_python_set(self, editor):
        editor.current_file = "module.py"
        editor.snippet_manager.reload()
        assert "def" in editor.snippet_manager.snippets()

    def test_reloading_picks_up_user_snippets(self, editor, tmp_path):
        path = tmp_path / "snippets.json"
        path.write_text(json.dumps({"zzz": "expanded $0"}), encoding="utf-8")
        editor.snippet_manager.reload(path)
        assert "zzz" in editor.snippet_manager.snippets()
