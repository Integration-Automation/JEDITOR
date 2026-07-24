"""Tests for the quick open dialog, its background indexer and mode switching."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QAction

from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import _payload_runner
from je_editor.pyside_ui.main_ui.command_palette.quick_open_dialog import (
    COMMAND_MODE_PREFIX,
    FileIndexThread,
    QuickOpenDialog,
    make_file_opener,
    resolve_project_root,
)
from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry


class _FakeMainWindow:
    """Minimal stand-in that records the files quick open asked to open."""

    def __init__(self, working_dir=None):
        self.working_dir = working_dir
        self.opened: list[Path] = []

    def go_to_new_tab(self, file_path: Path) -> None:
        self.opened.append(file_path)


class TestPayloadRunner:
    """Payloads may be a QAction, a plain callable, or nothing."""

    def test_none_payload_has_no_runner(self):
        assert _payload_runner(None) is None

    def test_callable_payload_is_returned_as_is(self):
        def runner() -> None:
            return None

        assert _payload_runner(runner) is runner

    @pytest.mark.usefixtures("qapp")
    def test_action_payload_returns_its_trigger(self):
        action = QAction("Save")
        assert _payload_runner(action) == action.trigger

    def test_unrunnable_payload_returns_none(self):
        assert _payload_runner(object()) is None


class TestMakeFileOpener:
    """The opener closure must not depend on the (deleted) dialog."""

    def test_opener_forwards_the_path(self, tmp_path):
        window = _FakeMainWindow()
        make_file_opener(window, tmp_path / "main.py")()
        assert window.opened == [tmp_path / "main.py"]

    def test_opener_tolerates_no_window(self, tmp_path):
        make_file_opener(None, tmp_path / "main.py")()

    def test_opener_tolerates_window_without_tab_api(self, tmp_path):
        make_file_opener(object(), tmp_path / "main.py")()


class TestResolveProjectRoot:
    """Root resolution falls back to the process working directory."""

    def test_uses_working_dir_when_valid(self, tmp_path):
        assert resolve_project_root(_FakeMainWindow(str(tmp_path))) == str(tmp_path)

    def test_falls_back_when_working_dir_missing(self):
        assert resolve_project_root(_FakeMainWindow(None)) == os.getcwd()

    def test_falls_back_when_working_dir_does_not_exist(self, tmp_path):
        missing = str(tmp_path / "gone")
        assert resolve_project_root(_FakeMainWindow(missing)) == os.getcwd()


@pytest.mark.usefixtures("qapp")
class TestFileIndexThread:
    """Background indexing and cancellation."""

    def test_emits_indexed_paths(self, qtbot, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        thread = FileIndexThread(str(tmp_path))
        with qtbot.waitSignal(thread.indexed, timeout=5000) as blocker:
            thread.start()
        thread.wait()
        assert blocker.args[0] == ["main.py"]

    def test_stop_before_start_yields_nothing(self, qtbot, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        thread = FileIndexThread(str(tmp_path))
        thread.stop()
        with qtbot.waitSignal(thread.indexed, timeout=5000) as blocker:
            thread.start()
        thread.wait()
        assert blocker.args[0] == []


@pytest.mark.usefixtures("qapp")
class TestQuickOpenDialog:
    """File mode, command mode and thread teardown."""

    @staticmethod
    def _commands() -> list[CommandEntry]:
        return [
            CommandEntry(title="Run Program", path="Run > Run Program"),
            CommandEntry(title="Save File", path="File > Save File"),
        ]

    @staticmethod
    def _project(tmp_path) -> Path:
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "helper.py").write_text("y = 2\n", encoding="utf-8")
        return tmp_path

    def _dialog(self, qtbot, tmp_path, window=None) -> QuickOpenDialog:
        dialog = QuickOpenDialog(
            None, str(self._project(tmp_path)), self._commands(), main_window=window)
        qtbot.waitUntil(lambda: dialog.result_list.count() > 0, timeout=5000)
        return dialog

    def test_indexed_files_appear_in_the_list(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        assert dialog.result_list.count() == 2
        dialog.close()

    def test_typing_a_file_name_filters(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.search_input.setText("helper")
        assert dialog.result_list.count() == 1
        dialog.close()

    def test_folder_name_also_finds_the_file(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.search_input.setText("pkg")
        assert dialog.result_list.count() == 1
        dialog.close()

    def test_prefix_switches_to_command_mode(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.search_input.setText(f"{COMMAND_MODE_PREFIX}run")
        assert dialog.result_list.item(0).text().startswith("Run > Run Program")
        dialog.close()

    def test_command_mode_ignores_files(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.search_input.setText(f"{COMMAND_MODE_PREFIX}helper")
        assert dialog.result_list.count() == 0
        dialog.close()

    def test_clearing_the_prefix_returns_to_file_mode(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.search_input.setText(f"{COMMAND_MODE_PREFIX}run")
        dialog.search_input.setText("helper")
        assert dialog.result_list.count() == 1
        dialog.close()

    def test_selecting_a_file_opens_it(self, qtbot, tmp_path):
        window = _FakeMainWindow()
        dialog = self._dialog(qtbot, tmp_path, window)
        dialog.search_input.setText("helper")
        dialog._run_command_at(0)
        qtbot.waitUntil(lambda: len(window.opened) == 1, timeout=2000)
        assert window.opened[0].name == "helper.py"

    def test_closing_stops_the_index_thread(self, qtbot, tmp_path):
        dialog = self._dialog(qtbot, tmp_path)
        dialog.close()
        assert not dialog._index_thread.isRunning()

    def test_closing_immediately_is_safe(self, tmp_path):
        # Closing before the walk finishes must not leave a running QThread.
        dialog = QuickOpenDialog(None, str(self._project(tmp_path)), self._commands())
        dialog.close()
        assert not dialog._index_thread.isRunning()
