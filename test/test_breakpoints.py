"""Tests for breakpoints and the stepping commands sent to pdb."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.debugger.pdb_commands import (
    CONTINUE,
    STEP_INTO,
    STEP_OUT,
    STEP_OVER,
    breakpoint_command,
    breakpoint_commands,
    clear_command,
    step_command,
    toggle_command,
)


class TestPdbCommands:
    def test_a_breakpoint_names_the_file_and_line(self):
        assert breakpoint_command("/project/app.py", 12) == "break /project/app.py:12"

    def test_windows_paths_use_forward_slashes(self):
        assert breakpoint_command("D:\\project\\app.py", 3) == "break D:/project/app.py:3"

    def test_line_numbers_below_one_are_clamped(self):
        assert breakpoint_command("app.py", 0).endswith(":1")

    def test_several_breakpoints_are_sorted_and_unique(self):
        commands = breakpoint_commands("app.py", [7, 3, 7])
        assert commands == ["break app.py:3", "break app.py:7"]

    def test_invalid_lines_are_dropped(self):
        assert breakpoint_commands("app.py", [0, -2]) == []

    def test_clearing_names_the_file_and_line(self):
        assert clear_command("/project/app.py", 12) == "clear /project/app.py:12"

    def test_clearing_uses_forward_slashes_too(self):
        assert clear_command("D:\\project\\app.py", 3) == "clear D:/project/app.py:3"

    def test_toggling_on_sets_a_breakpoint(self):
        assert toggle_command("app.py", 4, True) == "break app.py:4"

    def test_toggling_off_clears_it(self):
        assert toggle_command("app.py", 4, False) == "clear app.py:4"

    @pytest.mark.parametrize("action,expected", [
        ("into", STEP_INTO), ("over", STEP_OVER),
        ("out", STEP_OUT), ("continue", CONTINUE),
    ])
    def test_stepping_actions(self, action, expected):
        assert step_command(action) == expected

    def test_an_unknown_action_has_no_command(self):
        assert step_command("sideways") is None


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
        parent.exec_python_debugger = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.close()
    code_editor.deleteLater()


def _place_cursor(editor, line: int) -> None:
    block = editor.document().findBlockByNumber(line)
    cursor = editor.textCursor()
    cursor.setPosition(block.position())
    editor.setTextCursor(cursor)


class TestBreakpointManager:
    def test_none_at_first(self, editor):
        editor.setPlainText("one\ntwo\nthree\n")
        assert editor.breakpoint_manager.lines() == []

    def test_toggling_sets_then_clears(self, editor):
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 1)
        assert editor.toggle_breakpoint() is True
        assert editor.breakpoint_manager.lines() == [1]
        assert editor.toggle_breakpoint() is False
        assert editor.breakpoint_manager.lines() == []

    def test_breakpoints_follow_inserted_lines(self, editor):
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 2)
        editor.toggle_breakpoint()
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.insertText("inserted above\n")
        # The breakpoint stays on "three", which is now one line further down.
        assert editor.breakpoint_manager.lines() == [3]

    def test_pdb_lines_are_one_based(self, editor):
        editor.setPlainText("one\ntwo\n")
        _place_cursor(editor, 0)
        editor.toggle_breakpoint()
        assert editor.breakpoint_manager.pdb_lines() == [1]

    def test_clearing_removes_everything(self, editor):
        editor.setPlainText("one\ntwo\n")
        _place_cursor(editor, 0)
        editor.toggle_breakpoint()
        assert editor.breakpoint_manager.clear() is True
        assert editor.breakpoint_manager.lines() == []

    def test_a_line_past_the_end_is_refused(self, editor):
        editor.setPlainText("only\n")
        assert editor.breakpoint_manager.toggle(99) is False

    def test_painting_with_a_breakpoint_does_not_raise(self, editor):
        editor.setPlainText("one\ntwo\n")
        _place_cursor(editor, 0)
        editor.toggle_breakpoint()
        editor.show()
        QApplication.processEvents()
        editor.hide()


class TestSendingToTheDebugger:
    def test_nothing_is_sent_without_a_debugger(self, editor):
        assert editor.send_debugger_command("over") is False

    def test_an_unknown_action_is_refused(self, editor):
        assert editor.send_debugger_command("sideways") is False

    def test_a_stepping_command_reaches_stdin(self, editor):
        stdin = MagicMock()
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        assert editor.send_debugger_command("into") is True
        stdin.write.assert_called_once_with(b"step\n")

    def test_breakpoints_are_sent_for_the_current_file(self, editor):
        stdin = MagicMock()
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        editor.current_file = "app.py"
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 1)
        editor.toggle_breakpoint()
        # Toggling sends its own change; this is about the full set going over.
        stdin.write.reset_mock()
        assert editor.send_breakpoints_to_debugger() == 1
        stdin.write.assert_called_once_with(b"break app.py:2\n")

    def test_no_breakpoints_are_sent_without_a_file(self, editor):
        editor.current_file = None
        assert editor.send_breakpoints_to_debugger() == 0

    def test_starting_the_debugger_sends_them(self, editor):
        # Without this the gutter marks never reach pdb and never stop anything.
        from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_debug_menu import (
            send_breakpoints
        )
        stdin = MagicMock()
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        editor.current_file = "app.py"
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 2)
        editor.toggle_breakpoint()
        stdin.write.reset_mock()
        widget = MagicMock()
        widget.code_edit = editor
        assert send_breakpoints(widget) == 1
        stdin.write.assert_called_once_with(b"break app.py:3\n")

    def test_a_tab_without_an_editor_sends_nothing(self, editor):
        from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_debug_menu import (
            send_breakpoints
        )
        widget = MagicMock()
        widget.code_edit = None
        assert send_breakpoints(widget) == 0

    def test_toggling_during_a_run_sets_the_breakpoint(self, editor):
        stdin = MagicMock()
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        editor.current_file = "app.py"
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 1)
        assert editor.toggle_breakpoint() is True
        stdin.write.assert_called_once_with(b"break app.py:2\n")

    def test_toggling_it_off_during_a_run_clears_it(self, editor):
        stdin = MagicMock()
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        editor.current_file = "app.py"
        editor.setPlainText("one\ntwo\nthree\n")
        _place_cursor(editor, 1)
        editor.toggle_breakpoint()
        stdin.write.reset_mock()
        assert editor.toggle_breakpoint() is False
        stdin.write.assert_called_once_with(b"clear app.py:2\n")

    def test_an_unsaved_buffer_sends_nothing(self, editor):
        editor.main_window.exec_python_debugger = MagicMock()
        editor.current_file = None
        assert editor.send_breakpoint_change(0, True) is False

    def test_toggling_without_a_debugger_still_works(self, editor):
        editor.main_window.exec_python_debugger = None
        editor.current_file = "app.py"
        editor.setPlainText("one\ntwo\n")
        _place_cursor(editor, 0)
        assert editor.toggle_breakpoint() is True
        assert editor.breakpoint_manager.lines() == [0]

    def test_a_broken_pipe_is_reported_rather_than_raised(self, editor):
        stdin = MagicMock()
        stdin.write.side_effect = OSError("broken pipe")
        editor.main_window.exec_python_debugger = MagicMock()
        editor.main_window.exec_python_debugger.process.stdin = stdin
        assert editor.send_debugger_command("continue") is False
