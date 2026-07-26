"""Tests for reading git blame and showing it inline."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.git_client.file_blame import BlameLine, blame_lines

git = pytest.importorskip("git")


@pytest.fixture()
def repo(tmp_path):
    """A throw-away repository with one committed file."""
    repository = git.Repo.init(tmp_path)
    with repository.config_writer() as config:
        config.set_value("user", "name", "Blame Tester")
        config.set_value("user", "email", "blame@example.com")
    tracked = tmp_path / "tracked.py"
    tracked.write_text("first\nsecond\n", encoding="utf-8")
    repository.index.add(["tracked.py"])
    repository.index.commit("initial commit")
    yield repository, tmp_path
    repository.close()


class TestBlameLines:
    def test_every_committed_line_is_annotated(self, repo):
        _repository, root = repo
        annotations = blame_lines(root / "tracked.py")
        assert set(annotations) == {0, 1}

    def test_annotation_names_the_author_and_summary(self, repo):
        _repository, root = repo
        blame = blame_lines(root / "tracked.py")[0]
        assert blame.author == "Blame Tester"
        assert blame.summary == "initial commit"
        assert len(blame.commit) == 8

    def test_annotation_line_joins_the_parts(self, repo):
        _repository, root = repo
        annotation = blame_lines(root / "tracked.py")[0].annotation
        assert "Blame Tester" in annotation and "initial commit" in annotation

    def test_untracked_file_has_no_blame(self, repo):
        _repository, root = repo
        loose = root / "untracked.py"
        loose.write_text("x\n", encoding="utf-8")
        assert blame_lines(loose) == {}

    def test_file_outside_a_repository_has_no_blame(self, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("x\n", encoding="utf-8")
        assert blame_lines(loose) == {}

    def test_long_summary_is_shortened(self, repo):
        _repository, root = repo
        wordy = root / "wordy.py"
        wordy.write_text("x\n", encoding="utf-8")
        _repository.index.add(["wordy.py"])
        _repository.index.commit("w" * 200)
        assert blame_lines(wordy)[0].summary.endswith("…")


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
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.blame_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


SAMPLE_BLAME = {
    0: BlameLine(commit="abc12345", author="Ann", summary="first change"),
    1: BlameLine(commit="def67890", author="Bob", summary="second change"),
}


class TestBlameManager:
    def test_starts_hidden(self, editor):
        assert editor.blame_manager.enabled is False
        assert editor.blame_manager.annotation(0) == ""

    def test_annotations_are_hidden_while_disabled(self, editor):
        editor.blame_manager.set_annotations(SAMPLE_BLAME)
        assert editor.blame_manager.annotation(0) == ""

    def test_toggle_without_a_file_stays_off(self, editor):
        editor.current_file = None
        assert editor.toggle_blame() is False

    def test_annotation_is_shown_once_enabled(self, editor):
        editor.blame_manager._enabled = True
        editor.blame_manager.set_annotations(SAMPLE_BLAME)
        assert "Ann" in editor.blame_manager.annotation(0)
        assert "second change" in editor.blame_manager.annotation(1)

    def test_line_without_blame_shows_nothing(self, editor):
        editor.blame_manager._enabled = True
        editor.blame_manager.set_annotations(SAMPLE_BLAME)
        assert editor.blame_manager.annotation(9) == ""

    def test_clear_turns_it_off(self, editor):
        editor.blame_manager._enabled = True
        editor.blame_manager.set_annotations(SAMPLE_BLAME)
        editor.blame_manager.clear()
        assert editor.blame_manager.enabled is False
        assert editor.blame_manager.annotation(0) == ""

    def test_toggling_off_drops_the_annotations(self, editor, repo):
        _repository, root = repo
        editor.current_file = str(root / "tracked.py")
        assert editor.toggle_blame() is True
        editor.blame_manager.stop()
        assert editor.toggle_blame() is False
        assert editor.blame_manager.annotation(0) == ""

    def test_painting_with_annotations_does_not_raise(self, editor):
        editor.setPlainText("first\nsecond\n")
        editor.blame_manager._enabled = True
        editor.blame_manager.set_annotations(SAMPLE_BLAME)
        editor.show()
        editor.viewport().update()
        QApplication.processEvents()
        editor.hide()

    def test_stop_is_safe_without_a_loader(self, editor):
        editor.blame_manager.stop()
        editor.blame_manager.stop()
