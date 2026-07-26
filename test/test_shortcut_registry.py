"""Tests that key sequences are normalised and that nothing claims one twice."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from je_editor.utils.shortcuts.shortcut_registry import (
    WINDOW_SHORTCUTS, ShortcutRegistry, normalise_sequence
)


class TestNormalising:
    def test_case_is_levelled(self):
        assert normalise_sequence("Ctrl+Shift+f") == normalise_sequence("ctrl+shift+F")

    def test_modifier_order_does_not_matter(self):
        assert normalise_sequence("Shift+Ctrl+A") == normalise_sequence("Ctrl+Shift+A")

    def test_modifier_aliases_agree(self):
        assert normalise_sequence("Control+Alt+S") == normalise_sequence("Ctrl+Option+S")

    def test_a_plain_key_survives(self):
        assert normalise_sequence("F7") == "f7"

    def test_plus_can_be_the_key(self):
        assert normalise_sequence("Ctrl++") == "ctrl++"

    def test_blank_means_unassigned(self):
        assert normalise_sequence("   ") == ""

    def test_surrounding_space_is_ignored(self):
        assert normalise_sequence(" Ctrl + G ") == "ctrl+g"

    def test_different_keys_stay_different(self):
        assert normalise_sequence("Ctrl+D") != normalise_sequence("Ctrl+Alt+D")


class TestRegistry:
    def test_an_unused_sequence_is_accepted(self):
        registry = ShortcutRegistry()
        assert registry.register("Ctrl+Alt+N", "next_occurrence") is None

    def test_the_owner_can_be_looked_up(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+Alt+N", "next_occurrence")
        assert registry.owner_of("ctrl+alt+n") == "next_occurrence"

    def test_a_second_claim_names_the_first_owner(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+D", "duplicate_line")
        assert registry.register("Ctrl+D", "next_occurrence") == "duplicate_line"

    def test_the_first_owner_keeps_the_sequence(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+D", "duplicate_line")
        registry.register("Ctrl+D", "next_occurrence")
        assert registry.owner_of("Ctrl+D") == "duplicate_line"

    def test_registering_the_same_command_twice_is_not_a_clash(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+D", "duplicate_line")
        assert registry.register("Ctrl+D", "duplicate_line") is None

    def test_clashes_are_collected(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+D", "duplicate_line")
        registry.register("Ctrl+D", "next_occurrence")
        assert registry.conflicts() == [("ctrl+d", "duplicate_line", "next_occurrence")]

    def test_reserved_sequences_are_already_taken(self):
        registry = ShortcutRegistry({"Ctrl+Shift+P": "pip_install"})
        assert registry.register("Ctrl+Shift+P", "play_macro") == "pip_install"

    def test_register_all_reports_only_its_own_clashes(self):
        registry = ShortcutRegistry()
        registry.register("Ctrl+D", "duplicate_line")
        registry.register("Ctrl+D", "next_occurrence")
        clashes = registry.register_all([("Ctrl+G", "go_to_line"), ("Ctrl+G", "other")])
        assert clashes == [("ctrl+g", "go_to_line", "other")]

    def test_a_blank_sequence_is_ignored(self):
        registry = ShortcutRegistry()
        assert registry.register("", "nothing") is None
        assert registry.commands() == {}


class TestWindowShortcutTable:
    """
    The reserved table has to describe what the menus and toolbar really set.

    The toolbar side of that check lives in ``test_toolbar_actions``, next to the
    fixture that builds a real toolbar.
    """

    def test_no_sequence_is_listed_twice(self):
        normalised = [normalise_sequence(sequence) for sequence in WINDOW_SHORTCUTS]
        assert len(normalised) == len(set(normalised))

    def test_save_all_moved_off_the_editors_sort_shortcut(self):
        assert normalise_sequence("Ctrl+Alt+S") not in {
            normalise_sequence(sequence) for sequence in WINDOW_SHORTCUTS}


@pytest.fixture()
def editor(qapp, qtbot):
    """One editor, with its lifetime handled by qtbot rather than by hand."""
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    qtbot.addWidget(code_editor)
    return code_editor


class TestTheEditorHasNoClashes:
    """
    Two actions sharing a sequence make Qt run neither, so a clash silently
    disables both features. These walk the real actions rather than a list.
    """

    def test_the_registry_recorded_no_conflict(self, editor):
        assert editor.shortcut_registry.conflicts() == []

    def test_no_two_actions_share_a_sequence(self, editor):
        sequences = [
            normalise_sequence(action.shortcut().toString())
            for action in editor.actions()
            if action.shortcut().toString()
        ]
        assert len(sequences) == len(set(sequences))

    def test_no_action_takes_a_menu_sequence(self, editor):
        reserved = {normalise_sequence(sequence) for sequence in WINDOW_SHORTCUTS}
        taken = {
            normalise_sequence(action.shortcut().toString())
            for action in editor.actions()
            if action.shortcut().toString()
        }
        assert taken & reserved == set()

    def test_shortcuts_are_scoped_to_the_focused_editor(self, editor):
        # A split view shows two editors of the same document at once. With the
        # window-level default every sequence would have two owners, and Qt fires
        # neither of them.
        from PySide6.QtCore import Qt
        contexts = {
            action.shortcutContext()
            for action in editor.actions()
            if action.shortcut().toString()
        }
        assert contexts == {Qt.ShortcutContext.WidgetWithChildrenShortcut}

    def test_duplicate_line_still_owns_control_d(self, editor):
        # Ctrl+D is handled in keyPressEvent; no action may shadow it.
        assert editor.shortcut_registry.owner_of("Ctrl+D") is None
