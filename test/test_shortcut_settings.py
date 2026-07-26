"""Tests for the shortcut table, user overrides and the settings dialog."""
from __future__ import annotations

import pytest

from je_editor.utils.shortcuts.shortcut_registry import (
    DEFAULT_SHORTCUTS, EDITOR_SHORTCUTS, WINDOW_SHORTCUTS, clean_overrides,
    effective_shortcuts, find_conflicts, normalise_sequence, sequence_for
)


class TestTheDefaultTable:
    def test_it_covers_both_halves(self):
        assert set(DEFAULT_SHORTCUTS) == set(WINDOW_SHORTCUTS) | set(EDITOR_SHORTCUTS)

    def test_the_two_halves_do_not_overlap(self):
        assert set(WINDOW_SHORTCUTS) & set(EDITOR_SHORTCUTS) == set()

    def test_nothing_is_claimed_twice(self):
        # A duplicate here would make Qt fire neither of the two commands.
        assert find_conflicts(DEFAULT_SHORTCUTS) == []

    def test_every_command_has_keys(self):
        assert all(sequence for sequence in DEFAULT_SHORTCUTS.values())

    def test_every_default_survives_a_round_trip_through_qt(self, qapp):
        # A default Qt spells differently would be recorded as a user change the
        # first time the settings dialog is saved.
        from PySide6.QtGui import QKeySequence
        for command, sequence in DEFAULT_SHORTCUTS.items():
            assert normalise_sequence(QKeySequence(sequence).toString()) == \
                normalise_sequence(sequence), command


class TestLookingUpASequence:
    def test_an_unconfigured_command_uses_its_default(self):
        assert sequence_for("save_file") == DEFAULT_SHORTCUTS["save_file"]

    def test_a_configured_command_uses_the_override(self):
        assert sequence_for("save_file", {"save_file": "Ctrl+Alt+W"}) == "Ctrl+Alt+W"

    def test_an_override_for_another_command_is_ignored(self):
        assert sequence_for("save_file", {"open_file": "Ctrl+Alt+W"}) == \
            DEFAULT_SHORTCUTS["save_file"]

    def test_an_empty_override_removes_the_shortcut(self):
        assert sequence_for("save_file", {"save_file": ""}) == ""

    def test_an_unknown_command_has_no_sequence(self):
        assert sequence_for("no_such_command") == ""

    def test_the_effective_table_covers_every_command(self):
        assert set(effective_shortcuts()) == set(DEFAULT_SHORTCUTS)

    def test_the_effective_table_applies_overrides(self):
        table = effective_shortcuts({"save_file": "Ctrl+Alt+W"})
        assert table["save_file"] == "Ctrl+Alt+W"


class TestFindingConflicts:
    def test_two_commands_on_one_sequence_are_reported(self):
        assert find_conflicts({"a": "Ctrl+G", "b": "Ctrl+G"}) == [("ctrl+g", ["a", "b"])]

    def test_the_comparison_ignores_case_and_order(self):
        assert find_conflicts({"a": "Ctrl+Shift+G", "b": "shift+ctrl+g"}) != []

    def test_distinct_sequences_are_fine(self):
        assert find_conflicts({"a": "Ctrl+G", "b": "Ctrl+H"}) == []

    def test_unassigned_commands_do_not_clash(self):
        assert find_conflicts({"a": "", "b": ""}) == []


class TestCleaningOverrides:
    def test_a_real_change_is_kept(self):
        assert clean_overrides({"save_file": "Ctrl+Alt+W"}) == {"save_file": "Ctrl+Alt+W"}

    def test_a_value_still_at_its_default_is_dropped(self):
        assert clean_overrides({"save_file": DEFAULT_SHORTCUTS["save_file"]}) == {}

    def test_a_default_written_differently_is_still_a_default(self):
        assert clean_overrides({"command_palette": "shift+ctrl+a"}) == {}

    def test_an_unknown_command_is_dropped(self):
        assert clean_overrides({"no_such_command": "Ctrl+G"}) == {}

    def test_a_non_string_is_dropped(self):
        assert clean_overrides({"save_file": 5}) == {}

    def test_nothing_configured_stays_nothing(self):
        assert clean_overrides({}) == {}


@pytest.fixture()
def dialog(qapp, qtbot):
    """The settings dialog, with the real command table behind it."""
    from je_editor.pyside_ui.dialog.shortcut_dialog.shortcut_settings_dialog import (
        ShortcutSettingsDialog
    )
    from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
    saved = dict(user_setting_dict.get("shortcuts") or {})
    widget = ShortcutSettingsDialog()
    qtbot.addWidget(widget)
    yield widget
    user_setting_dict["shortcuts"] = saved


class TestTheSettingsDialog:
    def test_it_lists_every_command(self, dialog):
        assert dialog.tree.topLevelItemCount() == len(DEFAULT_SHORTCUTS)

    def test_it_starts_from_the_current_shortcuts(self, dialog):
        assert normalise_sequence(dialog.current_shortcuts()["save_file"]) == \
            normalise_sequence(DEFAULT_SHORTCUTS["save_file"])

    def test_it_starts_without_conflicts(self, dialog):
        assert dialog.conflicts() == []

    def test_a_clash_is_reported(self, dialog):
        from PySide6.QtGui import QKeySequence
        dialog._editors["save_file"].setKeySequence(
            QKeySequence(DEFAULT_SHORTCUTS["open_file"]))
        assert dialog.conflicts() != []

    def test_a_clash_cannot_be_saved(self, dialog):
        from PySide6.QtGui import QKeySequence
        dialog._editors["save_file"].setKeySequence(
            QKeySequence(DEFAULT_SHORTCUTS["open_file"]))
        assert dialog.save() is False
        assert dialog.save_button.isEnabled() is False

    def test_a_change_is_stored(self, dialog):
        from PySide6.QtGui import QKeySequence
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        dialog._editors["save_all"].setKeySequence(QKeySequence("Ctrl+Alt+W"))
        assert dialog.save() is True
        assert user_setting_dict["shortcuts"]["save_all"] == "Ctrl+Alt+W"

    def test_untouched_commands_are_not_stored(self, dialog):
        from PySide6.QtGui import QKeySequence
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        dialog._editors["save_all"].setKeySequence(QKeySequence("Ctrl+Alt+W"))
        dialog.save()
        assert set(user_setting_dict["shortcuts"]) == {"save_all"}

    def test_saving_reaches_the_menus_already_built(self, dialog):
        # The menus and the toolbar are built once at startup, so a saved change
        # has to be pushed to them rather than waiting for the next launch.
        from PySide6.QtGui import QAction, QKeySequence
        from je_editor.pyside_ui.main_ui.save_settings.shortcut_setting import bind
        action = QAction()
        bind(action, "save_all")
        dialog._editors["save_all"].setKeySequence(QKeySequence("Ctrl+Alt+W"))
        dialog.save()
        assert normalise_sequence(action.shortcut().toString()) == \
            normalise_sequence("Ctrl+Alt+W")

    def test_restoring_defaults_clears_a_change(self, dialog):
        from PySide6.QtGui import QKeySequence
        dialog._editors["save_all"].setKeySequence(QKeySequence("Ctrl+Alt+W"))
        dialog.reset_to_defaults()
        assert normalise_sequence(dialog.current_shortcuts()["save_all"]) == \
            normalise_sequence(DEFAULT_SHORTCUTS["save_all"])


class TestTheEditorFollowsTheSetting:
    def test_a_configured_sequence_reaches_the_action(self, qapp, qtbot):
        from unittest.mock import MagicMock, patch
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        saved = dict(user_setting_dict.get("shortcuts") or {})
        user_setting_dict["shortcuts"] = {"go_to_line": "Ctrl+Alt+W"}
        try:
            with patch(
                "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
            ) as mock_venv:
                mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
                parent = MagicMock()
                parent.current_file = None
                from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import (
                    CodeEditor
                )
                editor = CodeEditor(parent)
            qtbot.addWidget(editor)
            assert normalise_sequence(editor.goto_line_action.shortcut().toString()) == \
                normalise_sequence("Ctrl+Alt+W")
        finally:
            user_setting_dict["shortcuts"] = saved
