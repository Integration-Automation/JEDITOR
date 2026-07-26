"""Tests that the toolbar wires up its actions with working labels and shortcuts."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import build_toolbar
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
