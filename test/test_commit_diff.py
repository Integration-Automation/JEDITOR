"""Tests for the patch a commit is shown to have made."""
from __future__ import annotations

import pytest

from je_editor.git_client.git_action import GitService

git = pytest.importorskip("git")


@pytest.fixture()
def service(tmp_path):
    """A throw-away repository whose first commit adds a file, opened by the service."""
    repository = git.Repo.init(tmp_path, initial_branch="main")
    with repository.config_writer() as config:
        config.set_value("user", "name", "Git Tester")
        config.set_value("user", "email", "git@example.com")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    repository.index.add(["tracked.txt"])
    repository.index.commit("initial")
    repository.close()
    instance = GitService()
    instance.open_repo(str(tmp_path))
    yield instance, tmp_path
    instance.close()


def _commit(instance, root, text: str, message: str) -> str:
    """Write ``text`` over the tracked file and commit it, returning the sha."""
    (root / "tracked.txt").write_text(text, encoding="utf-8")
    instance.repo.index.add(["tracked.txt"])
    return instance.repo.index.commit(message).hexsha


class TestTheDiffOfACommit:
    def test_an_added_line_reads_as_an_addition(self, service):
        instance, root = service
        sha = _commit(instance, root, "first\nsecond\n", "add a line")
        assert "+second" in instance.show_diff_of_commit(sha)

    def test_an_added_line_is_not_reported_as_a_removal(self, service):
        instance, root = service
        sha = _commit(instance, root, "first\nsecond\n", "add a line")
        assert "-second" not in instance.show_diff_of_commit(sha)

    def test_a_removed_line_reads_as_a_removal(self, service):
        instance, root = service
        sha = _commit(instance, root, "", "empty the file")
        assert "-first" in instance.show_diff_of_commit(sha)

    def test_the_first_commit_reads_as_an_addition(self, service):
        instance, _root = service
        first = list(instance.repo.iter_commits())[-1]
        assert "+first" in instance.show_diff_of_commit(first.hexsha)

    def test_it_matches_what_git_itself_prints(self, service):
        instance, root = service
        sha = _commit(instance, root, "first\nsecond\n", "add a line")
        printed = instance.repo.git.show("--format=", "--unified=0", sha)
        changed = [line for line in printed.splitlines()
                   if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
        ours = [line for line in instance.show_diff_of_commit(sha).splitlines()
                if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
        assert ours == changed
