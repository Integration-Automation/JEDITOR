"""Tests for stashing, listing conflicts and resolving them."""
from __future__ import annotations

import pytest

from je_editor.git_client.git_action import GitService

git = pytest.importorskip("git")


@pytest.fixture()
def service(tmp_path):
    """A throw-away repository with one committed file, opened by the service."""
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
    instance.repo.close()


class TestStashing:
    def test_a_change_can_be_put_away(self, service):
        instance, root = service
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        instance.stash_save("wip")
        assert (root / "tracked.txt").read_text(encoding="utf-8") == "first\n"

    def test_the_stash_is_listed(self, service):
        instance, root = service
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        instance.stash_save("wip")
        assert any("wip" in line for line in instance.stash_list())

    def test_nothing_is_stashed_when_nothing_changed(self, service):
        instance, _root = service
        instance.stash_save("empty")
        assert instance.stash_list() == []

    def test_taking_it_back_restores_the_change(self, service):
        instance, root = service
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        instance.stash_save("wip")
        instance.stash_pop()
        assert (root / "tracked.txt").read_text(encoding="utf-8") == "changed\n"

    def test_taking_it_back_removes_it_from_the_list(self, service):
        instance, root = service
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        instance.stash_save("wip")
        instance.stash_pop()
        assert instance.stash_list() == []

    def test_a_stash_without_a_message_still_works(self, service):
        instance, root = service
        (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
        instance.stash_save()
        assert len(instance.stash_list()) == 1


def _make_conflict(instance, root) -> None:
    """Merge two branches that changed the same line, leaving a conflict."""
    repository = instance.repo
    repository.git.checkout("-b", "other")
    (root / "tracked.txt").write_text("theirs\n", encoding="utf-8")
    repository.index.add(["tracked.txt"])
    repository.index.commit("theirs")
    repository.git.checkout("main")
    (root / "tracked.txt").write_text("ours\n", encoding="utf-8")
    repository.index.add(["tracked.txt"])
    repository.index.commit("ours")
    try:
        repository.git.merge("other")
    except git.GitCommandError:
        # The merge is meant to fail; the conflict is the point.
        pass


class TestConflicts:
    def test_a_clean_repository_has_none(self, service):
        instance, _root = service
        assert instance.conflicted_files() == []

    def test_a_conflicted_file_is_listed(self, service):
        instance, root = service
        _make_conflict(instance, root)
        assert instance.conflicted_files() == ["tracked.txt"]

    def test_keeping_our_side_resolves_it(self, service):
        instance, root = service
        _make_conflict(instance, root)
        assert instance.resolve_conflict("tracked.txt", "ours") is True
        assert (root / "tracked.txt").read_text(encoding="utf-8") == "ours\n"

    def test_keeping_their_side_resolves_it(self, service):
        instance, root = service
        _make_conflict(instance, root)
        assert instance.resolve_conflict("tracked.txt", "theirs") is True
        assert (root / "tracked.txt").read_text(encoding="utf-8") == "theirs\n"

    def test_resolving_clears_it_from_the_list(self, service):
        instance, root = service
        _make_conflict(instance, root)
        instance.resolve_conflict("tracked.txt", "ours")
        assert instance.conflicted_files() == []

    def test_an_unknown_side_is_refused(self, service):
        instance, root = service
        _make_conflict(instance, root)
        assert instance.resolve_conflict("tracked.txt", "either") is False

    def test_resolving_a_file_that_is_not_in_conflict_reports_failure(self, service):
        instance, _root = service
        assert instance.resolve_conflict("tracked.txt", "ours") is False


class TestWithoutARepository:
    def test_stashing_needs_an_open_repository(self):
        unopened = GitService()
        with pytest.raises(RuntimeError):
            unopened.stash_save("wip")

    def test_listing_conflicts_needs_an_open_repository(self):
        unopened = GitService()
        with pytest.raises(RuntimeError):
            unopened.conflicted_files()
