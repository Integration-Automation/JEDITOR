"""
Tests that the editing keys the editor used to hard-code are ordinary, reassignable commands.

Each key is pressed with ``QTest.keyClick`` on a shown, focused editor, so the
event takes the real route: Qt first offers it to the editor as a
``ShortcutOverride`` and only then to the actions. A key the text control claimed
at that stage would never reach its action, which calling the handler directly
could not show.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtTest import QTest

from je_editor.pyside_ui.main_ui.save_settings.shortcut_setting import (
    reload_bound_shortcuts,
)
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import (
    user_setting_dict,
)
from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.shortcuts.shortcut_registry import (
    DEFAULT_SHORTCUTS,
    EDITOR_SHORTCUTS,
    WINDOW_SHORTCUTS,
    find_conflicts,
    normalise_sequence,
)

CTRL = Qt.KeyboardModifier.ControlModifier
ALT = Qt.KeyboardModifier.AltModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier

# 指令、預設按鍵，以及用 QTest 按下它的方式
# Each command, its default keys, and how QTest presses them
EDITING_KEYS = (
    ("duplicate_line", "Ctrl+D", Qt.Key.Key_D, CTRL),
    ("toggle_comment", "Ctrl+/", Qt.Key.Key_Slash, CTRL),
    ("move_line_up", "Alt+Up", Qt.Key.Key_Up, ALT),
    ("move_line_down", "Alt+Down", Qt.Key.Key_Down, ALT),
    ("jump_to_definition", "Ctrl+B", Qt.Key.Key_B, CTRL),
    ("jump_to_matching_bracket", "Ctrl+Shift+\\", Qt.Key.Key_Backslash, CTRL | SHIFT),
    ("zoom_in", "Ctrl++", Qt.Key.Key_Plus, CTRL),
    ("zoom_in_alternate", "Ctrl+=", Qt.Key.Key_Equal, CTRL),
    ("zoom_out", "Ctrl+-", Qt.Key.Key_Minus, CTRL),
)
COMMANDS = [command for command, *_ in EDITING_KEYS]

# 覆寫測試用的按鍵：沒有任何指令使用它
# The key used by the override tests; no command uses it by default
FREE_KEY = "F8"


@pytest.fixture()
def editor(qapp, qtbot):
    """A shown editor that holds the keyboard focus, so shortcuts can match."""
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import (
            CodeEditor,
        )
        code_editor = CodeEditor(parent)
    qtbot.addWidget(code_editor)
    code_editor.show()
    code_editor.activateWindow()
    code_editor.setFocus()
    qtbot.waitUntil(code_editor.hasFocus)
    return code_editor


@pytest.fixture()
def restore_shortcuts():
    """Put the user's shortcut setting back, and every bound action with it."""
    saved = dict(user_setting_dict.get("shortcuts") or {})
    yield
    user_setting_dict["shortcuts"] = saved
    reload_bound_shortcuts()


def _action(editor, command: str) -> QAction:
    """The editor's action for a command."""
    action = editor.findChild(QAction, command)
    assert action is not None, f"no action for {command}"
    return action


def _place_caret(editor, text: str, line: int, column: int = 0) -> None:
    """Replace the text and put the caret on a line and column."""
    editor.setPlainText(text)
    cursor = editor.textCursor()
    cursor.setPosition(editor.document().findBlockByNumber(line).position() + column)
    editor.setTextCursor(cursor)


class TestTheDefaults:
    @pytest.mark.parametrize(("command", "sequence", "_key", "_modifiers"), EDITING_KEYS)
    def test_each_command_is_in_the_editor_table(self, command, sequence, _key, _modifiers):
        assert normalise_sequence(EDITOR_SHORTCUTS[command]) == normalise_sequence(sequence)

    def test_the_whole_table_is_still_conflict_free(self):
        assert find_conflicts(DEFAULT_SHORTCUTS) == []

    def test_no_default_takes_a_window_sequence(self):
        reserved = {normalise_sequence(sequence) for sequence in WINDOW_SHORTCUTS.values()}
        assert {normalise_sequence(EDITOR_SHORTCUTS[command]) for command in COMMANDS} & reserved \
            == set()

    @pytest.mark.parametrize("command", COMMANDS)
    def test_the_settings_dialog_has_a_label_for_each_one(self, command):
        assert english_word_dict.get(f"shortcut_{command}")

    @pytest.mark.parametrize("command", COMMANDS)
    def test_the_editor_registered_each_one(self, editor, command):
        assert editor.shortcut_registry.owner_of(EDITOR_SHORTCUTS[command]) == command
        assert editor.shortcut_registry.conflicts() == []


class TestPressingTheDefaultKeys:
    """Each default key, pressed on a focused editor, reaches its action and does its job."""

    def _press(self, qtbot, editor, command: str) -> None:
        """Press a command's default key and require its action to fire."""
        _command, _sequence, key, modifiers = next(
            entry for entry in EDITING_KEYS if entry[0] == command)
        with qtbot.waitSignal(_action(editor, command).triggered, timeout=1000):
            QTest.keyClick(editor, key, modifiers)

    def test_duplicate_line(self, qtbot, editor):
        _place_caret(editor, "one\ntwo", 0)
        self._press(qtbot, editor, "duplicate_line")
        assert editor.toPlainText() == "one\none\ntwo"

    def test_toggle_comment(self, qtbot, editor):
        _place_caret(editor, "value = 1", 0)
        self._press(qtbot, editor, "toggle_comment")
        assert editor.toPlainText() == "# value = 1"

    def test_move_line_up(self, qtbot, editor):
        _place_caret(editor, "first\nsecond", 1)
        self._press(qtbot, editor, "move_line_up")
        assert editor.toPlainText() == "second\nfirst"

    def test_move_line_down(self, qtbot, editor):
        _place_caret(editor, "first\nsecond", 0)
        self._press(qtbot, editor, "move_line_down")
        assert editor.toPlainText() == "second\nfirst"

    def test_jump_to_definition(self, qtbot, editor):
        _place_caret(editor, "def target():\n    pass\n\n\ntarget()\n", 4, 2)
        self._press(qtbot, editor, "jump_to_definition")
        assert editor.textCursor().blockNumber() == 0

    def test_jump_to_matching_bracket(self, qtbot, editor):
        _place_caret(editor, "(a, b)", 0)
        self._press(qtbot, editor, "jump_to_matching_bracket")
        assert editor.textCursor().position() == len("(a, b")

    @pytest.mark.parametrize(("command", "step"), [
        ("zoom_in", 1), ("zoom_in_alternate", 1), ("zoom_out", -1)])
    def test_zoom(self, qtbot, editor, command, step):
        before = editor.font().pointSize()
        self._press(qtbot, editor, command)
        assert editor.font().pointSize() == before + step


class TestReassigningAKey:
    """After a saved change the new key does the job and the old one no longer does."""

    @pytest.mark.parametrize("command", COMMANDS)
    def test_the_action_follows_the_setting(self, editor, restore_shortcuts, command):
        user_setting_dict["shortcuts"] = {command: FREE_KEY}
        reload_bound_shortcuts()
        assert normalise_sequence(_action(editor, command).shortcut().toString()) == \
            normalise_sequence(FREE_KEY)

    def test_the_new_key_works(self, qtbot, editor, restore_shortcuts):
        user_setting_dict["shortcuts"] = {"duplicate_line": FREE_KEY}
        reload_bound_shortcuts()
        _place_caret(editor, "one", 0)
        with qtbot.waitSignal(_action(editor, "duplicate_line").triggered, timeout=1000):
            QTest.keyClick(editor, Qt.Key.Key_F8)
        assert editor.toPlainText() == "one\none"

    def test_the_old_key_no_longer_works(self, qtbot, editor, restore_shortcuts):
        user_setting_dict["shortcuts"] = {"duplicate_line": FREE_KEY}
        reload_bound_shortcuts()
        _place_caret(editor, "one", 0)
        with qtbot.assertNotEmitted(_action(editor, "duplicate_line").triggered):
            QTest.keyClick(editor, Qt.Key.Key_D, CTRL)
        assert editor.toPlainText() == "one"

    def test_the_old_zoom_key_no_longer_zooms(self, qtbot, editor, restore_shortcuts):
        user_setting_dict["shortcuts"] = {"zoom_in_alternate": FREE_KEY}
        reload_bound_shortcuts()
        before = editor.font().pointSize()
        QTest.keyClick(editor, Qt.Key.Key_Equal, CTRL)
        assert editor.font().pointSize() == before


class TestMoveLineWithExtraCarets:
    @pytest.mark.parametrize(("key", "direction"), [(Qt.Key.Key_Up, -1), (Qt.Key.Key_Down, 1)])
    def test_alt_arrow_moves_the_carets_not_the_line(self, editor, qtbot, key, direction):
        _place_caret(editor, "aa\nbb\ncc\ndd", 1, 1)
        assert editor.multi_cursor_manager.add_caret_on_neighbouring_line(1)
        with patch.object(editor.multi_cursor_manager, "move_all_vertically",
                          wraps=editor.multi_cursor_manager.move_all_vertically) as moved:
            QTest.keyClick(editor, key, Qt.KeyboardModifier.AltModifier)
            qtbot.waitUntil(lambda: moved.call_count == 1)
        moved.assert_called_once_with(direction)
        assert editor.toPlainText() == "aa\nbb\ncc\ndd"
