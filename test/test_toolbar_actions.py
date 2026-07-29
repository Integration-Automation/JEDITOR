"""Tests that the toolbar wires up its actions with working labels and shortcuts."""
from __future__ import annotations

import gc
import weakref

import pytest
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.main_ui.toolbar import toolbar_builder
from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
    build_toolbar, stop_background_threads
)
from je_editor.utils.shortcuts.shortcut_registry import (
    WINDOW_SHORTCUTS, normalise_sequence
)


@pytest.fixture()
def toolbar_window(qapp, qtbot):
    """Build the real toolbar on a bare main window."""
    window = QMainWindow()
    qtbot.addWidget(window)
    build_toolbar(window)
    yield window
    # The git scan the toolbar starts fills a combo box that is about to go away.
    stop_background_threads()


@pytest.mark.usefixtures("qapp")
class TestToolbarActions:
    """Every toolbar entry must reach a real callback with a translated label."""

    # (attribute on the main window, expected shortcut)
    PICKER_ACTIONS = (
        ("command_palette_action", "Ctrl+Shift+A"),
        ("quick_open_action", "Ctrl+P"),
        ("go_to_symbol_action", "Ctrl+Shift+O"),
    )

    def test_toolbar_is_attached(self, toolbar_window):
        assert toolbar_window.main_toolbar is not None

    @pytest.mark.parametrize("attribute,shortcut", PICKER_ACTIONS)
    def test_picker_action_exists(self, toolbar_window, attribute, shortcut):
        assert getattr(toolbar_window, attribute, None) is not None

    @pytest.mark.parametrize("attribute,shortcut", PICKER_ACTIONS)
    def test_picker_action_has_expected_shortcut(self, toolbar_window, attribute, shortcut):
        action = getattr(toolbar_window, attribute)
        assert action.shortcut().toString() == shortcut

    @pytest.mark.parametrize("attribute,shortcut", PICKER_ACTIONS)
    def test_picker_action_label_is_translated(self, toolbar_window, attribute, shortcut):
        # An empty label means the language dictionary is missing the key.
        assert getattr(toolbar_window, attribute).text().strip()

    def test_picker_shortcuts_do_not_collide(self, toolbar_window):
        shortcuts = [
            action.shortcut().toString()
            for action in toolbar_window.main_toolbar.actions()
            if action.shortcut().toString()
        ]
        assert len(shortcuts) == len(set(shortcuts))

    def test_new_actions_are_on_the_toolbar(self, toolbar_window):
        toolbar_actions = set(toolbar_window.main_toolbar.actions())
        for attribute, _shortcut in self.PICKER_ACTIONS:
            assert getattr(toolbar_window, attribute) in toolbar_actions

    def test_background_work_can_be_waited_for(self, toolbar_window):
        # Building the toolbar starts a git scan. Qt aborts the process if one is
        # still running when the window it hangs off is destroyed, and scanning a
        # large repository is not quick.
        from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
            stop_background_threads
        )
        assert stop_background_threads() >= 0

    def test_waiting_twice_is_safe(self, toolbar_window):
        from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
            stop_background_threads
        )
        stop_background_threads()
        assert stop_background_threads() == 0

    def test_every_toolbar_shortcut_is_reserved(self, toolbar_window):
        # The editor checks its own shortcuts against this table, so a sequence
        # the toolbar takes without listing it there could be claimed twice.
        reserved = {normalise_sequence(sequence) for sequence in WINDOW_SHORTCUTS.values()}
        for action in toolbar_window.main_toolbar.actions():
            sequence = normalise_sequence(action.shortcut().toString())
            if sequence:
                assert sequence in reserved, f"{sequence} is set but not reserved"


@pytest.mark.usefixtures("qapp", "toolbar_window")
class TestBackgroundScansOutliveTheirCaller:
    """
    A background scan has to be held somewhere once it is started.

    Nothing but the caller's local refers to it, so dropped early it is
    collected mid-run -- and destroying a running QThread makes Qt abort the
    process. The branch box also stays empty, because the scan never reports.
    """

    def test_the_scan_is_not_collected_when_the_caller_returns(self):
        stop_background_threads()
        reference = self._start_and_drop()
        gc.collect()
        assert reference() is not None
        stop_background_threads()

    def test_the_scan_reports_after_the_caller_returns(self, qtbot):
        stop_background_threads()
        reported = []

        # Connecting a callback does not keep the scan alive -- it owns the
        # connection, not the other way round -- so this still drops it.
        scan = toolbar_builder._GitBranchScan()
        scan.scanned.connect(lambda heads, current: reported.append(current))
        toolbar_builder._run_in_background(scan)
        del scan
        gc.collect()

        qtbot.waitUntil(lambda: bool(reported), timeout=15000)
        stop_background_threads()

    def test_the_scan_is_released_once_the_wait_is_over(self):
        # Held until it has run, but not held forever -- every refresh would
        # otherwise leave a thread behind for the life of the window.
        stop_background_threads()
        reference = self._start_and_drop()
        stop_background_threads()
        gc.collect()
        assert reference() is None

    @staticmethod
    def _start_and_drop() -> weakref.ref:
        """Start a scan the way the real call sites do, keeping only a weak reference."""
        scan = toolbar_builder._GitBranchScan()
        toolbar_builder._run_in_background(scan)
        return weakref.ref(scan)


@pytest.fixture()
def repository(tmp_path, monkeypatch):
    """A throw-away repository with two branches, and the toolbar looking at it."""
    git = pytest.importorskip("git")
    made = git.Repo.init(tmp_path, initial_branch="main")
    with made.config_writer() as config:
        config.set_value("user", "name", "Git Tester")
        config.set_value("user", "email", "git@example.com")
    (tmp_path / "tracked.txt").write_text("first\n", encoding="utf-8")
    made.index.add(["tracked.txt"])
    made.index.commit("initial")
    made.create_head("side")
    made.close()
    # The scan reads whatever repository the working directory sits in.
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _scan_result() -> tuple:
    """Run one scan on this thread and return what it reported."""
    reported = []
    scan = toolbar_builder._GitBranchScan()
    scan.scanned.connect(lambda heads, current: reported.append((heads, current)))
    scan.run()
    return reported[0]


@pytest.mark.usefixtures("qapp")
class TestTheBranchScan:
    """
    What the branch box is filled from. This never ran until the scan was held
    onto properly, so the reading itself had never been checked.
    """

    def test_it_lists_the_branches(self, repository):
        heads, _current = _scan_result()
        assert sorted(heads) == ["main", "side"]

    def test_it_names_the_branch_that_is_checked_out(self, repository):
        _heads, current = _scan_result()
        assert current == "main"

    def test_a_detached_head_reports_a_sha(self, repository):
        import subprocess
        # Fixed arguments against the throw-away repository above; no shell.
        sha = subprocess.run(  # nosemgrep  # noqa: S603,S607  # nosec B603,B607
            ["git", "rev-parse", "--short=8", "HEAD"], cwd=repository,
            capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(  # nosemgrep  # noqa: S603,S607  # nosec B603,B607
            ["git", "checkout", "--detach", "HEAD"], cwd=repository,
            capture_output=True, check=True)
        _heads, current = _scan_result()
        assert current == sha

    def test_somewhere_that_is_not_a_repository_reports_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _scan_result() == ([], "")

    def test_a_subdirectory_still_finds_the_repository(self, repository, monkeypatch):
        nested = repository / "deep" / "deeper"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)
        heads, current = _scan_result()
        assert sorted(heads) == ["main", "side"]
        assert current == "main"
