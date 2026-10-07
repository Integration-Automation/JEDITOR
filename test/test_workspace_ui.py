"""Tests for a workspace with several roots, as the window, its panels and its dialogs see it."""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget

from je_editor.core.services.editor_services import EditorServices
from je_editor.core.workspace.workspace_model import Workspace
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.pyside_ui.main_ui.workspace import workspace_actions
from je_editor.pyside_ui.main_ui.workspace.workspace_actions import (
    add_folder_to_workspace, remove_folder_from_workspace
)
from je_editor.pyside_ui.main_ui.workspace.workspace_roots import (
    EXTRA_ROOTS_SETTING, labelled_root_paths, local_root_paths, primary_root_path,
    remember_extra_roots, restore_extra_roots, window_workspace
)
from je_editor.utils.file_scan.workspace_scan import (
    as_labelled_roots, index_workspace_files, scan_workspace_todos
)
from je_editor.utils.lint.ruff_diagnostics import Diagnostic

# Long enough that a slow machine still finishes; a hang fails rather than blocks.
TIMEOUT_MS = 10_000
ACTIONS = "je_editor.pyside_ui.main_ui.workspace.workspace_actions"


def norm(path) -> str:
    return os.path.normpath(str(path))


@pytest.fixture()
def two_roots(tmp_path):
    """Two unrelated projects, each with a ``main.py`` and a TODO in it."""
    for name in ("frontend", "backend"):
        (tmp_path / name / "src").mkdir(parents=True)
        (tmp_path / name / "main.py").write_text(f"# TODO: finish {name}\n", encoding="utf-8")
        (tmp_path / name / "src" / f"{name}_only.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path / "frontend", tmp_path / "backend"


@pytest.fixture()
def window(two_roots):
    """A stand-in for the main window whose workspace holds both projects."""
    services = EditorServices(Workspace.single_root(two_roots[0]))
    services.workspace.add_root(two_roots[1])
    return SimpleNamespace(services=services, working_dir=None, go_to_new_tab=MagicMock(),
                           tab_widget=None)


@pytest.fixture()
def _settings_untouched():
    """Put the recorded extra roots back as they were."""
    saved = user_setting_dict.get(EXTRA_ROOTS_SETTING)
    yield
    user_setting_dict[EXTRA_ROOTS_SETTING] = saved if saved is not None else []


class TestTheWindowsWorkspace:
    def test_a_window_with_services_uses_their_workspace(self, window):
        assert window_workspace(window) is window.services.workspace

    def test_every_root_is_listed_in_order(self, window, two_roots):
        assert local_root_paths(window) == [norm(two_roots[0]), norm(two_roots[1])]
        assert primary_root_path(window) == norm(two_roots[0])
        assert labelled_root_paths(window) == [
            ("frontend", norm(two_roots[0])), ("backend", norm(two_roots[1]))]

    def test_a_window_without_services_falls_back_to_its_working_directory(self, tmp_path):
        assert local_root_paths(SimpleNamespace(working_dir=str(tmp_path))) == [norm(tmp_path)]

    @pytest.mark.parametrize("stand_in", [None, SimpleNamespace(working_dir=None), MagicMock()])
    def test_a_window_that_knows_nothing_falls_back_to_the_current_directory(self, stand_in):
        assert local_root_paths(stand_in) == [norm(os.getcwd())]

    def test_a_working_directory_that_is_gone_falls_back_too(self, tmp_path):
        missing = SimpleNamespace(working_dir=str(tmp_path / "removed"))
        assert local_root_paths(missing) == [norm(os.getcwd())]

    def test_services_with_an_empty_workspace_fall_back(self, tmp_path):
        stand_in = SimpleNamespace(services=EditorServices(), working_dir=str(tmp_path))
        assert local_root_paths(stand_in) == [norm(tmp_path)]


@pytest.mark.usefixtures("_settings_untouched")
class TestRememberingTheExtraRoots:
    def test_only_the_roots_beyond_the_first_are_recorded(self, window, two_roots):
        remember_extra_roots(window.services.workspace)
        assert user_setting_dict[EXTRA_ROOTS_SETTING] == [norm(two_roots[1])]

    def test_recorded_roots_are_added_back(self, two_roots):
        user_setting_dict[EXTRA_ROOTS_SETTING] = [str(two_roots[1])]
        workspace = Workspace.single_root(two_roots[0])
        restore_extra_roots(workspace)
        assert [root.name for root in workspace.roots] == ["frontend", "backend"]

    @pytest.mark.parametrize("stored", [None, "not a list", [42, None, ""], {"a": 1}])
    def test_a_hand_edited_setting_adds_nothing(self, two_roots, stored):
        user_setting_dict[EXTRA_ROOTS_SETTING] = stored
        workspace = Workspace.single_root(two_roots[0])
        restore_extra_roots(workspace)
        assert len(workspace.roots) == 1


class TestScanningEveryRoot:
    def test_one_root_shows_paths_as_a_single_project_did(self, two_roots):
        found = index_workspace_files(as_labelled_roots(str(two_roots[0])))
        assert [item.display_path for item in found] == ["main.py", "src/frontend_only.py"]

    def test_several_roots_put_the_label_in_front(self, window):
        shown = [item.display_path for item in index_workspace_files(labelled_root_paths(window))]
        assert shown == ["frontend/main.py", "frontend/src/frontend_only.py",
                         "backend/main.py", "backend/src/backend_only.py"]

    def test_same_named_files_keep_their_own_full_paths(self, window, two_roots):
        found = {item.display_path: item.full_path
                 for item in index_workspace_files(labelled_root_paths(window))}
        assert norm(found["frontend/main.py"]) == norm(two_roots[0] / "main.py")
        assert norm(found["backend/main.py"]) == norm(two_roots[1] / "main.py")

    def test_the_limit_counts_over_all_roots(self, window):
        assert len(index_workspace_files(labelled_root_paths(window), limit=3)) == 3

    def test_stopping_yields_nothing(self, window):
        assert index_workspace_files(labelled_root_paths(window), should_stop=lambda: True) == []

    def test_todos_come_from_every_root(self, window, two_roots):
        found = scan_workspace_todos(labelled_root_paths(window))
        assert [(entry.item.path, entry.item.message) for entry in found] == [
            ("frontend/main.py", "finish frontend"), ("backend/main.py", "finish backend")]
        assert norm(found[1].full_path) == norm(two_roots[1] / "main.py")

    def test_a_plain_path_counts_as_one_root(self, two_roots):
        assert as_labelled_roots(two_roots[0]) == [("frontend", str(two_roots[0]))]


@pytest.mark.usefixtures("qapp", "_settings_untouched", "tmp_dir")
class TestAddingAndRemovingFolders:
    def test_adding_a_folder_makes_it_a_root_and_records_it(self, tmp_path, two_roots):
        services = EditorServices(Workspace.single_root(two_roots[0]))
        stand_in = SimpleNamespace(services=services)
        assert add_folder_to_workspace(stand_in, str(two_roots[1])) is True
        assert [root.name for root in services.workspace.roots] == ["frontend", "backend"]
        assert user_setting_dict[EXTRA_ROOTS_SETTING] == [norm(two_roots[1])]

    def test_the_change_is_written_to_the_settings_file_at_once(self, two_roots):
        stand_in = SimpleNamespace(services=EditorServices(Workspace.single_root(two_roots[0])))
        with patch.object(workspace_actions, "write_user_setting") as write:
            add_folder_to_workspace(stand_in, str(two_roots[1]))
        write.assert_called_once()

    def test_a_folder_already_in_the_workspace_is_reported(self, window, two_roots):
        with patch(f"{ACTIONS}.QMessageBox.information") as told:
            assert add_folder_to_workspace(window, str(two_roots[1])) is False
        assert told.call_args.args[2] == "That folder is already in the workspace"

    def test_a_folder_that_does_not_exist_is_not_added(self, window, tmp_path):
        assert add_folder_to_workspace(window, str(tmp_path / "missing")) is False
        assert len(window.services.workspace.roots) == 2

    def test_cancelling_the_folder_dialog_adds_nothing(self, window):
        with patch(f"{ACTIONS}.QFileDialog.getExistingDirectory", return_value=""):
            assert add_folder_to_workspace(window) is False

    def test_an_added_folder_can_be_removed(self, window, two_roots):
        assert remove_folder_from_workspace(window, norm(two_roots[1])) is True
        assert [root.name for root in window.services.workspace.roots] == ["frontend"]
        assert user_setting_dict[EXTRA_ROOTS_SETTING] == []

    def test_the_primary_root_cannot_be_removed_here(self, window, two_roots):
        assert remove_folder_from_workspace(window, norm(two_roots[0])) is False
        assert len(window.services.workspace.roots) == 2

    def test_nothing_to_remove_is_reported(self, two_roots):
        stand_in = SimpleNamespace(services=EditorServices(Workspace.single_root(two_roots[0])))
        with patch(f"{ACTIONS}.QMessageBox.information") as told:
            assert remove_folder_from_workspace(stand_in) is False
        assert told.call_args.args[2] == "The workspace has no added folders"

    def test_the_user_picks_the_folder_from_the_added_ones(self, window, two_roots):
        with patch(f"{ACTIONS}.QInputDialog.getItem",
                   return_value=(norm(two_roots[1]), True)) as asked:
            assert remove_folder_from_workspace(window) is True
        assert asked.call_args.args[3] == [norm(two_roots[1])]

    def test_cancelling_the_choice_removes_nothing(self, window, two_roots):
        with patch(f"{ACTIONS}.QInputDialog.getItem", return_value=(norm(two_roots[1]), False)):
            assert remove_folder_from_workspace(window) is False
        assert len(window.services.workspace.roots) == 2


@pytest.mark.usefixtures("qapp")
class TestThePanelsSeeEveryRoot:
    def test_quick_open_lists_both_roots_and_opens_the_right_file(self, qtbot, window, two_roots):
        from je_editor.pyside_ui.main_ui.command_palette.quick_open_dialog import QuickOpenDialog
        dialog = QuickOpenDialog(None, labelled_root_paths(window), [], main_window=window)
        qtbot.waitUntil(lambda: dialog.result_list.count() > 0, timeout=TIMEOUT_MS)
        entries = {entry.path: entry for entry in dialog._file_entries}
        assert sorted(entries) == ["backend/main.py", "backend/src/backend_only.py",
                                   "frontend/main.py", "frontend/src/frontend_only.py"]
        entries["backend/main.py"].payload()
        assert norm(window.go_to_new_tab.call_args.args[0]) == norm(two_roots[1] / "main.py")
        dialog.close()

    def test_the_todo_panel_scans_both_roots_and_opens_the_right_file(
            self, qtbot, window, two_roots):
        from je_editor.pyside_ui.main_ui.todo_panel.todo_panel_widget import TodoPanelWidget
        panel = TodoPanelWidget(main_window=window)
        qtbot.addWidget(panel)
        qtbot.waitUntil(lambda: panel.result_tree.topLevelItemCount() == 2, timeout=TIMEOUT_MS)
        assert [item.path for item in panel.visible_items()] == [
            "frontend/main.py", "backend/main.py"]
        panel._open_item(panel.result_tree.topLevelItem(1), 0)
        assert norm(window.go_to_new_tab.call_args.args[0]) == norm(two_roots[1] / "main.py")
        panel.close()

    def test_a_root_added_later_is_scanned_on_the_next_refresh(self, qtbot, two_roots):
        from je_editor.pyside_ui.main_ui.todo_panel.todo_panel_widget import TodoPanelWidget
        services = EditorServices(Workspace.single_root(two_roots[0]))
        panel = TodoPanelWidget(main_window=SimpleNamespace(services=services))
        qtbot.addWidget(panel)
        qtbot.waitUntil(lambda: not panel._scan_thread.isRunning(), timeout=TIMEOUT_MS)
        QApplication.processEvents()
        services.workspace.add_root(two_roots[1])
        panel.start_scan()
        qtbot.waitUntil(lambda: panel.result_tree.topLevelItemCount() == 2, timeout=TIMEOUT_MS)
        panel.close()

    def test_the_project_check_lints_every_root(self, qtbot, window, two_roots):
        from je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker import (
            ProjectLintWorker
        )

        def lint(root: str) -> list[Diagnostic]:
            return [Diagnostic(1, 1, 1, 2, "F401", f"in {Path(root).name}",
                               file_path=str(Path(root) / "main.py"))]

        worker = ProjectLintWorker(local_root_paths(window))
        with patch("je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker.lint_project",
                   side_effect=lint) as linted:
            with qtbot.waitSignal(worker.linted, timeout=TIMEOUT_MS) as blocker:
                worker.start()
            worker.wait(TIMEOUT_MS)
        assert [call.args[0] for call in linted.call_args_list] == [
            norm(two_roots[0]), norm(two_roots[1])]
        assert [item.message for item in blocker.args[0]] == ["in frontend", "in backend"]

    def test_the_problems_panel_keeps_same_named_files_apart(self, qtbot, window, two_roots):
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
            ProblemsPanelWidget
        )
        from je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker import (
            ProjectLintWorker
        )
        panel = ProblemsPanelWidget(window)
        qtbot.addWidget(panel)

        def lint(root: str) -> list[Diagnostic]:
            return [Diagnostic(1, 1, 1, 2, "F401", "unused", file_path=str(Path(root) / "main.py"))]

        with patch("je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker.lint_project",
                   side_effect=lint):
            panel.project_check.setChecked(True)
            worker = panel._project_worker
            assert isinstance(worker, ProjectLintWorker) and len(worker.roots) == 2
            worker.wait(TIMEOUT_MS)
            QApplication.processEvents()
        assert len(panel.diagnostics()) == 2
        panel.close()

    def test_a_single_root_worker_still_takes_a_plain_path(self, two_roots):
        from je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker import (
            ProjectLintWorker
        )
        worker = ProjectLintWorker(str(two_roots[0]))
        assert (worker.root, worker.roots) == (str(two_roots[0]), [str(two_roots[0])])


@pytest.mark.usefixtures("qapp")
class TestSearchingEveryRoot:
    def _search(self, qtbot, roots, pattern: str) -> list[str]:
        from je_editor.pyside_ui.dialog.search_ui.search_replace_widget import _SearchWorker
        worker = _SearchWorker(roots, pattern, case_sensitive=True, use_regex=False)
        found: list[str] = []
        worker.match_found.connect(lambda path, _line, _text: found.append(path))
        with qtbot.waitSignal(worker.finished_signal, timeout=TIMEOUT_MS):
            worker.start()
        worker.wait(TIMEOUT_MS)
        QApplication.processEvents()
        return sorted(Path(path).parent.name for path in found)

    def test_a_project_search_covers_both_roots(self, qtbot, window):
        assert self._search(qtbot, local_root_paths(window), "TODO") == ["backend", "frontend"]

    def test_a_single_folder_search_still_takes_a_plain_path(self, qtbot, two_roots):
        assert self._search(qtbot, str(two_roots[0]), "TODO") == ["frontend"]

    @pytest.fixture()
    def locate(self, window):
        from je_editor.pyside_ui.dialog.search_ui.search_replace_widget import SearchReplaceDialog
        stand_in = SimpleNamespace(_project_roots=lambda: local_root_paths(window))
        return lambda path: SearchReplaceDialog._locate_in_project(stand_in, str(path))

    def test_a_file_in_the_second_root_may_be_rewritten(self, locate, two_roots):
        root, relative = locate(two_roots[1] / "src" / "backend_only.py")
        assert (root, relative.as_posix()) == (two_roots[1].resolve(), "src/backend_only.py")

    def test_a_file_outside_every_root_is_refused(self, locate, tmp_path):
        assert locate(tmp_path / "elsewhere" / "secret.py") is None

    def test_a_path_that_climbs_out_of_a_root_is_refused(self, locate, two_roots):
        assert locate(two_roots[0] / ".." / "elsewhere" / "secret.py") is None


@pytest.fixture()
def editor_tab(qapp, window):
    """A real editor tab whose window is the two-root stand-in."""
    window.tab_widget = QTabWidget()
    window.python_compiler = None
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as venv:
        venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        widget = EditorWidget(window)
        window.tab_widget.addTab(widget, "Test")
    yield widget
    widget.close()
    widget.deleteLater()
    window.tab_widget.deleteLater()


class TestTheFileTree:
    def _shown_root(self, tab) -> str:
        return norm(tab.project_treeview_model.filePath(tab.project_treeview.rootIndex()))

    def test_the_root_list_offers_every_root(self, editor_tab, two_roots):
        offered = [editor_tab.project_root_combobox.itemData(index)
                   for index in range(editor_tab.project_root_combobox.count())]
        assert offered == [norm(two_roots[0]), norm(two_roots[1])]
        assert not editor_tab.project_root_combobox.isHidden()

    def test_the_tree_starts_on_the_primary_root(self, editor_tab, two_roots):
        assert self._shown_root(editor_tab) == norm(two_roots[0])

    def test_picking_a_root_shows_it_in_the_tree(self, editor_tab, two_roots):
        editor_tab.project_root_combobox.setCurrentIndex(1)
        assert self._shown_root(editor_tab) == norm(two_roots[1])

    def test_the_picked_root_survives_a_change_to_the_workspace(
            self, editor_tab, window, two_roots, tmp_path):
        editor_tab.project_root_combobox.setCurrentIndex(1)
        (tmp_path / "docs").mkdir()
        window.services.workspace.add_root(tmp_path / "docs")
        editor_tab.refresh_project_roots()
        assert editor_tab.project_root_combobox.count() == 3
        assert self._shown_root(editor_tab) == norm(two_roots[1])

    def test_one_root_needs_no_list(self, editor_tab, window, two_roots):
        window.services.workspace.remove_root(two_roots[1])
        editor_tab.refresh_project_roots()
        assert editor_tab.project_root_combobox.isHidden()
        assert self._shown_root(editor_tab) == norm(two_roots[0])


class TestTheLanguageServerRoot:
    def test_a_file_is_served_from_its_own_root(self, editor_tab, two_roots):
        editor_tab.code_edit.current_file = str(two_roots[1] / "src" / "lib.rs")
        assert editor_tab.code_edit._workspace_root() == norm(two_roots[1])

    def test_a_file_outside_every_root_has_no_root(self, editor_tab, tmp_path):
        editor_tab.code_edit.current_file = str(tmp_path / "elsewhere" / "lib.rs")
        assert editor_tab.code_edit._workspace_root() is None

    @staticmethod
    def _started_at(file_path: str, resolver) -> str:
        from je_editor.pyside_ui.code.lsp import lsp_client
        client = lsp_client.LspClient()
        client.root_resolver = resolver
        with patch.object(lsp_client, "server_command", return_value=["rust-analyzer"]), \
                patch.object(lsp_client.session_registry, "session_for",
                             return_value=MagicMock()) as session_for:
            client.start_for(file_path)
        client._session = None
        client.deleteLater()
        return norm(session_for.call_args.args[1])

    def test_the_session_is_started_at_the_root_the_resolver_names(self, qapp, two_roots):
        file_path = str(two_roots[1] / "src" / "lib.rs")
        asked: list[str] = []

        def resolver(path: str) -> str:
            asked.append(path)
            return norm(two_roots[1])

        assert self._started_at(file_path, resolver) == norm(two_roots[1])
        assert asked == [file_path]

    @pytest.mark.parametrize("resolver", [None, lambda _path: None, lambda _path: ""])
    def test_without_an_answer_it_starts_at_the_files_own_folder(self, qapp, two_roots, resolver):
        file_path = str(two_roots[1] / "src" / "lib.rs")
        assert self._started_at(file_path, resolver) == norm(two_roots[1] / "src")

    def test_the_editor_gives_its_client_the_workspace_as_resolver(self, editor_tab, two_roots):
        resolver = editor_tab.code_edit.lsp_client.root_resolver
        assert resolver(str(two_roots[0] / "main.rs")) == norm(two_roots[0])
        assert resolver(str(two_roots[1] / "deep" / "lib.rs")) == norm(two_roots[1])
