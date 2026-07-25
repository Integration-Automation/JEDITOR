"""Tests for reading a file's committed content as the diff baseline."""
from __future__ import annotations

import pytest

from je_editor.git_client.file_baseline import baseline_text, open_repository

git = pytest.importorskip("git")


@pytest.fixture()
def repo(tmp_path):
    """A throw-away repository with one committed file."""
    repository = git.Repo.init(tmp_path)
    with repository.config_writer() as config:
        config.set_value("user", "name", "Test")
        config.set_value("user", "email", "test@example.com")
    tracked = tmp_path / "tracked.py"
    tracked.write_text("first\nsecond\n", encoding="utf-8")
    repository.index.add(["tracked.py"])
    repository.index.commit("initial")
    yield repository, tmp_path
    repository.close()


class TestOpenRepository:
    def test_finds_the_repository_of_a_tracked_file(self, repo):
        _repository, root = repo
        assert open_repository(root / "tracked.py") is not None

    def test_finds_the_repository_from_a_subdirectory(self, repo):
        _repository, root = repo
        nested = root / "pkg"
        nested.mkdir()
        assert open_repository(nested / "module.py") is not None

    def test_path_outside_any_repository(self, tmp_path):
        assert open_repository(tmp_path / "loose.py") is None


class TestBaselineText:
    def test_committed_content_is_returned(self, repo):
        _repository, root = repo
        assert baseline_text(root / "tracked.py") == "first\nsecond\n"

    def test_working_tree_edits_do_not_change_the_baseline(self, repo):
        _repository, root = repo
        tracked = root / "tracked.py"
        tracked.write_text("first\nCHANGED\n", encoding="utf-8")
        assert baseline_text(tracked) == "first\nsecond\n"

    def test_uncommitted_file_has_no_baseline(self, repo):
        _repository, root = repo
        new_file = root / "untracked.py"
        new_file.write_text("brand new\n", encoding="utf-8")
        assert baseline_text(new_file) is None

    def test_file_outside_a_repository_has_no_baseline(self, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("x\n", encoding="utf-8")
        assert baseline_text(loose) is None

    def test_missing_file_has_no_baseline(self, tmp_path):
        assert baseline_text(tmp_path / "gone.py") is None

    def test_line_endings_are_normalised(self, repo):
        # A repository may store CRLF (or be committed through a client that
        # does); the editor's document always uses \n, so the baseline must too.
        _repository, root = repo
        crlf = root / "crlf.py"
        crlf.write_bytes(b"first\r\nsecond\r\n")
        _repository.index.add(["crlf.py"])
        _repository.index.commit("add crlf file")
        assert baseline_text(crlf) == "first\nsecond\n"

    def test_binary_content_has_no_baseline(self, repo):
        _repository, root = repo
        blob = root / "logo.bin"
        blob.write_bytes(b"\xff\xfe\x00\x01binary")
        _repository.index.add(["logo.bin"])
        _repository.index.commit("add binary")
        assert baseline_text(blob) is None
