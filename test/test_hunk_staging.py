"""Tests for staging one hunk and comparing staged against working."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.git_client.file_staging import (
    commit_index, stage_content, staged_text, unstage_file
)
from je_editor.utils.file_diff.line_status import apply_hunk, hunk_at_line

git = pytest.importorskip("git")


class TestApplyHunk:
    def test_only_the_named_hunk_is_applied(self):
        baseline = "a\nb\nc\nd\n"
        current = "A\nb\nc\nD\n"
        first = hunk_at_line(baseline, current, 0)
        assert apply_hunk(baseline, current, first) == "A\nb\nc\nd\n"

    def test_the_other_hunk_applies_on_its_own(self):
        baseline = "a\nb\nc\nd\n"
        current = "A\nb\nc\nD\n"
        last = hunk_at_line(baseline, current, 3)
        assert apply_hunk(baseline, current, last) == "a\nb\nc\nD\n"

    def test_an_added_line_is_inserted(self):
        baseline = "a\nb\n"
        current = "a\nnew\nb\n"
        hunk = hunk_at_line(baseline, current, 1)
        assert apply_hunk(baseline, current, hunk) == "a\nnew\nb\n"

    def test_a_deleted_line_is_removed(self):
        baseline = "a\nb\nc\n"
        current = "a\nc\n"
        hunk = hunk_at_line(baseline, current, 1)
        assert apply_hunk(baseline, current, hunk) == "a\nc\n"

    def test_emptying_a_file_yields_empty_content(self):
        baseline = "a\n"
        hunk = hunk_at_line(baseline, "", 0)
        assert hunk is None or apply_hunk(baseline, "", hunk) == ""


@pytest.fixture()
def repo(tmp_path):
    """A throw-away repository with one committed file."""
    repository = git.Repo.init(tmp_path)
    with repository.config_writer() as config:
        config.set_value("user", "name", "Stage Tester")
        config.set_value("user", "email", "stage@example.com")
    tracked = tmp_path / "tracked.py"
    tracked.write_text("a\nb\nc\n", encoding="utf-8")
    repository.index.add(["tracked.py"])
    repository.index.commit("initial")
    repository.close()
    yield tmp_path


class TestStaging:
    def test_staged_text_reads_the_index(self, repo):
        assert staged_text(repo / "tracked.py") == "a\nb\nc\n"

    def test_staging_updates_the_index_only(self, repo):
        tracked = repo / "tracked.py"
        tracked.write_text("a\nWORKING\nc\n", encoding="utf-8")
        assert stage_content(tracked, "a\nSTAGED\nc\n") is True
        assert staged_text(tracked) == "a\nSTAGED\nc\n"
        # The working tree keeps what the user is editing.
        assert tracked.read_text(encoding="utf-8") == "a\nWORKING\nc\n"

    def test_staging_one_hunk_leaves_the_other_committed(self, repo):
        tracked = repo / "tracked.py"
        baseline = "a\nb\nc\n"
        current = "A\nb\nC\n"
        tracked.write_text(current, encoding="utf-8")
        first = hunk_at_line(baseline, current, 0)
        stage_content(tracked, apply_hunk(baseline, current, first))
        assert staged_text(tracked) == "A\nb\nc\n"

    def test_a_file_outside_a_repository_cannot_be_staged(self, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("x\n", encoding="utf-8")
        assert stage_content(loose, "y\n") is False
        assert staged_text(loose) is None

    def test_an_untracked_file_has_no_staged_text(self, repo):
        new_file = repo / "untracked.py"
        new_file.write_text("x\n", encoding="utf-8")
        assert staged_text(new_file) is None


class TestUnstaging:
    """The only way back from staging a hunk that should not have been staged."""

    def test_the_index_returns_to_the_committed_content(self, repo):
        tracked = repo / "tracked.py"
        stage_content(tracked, "a\nSTAGED\nc\n")
        assert unstage_file(tracked) is True
        assert staged_text(tracked) == "a\nb\nc\n"

    def test_the_working_tree_is_left_alone(self, repo):
        tracked = repo / "tracked.py"
        tracked.write_text("a\nWORKING\nc\n", encoding="utf-8")
        stage_content(tracked, "a\nSTAGED\nc\n")
        unstage_file(tracked)
        assert tracked.read_text(encoding="utf-8") == "a\nWORKING\nc\n"

    def test_a_never_committed_file_leaves_the_index(self, repo):
        new_file = repo / "fresh.py"
        new_file.write_text("x\n", encoding="utf-8")
        stage_content(new_file, "x\n")
        assert unstage_file(new_file) is True
        assert staged_text(new_file) is None

    def test_a_file_that_was_never_staged_changes_nothing(self, repo):
        new_file = repo / "never.py"
        new_file.write_text("x\n", encoding="utf-8")
        assert unstage_file(new_file) is False

    def test_a_file_outside_a_repository_cannot_be_unstaged(self, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("x\n", encoding="utf-8")
        assert unstage_file(loose) is False


class TestCommittingTheIndex:
    """Staging hunk by hunk is only useful if the index is what gets committed."""

    def test_only_the_staged_content_is_committed(self, repo):
        tracked = repo / "tracked.py"
        tracked.write_text("a\nWORKING\nc\n", encoding="utf-8")
        stage_content(tracked, "a\nSTAGED\nc\n")
        assert commit_index(tracked, "stage only") is True
        repository = git.Repo(repo)
        committed = (repository.head.commit.tree / "tracked.py").data_stream.read()
        repository.close()
        assert committed.decode("utf-8") == "a\nSTAGED\nc\n"

    def test_the_working_tree_keeps_the_unstaged_edit(self, repo):
        tracked = repo / "tracked.py"
        tracked.write_text("a\nWORKING\nc\n", encoding="utf-8")
        stage_content(tracked, "a\nSTAGED\nc\n")
        commit_index(tracked, "stage only")
        assert tracked.read_text(encoding="utf-8") == "a\nWORKING\nc\n"

    def test_an_empty_message_is_refused(self, repo):
        assert commit_index(repo / "tracked.py", "   ") is False

    def test_a_file_outside_a_repository_cannot_be_committed(self, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("x\n", encoding="utf-8")
        assert commit_index(loose, "message") is False


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
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.close()
    code_editor.deleteLater()


class TestEditorStaging:
    def test_staging_the_hunk_under_the_caret(self, editor, repo):
        tracked = repo / "tracked.py"
        editor.current_file = str(tracked)
        editor.setPlainText("A\nb\nC\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        assert editor.stage_change_at_cursor() is True
        assert staged_text(tracked) == "A\nb\nc\n"

    def test_staging_without_a_baseline_is_refused(self, editor):
        editor.setPlainText("x\n")
        assert editor.stage_change_at_cursor() is False

    def test_staging_an_unchanged_line_is_refused(self, editor, repo):
        editor.current_file = str(repo / "tracked.py")
        editor.setPlainText("a\nb\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        assert editor.stage_change_at_cursor() is False

    def test_staged_diff_shows_the_unstaged_edit(self, editor, repo):
        tracked = repo / "tracked.py"
        editor.current_file = str(tracked)
        editor.setPlainText("a\nEDITED\nc\n")
        diff = editor.staged_diff_text()
        assert "-b" in diff and "+EDITED" in diff

    def test_no_diff_without_a_file(self, editor):
        editor.current_file = None
        assert editor.staged_diff_text() == ""
