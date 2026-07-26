"""Tests that the git panel reaches the stash and conflict operations."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

git = pytest.importorskip("git")


@pytest.fixture()
def repo(tmp_path):
    """A throw-away repository with one committed file."""
    repository = git.Repo.init(tmp_path, initial_branch="main")
    with repository.config_writer() as config:
        config.set_value("user", "name", "Panel Tester")
        config.set_value("user", "email", "panel@example.com")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    repository.index.add(["tracked.txt"])
    repository.index.commit("initial")
    repository.close()
    return tmp_path


@pytest.fixture()
def panel(qapp, qtbot, repo):
    """The git panel with a repository open."""
    from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
    with patch.object(GitGui, "_restore_last_opened_repository", lambda self: None):
        widget = GitGui()
    qtbot.addWidget(widget)
    widget._load_repository_from_path(repo)
    yield widget, repo
    widget.close()


class TestTheButtonsExist:
    """
    The operations had tests but no way to reach them: GitService had no UI
    consumer at all, since the panel talks to GitPython directly.
    """

    def test_stashing_is_offered(self, panel):
        widget, _repo = panel
        assert widget.stash_button.isEnabled() is True

    def test_popping_is_offered(self, panel):
        widget, _repo = panel
        assert widget.stash_pop_button.isEnabled() is True

    def test_resolving_is_offered(self, panel):
        widget, _repo = panel
        assert widget.resolve_button.isEnabled() is True

    def test_they_are_disabled_without_a_repository(self, qapp, qtbot):
        from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
        with patch.object(GitGui, "_restore_last_opened_repository", lambda self: None):
            widget = GitGui()
        qtbot.addWidget(widget)
        assert widget.stash_button.isEnabled() is False
        widget.close()


class TestStashingFromThePanel:
    def test_stashing_puts_the_change_away(self, panel):
        widget, repo = panel
        (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        widget.on_stash_changes()
        assert (repo / "tracked.txt").read_text(encoding="utf-8") == "first\n"

    def test_the_message_box_is_used_as_the_stash_name(self, panel):
        widget, repo = panel
        (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        widget.commit_message_input.setText("half done")
        widget.on_stash_changes()
        assert any("half done" in line for line in widget._service().stash_list())

    def test_the_message_is_cleared_afterwards(self, panel):
        widget, repo = panel
        (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        widget.commit_message_input.setText("half done")
        widget.on_stash_changes()
        assert widget.commit_message_input.text() == ""

    def test_popping_brings_it_back(self, panel):
        widget, repo = panel
        (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
        widget.on_stash_changes()
        with patch(
            "je_editor.pyside_ui.git_ui.git_client.git_client_gui.QInputDialog.getItem",
            side_effect=lambda *args, **kwargs: (args[3][0], True),
        ):
            widget.on_pop_stash()
        assert (repo / "tracked.txt").read_text(encoding="utf-8") == "changed\n"

    def test_popping_with_nothing_stashed_says_so(self, panel):
        widget, _repo = panel
        with patch(
            "je_editor.pyside_ui.git_ui.git_client.git_client_gui.QMessageBox.information"
        ) as told:
            widget.on_pop_stash()
        assert told.called

    def test_a_service_is_only_built_once(self, panel):
        widget, _repo = panel
        assert widget._service() is widget._service()

    def test_no_repository_means_no_service(self, qapp, qtbot):
        from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
        with patch.object(GitGui, "_restore_last_opened_repository", lambda self: None):
            widget = GitGui()
        qtbot.addWidget(widget)
        assert widget._service() is None
        widget.close()


class TestResolvingFromThePanel:
    @staticmethod
    def _conflict(repo):
        repository = git.Repo(repo)
        repository.git.checkout("-b", "other")
        (repo / "tracked.txt").write_text("theirs\n", encoding="utf-8")
        repository.index.add(["tracked.txt"])
        repository.index.commit("theirs")
        repository.git.checkout("main")
        (repo / "tracked.txt").write_text("ours\n", encoding="utf-8")
        repository.index.add(["tracked.txt"])
        repository.index.commit("ours")
        try:
            repository.git.merge("other")
        except git.GitCommandError:
            pass
        repository.close()

    def test_nothing_in_conflict_says_so(self, panel):
        widget, _repo = panel
        with patch(
            "je_editor.pyside_ui.git_ui.git_client.git_client_gui.QMessageBox.information"
        ) as told:
            widget.on_resolve_conflict()
        assert told.called

    def test_keeping_one_side_settles_it(self, panel):
        widget, repo = panel
        self._conflict(repo)
        answers = iter([("tracked.txt", True), ("theirs", True)])
        with patch(
            "je_editor.pyside_ui.git_ui.git_client.git_client_gui.QInputDialog.getItem",
            side_effect=lambda *args, **kwargs: next(answers),
        ):
            widget.on_resolve_conflict()
        assert (repo / "tracked.txt").read_text(encoding="utf-8") == "theirs\n"

    def test_cancelling_leaves_the_conflict(self, panel):
        widget, repo = panel
        self._conflict(repo)
        with patch(
            "je_editor.pyside_ui.git_ui.git_client.git_client_gui.QInputDialog.getItem",
            return_value=("tracked.txt", False),
        ):
            widget.on_resolve_conflict()
        assert widget._service().conflicted_files() == ["tracked.txt"]


class TestClosingThePanel:
    def test_background_work_is_waited_for(self, panel):
        # The panel's threads hang off it, and Qt aborts the process if one
        # outlives the widget it belongs to.
        widget, _repo = panel
        widget._bg_threads = [(MagicMock(isRunning=MagicMock(return_value=True)), MagicMock())]
        thread = widget._bg_threads[0][0]
        widget.close()
        thread.wait.assert_called_once()

    def test_a_thread_already_gone_is_tolerated(self, panel):
        widget, _repo = panel
        dead = MagicMock()
        dead.isRunning.side_effect = RuntimeError("already deleted")
        widget._bg_threads = [(dead, MagicMock())]
        widget.close()
        assert widget._bg_threads == []
