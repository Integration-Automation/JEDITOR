"""Tests for the command palette fuzzy matcher and menu command collector."""
from __future__ import annotations

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar

from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import (
    CommandPaletteDialog,
)
from je_editor.pyside_ui.main_ui.command_palette.menu_command_collector import (
    MAX_COMMANDS,
    clean_action_text,
    collect_menu_commands,
)
from je_editor.utils.command_palette.fuzzy_matcher import (
    CommandEntry,
    fuzzy_score,
    rank_commands,
    score_command,
)


class TestFuzzyScore:
    """Scoring behaviour of the greedy subsequence matcher."""

    def test_empty_query_scores_zero(self):
        assert fuzzy_score("", "Open File") == 0

    def test_empty_candidate_never_matches(self):
        assert fuzzy_score("open", "") is None

    def test_non_subsequence_returns_none(self):
        assert fuzzy_score("zzz", "Open File") is None

    def test_out_of_order_query_returns_none(self):
        # "fo" appears as f...o only in "File" -> "Open"? No: order matters.
        assert fuzzy_score("elif", "File") is None

    def test_subsequence_matches(self):
        assert fuzzy_score("of", "Open File") is not None

    def test_case_insensitive_match(self):
        assert fuzzy_score("OPEN", "open file") is not None

    def test_exact_prefix_beats_scattered_match(self):
        prefix = fuzzy_score("run", "Run Program")
        scattered = fuzzy_score("run", "Reformat Unused Names")
        assert prefix > scattered

    def test_consecutive_beats_split(self):
        consecutive = fuzzy_score("file", "file")
        split = fuzzy_score("file", "f_i_l_e")
        assert consecutive > split

    def test_shorter_candidate_scores_higher(self):
        short = fuzzy_score("save", "Save")
        long = fuzzy_score("save", "Save As Another Very Long Name")
        assert short > long


class TestScoreCommand:
    """Title weighting and path fallback."""

    def test_title_match_wins_over_path_only_match(self):
        title_match = CommandEntry(title="Open File", path="File > Open File")
        path_match = CommandEntry(title="Reload", path="Open File Menu > Reload")
        assert score_command("open file", title_match) > score_command("open file", path_match)

    def test_path_only_match_still_matches(self):
        command = CommandEntry(title="Reload", path="Git > Reload")
        assert score_command("git", command) is not None

    def test_unmatched_command_returns_none(self):
        command = CommandEntry(title="Reload", path="Git > Reload")
        assert score_command("xylophone", command) is None

    def test_entry_without_path_falls_back_to_title(self):
        command = CommandEntry(title="Reload")
        assert command.search_text == "Reload"
        assert score_command("rel", command) is not None


class TestRankCommands:
    """Ranking, limiting and stability."""

    @staticmethod
    def _commands() -> list[CommandEntry]:
        return [
            CommandEntry(title="Open File", path="File > Open File"),
            CommandEntry(title="Open Folder", path="File > Open Folder"),
            CommandEntry(title="Save File", path="File > Save File"),
            CommandEntry(title="Run Program", path="Run > Run Program"),
        ]

    def test_empty_query_returns_original_order(self):
        commands = self._commands()
        assert rank_commands("  ", commands) == commands

    def test_empty_query_respects_limit(self):
        assert len(rank_commands("", self._commands(), limit=2)) == 2

    def test_non_matching_commands_are_dropped(self):
        ranked = rank_commands("run", self._commands())
        assert [command.title for command in ranked] == ["Run Program"]

    def test_best_match_first(self):
        ranked = rank_commands("open file", self._commands())
        assert ranked[0].title == "Open File"

    def test_limit_caps_results(self):
        assert len(rank_commands("file", self._commands(), limit=1)) == 1

    def test_non_positive_limit_returns_everything(self):
        ranked = rank_commands("o", self._commands(), limit=0)
        assert len(ranked) >= 3

    def test_ranking_is_stable_for_equal_scores(self):
        duplicates = [
            CommandEntry(title="Same", path="A > Same"),
            CommandEntry(title="Same", path="B > Same"),
        ]
        ranked = rank_commands("same", duplicates)
        assert [command.path for command in ranked] == ["A > Same", "B > Same"]


class TestCleanActionText:
    """Qt mnemonic handling."""

    def test_removes_single_mnemonic(self):
        assert clean_action_text("&Open File") == "Open File"

    def test_keeps_literal_ampersand(self):
        assert clean_action_text("Download && Install") == "Download & Install"

    def test_strips_whitespace(self):
        assert clean_action_text("  Save  ") == "Save"


@pytest.mark.usefixtures("qapp")
class TestCollectMenuCommands:
    """Menu walking, deduplication and safety caps."""

    def test_none_menu_bar_returns_empty(self):
        assert collect_menu_commands(None) == []

    def test_collects_nested_actions_with_path(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(QAction("Open File", menu_bar))
        sub_menu = file_menu.addMenu("Recent")
        sub_menu.addAction(QAction("project.py", menu_bar))

        commands = collect_menu_commands(menu_bar)
        paths = {command.path for command in commands}
        assert "File > Open File" in paths
        assert "File > Recent > project.py" in paths

    def test_submenu_itself_is_not_a_command(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addMenu("Recent").addAction(QAction("project.py", menu_bar))

        titles = {command.title for command in collect_menu_commands(menu_bar)}
        assert "Recent" not in titles

    def test_separators_and_empty_titles_are_skipped(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(QAction("Open File", menu_bar))
        file_menu.addSeparator()
        file_menu.addAction(QAction("", menu_bar))

        assert len(collect_menu_commands(menu_bar)) == 1

    def test_disabled_actions_are_skipped(self):
        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu("File")
        disabled = QAction("Unavailable", menu_bar)
        disabled.setEnabled(False)
        file_menu.addAction(disabled)

        assert collect_menu_commands(menu_bar) == []

    def test_shortcut_is_captured(self):
        menu_bar = QMenuBar()
        action = QAction("Save File", menu_bar)
        action.setShortcut("Ctrl+S")
        menu_bar.addMenu("File").addAction(action)

        assert collect_menu_commands(menu_bar)[0].shortcut == "Ctrl+S"

    def test_payload_is_the_action(self):
        menu_bar = QMenuBar()
        action = QAction("Save File", menu_bar)
        menu_bar.addMenu("File").addAction(action)

        assert collect_menu_commands(menu_bar)[0].payload is action

    def test_shared_submenu_is_visited_once(self):
        menu_bar = QMenuBar()
        shared = QMenu("Shared")
        shared.addAction(QAction("Only Once", menu_bar))
        menu_bar.addMenu("First").addMenu(shared)
        menu_bar.addMenu("Second").addMenu(shared)

        titles = [command.title for command in collect_menu_commands(menu_bar)]
        assert titles.count("Only Once") == 1

    def test_collection_is_capped(self):
        menu_bar = QMenuBar()
        big_menu = menu_bar.addMenu("Fonts")
        for index in range(MAX_COMMANDS + 50):
            big_menu.addAction(QAction(f"Font {index}", menu_bar))

        assert len(collect_menu_commands(menu_bar)) <= MAX_COMMANDS


@pytest.mark.usefixtures("qapp")
class TestCommandPaletteDialog:
    """Live filtering and command execution in the dialog."""

    @staticmethod
    def _dialog(commands: list[CommandEntry]) -> CommandPaletteDialog:
        return CommandPaletteDialog(None, commands)

    @staticmethod
    def _sample() -> list[CommandEntry]:
        return [
            CommandEntry(title="Open File", path="File > Open File"),
            CommandEntry(title="Save File", path="File > Save File"),
            CommandEntry(title="Run Program", path="Run > Run Program"),
        ]

    def test_all_commands_listed_on_open(self):
        dialog = self._dialog(self._sample())
        assert dialog.result_list.count() == 3
        dialog.close()

    def test_first_row_selected_on_open(self):
        dialog = self._dialog(self._sample())
        assert dialog.result_list.currentRow() == 0
        dialog.close()

    def test_typing_filters_the_list(self):
        dialog = self._dialog(self._sample())
        dialog.search_input.setText("run")
        assert dialog.result_list.count() == 1
        dialog.close()

    def test_no_match_clears_the_list(self):
        dialog = self._dialog(self._sample())
        dialog.search_input.setText("xylophone")
        assert dialog.result_list.count() == 0
        dialog.close()

    def test_shortcut_is_shown_in_the_row_label(self):
        dialog = self._dialog([CommandEntry(title="Save", path="File > Save", shortcut="Ctrl+S")])
        assert "Ctrl+S" in dialog.result_list.item(0).text()
        dialog.close()

    def test_running_a_command_triggers_the_action(self, qtbot):
        triggered: list[str] = []
        action = QAction("Save File")
        action.triggered.connect(lambda: triggered.append("ran"))
        dialog = self._dialog([CommandEntry(title="Save File", path="File > Save File",
                                            payload=action)])
        dialog._run_command_at(0)
        # 觸發被延後到面板關閉之後 / The trigger is deferred until the palette closes
        qtbot.waitUntil(lambda: triggered == ["ran"], timeout=2000)

    def test_running_an_out_of_range_row_is_a_no_op(self):
        triggered: list[str] = []
        action = QAction("Save File")
        action.triggered.connect(lambda: triggered.append("ran"))
        dialog = self._dialog([CommandEntry(title="Save File", path="File > Save File",
                                            payload=action)])
        dialog._run_command_at(99)
        assert triggered == []
        dialog.close()

    def test_arrow_key_wraps_selection(self):
        dialog = self._dialog(self._sample())
        dialog._move_selection(-1)
        assert dialog.result_list.currentRow() == 2
        dialog.close()

    def test_move_selection_on_empty_list_is_a_no_op(self):
        dialog = self._dialog(self._sample())
        dialog.search_input.setText("xylophone")
        dialog._move_selection(1)
        assert dialog.result_list.currentRow() == -1
        dialog.close()
