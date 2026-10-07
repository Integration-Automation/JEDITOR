"""Tests for resource URIs and the workspace model."""
from __future__ import annotations

import os

import pytest

from je_editor.core.uri.resource_uri import is_local_uri, to_path, to_uri, uri_key, uri_scheme
from je_editor.core.workspace.workspace_model import ProjectRoot, Workspace
from je_editor.utils.exception.exceptions import JEditorServiceException

REMOTE_URI = "ssh://build-host/srv/project"


class TestResourceUri:
    def test_a_local_path_becomes_a_file_uri(self, tmp_path):
        assert to_uri(tmp_path / "a.py").startswith("file://")

    def test_a_uri_converts_back_to_the_same_path(self, tmp_path):
        target = tmp_path / "pkg" / "a.py"
        assert to_path(to_uri(target)) == os.path.normpath(str(target))

    @pytest.mark.usefixtures("tmp_dir")
    def test_a_relative_path_is_taken_from_the_working_directory(self):
        assert to_path(to_uri("a.py")) == os.path.join(os.getcwd(), "a.py")

    def test_a_remote_uri_has_no_local_path(self):
        assert to_path(REMOTE_URI) == ""

    @pytest.mark.parametrize("uri, expected", [
        ("file:///tmp/a.py", True), (REMOTE_URI, False), ("", False), (None, False),
    ])
    def test_only_file_uris_are_local(self, uri, expected):
        assert is_local_uri(uri) is expected

    @pytest.mark.parametrize("uri, expected", [
        ("file:///tmp/a.py", "file"), (REMOTE_URI, "ssh"), ("SSH://host/x", "ssh"),
        ("no scheme here", ""), (None, ""),
    ])
    def test_the_scheme_is_read_in_lower_case(self, uri, expected):
        assert uri_scheme(uri) == expected

    def test_two_spellings_of_one_file_share_a_key(self, tmp_path):
        direct = to_uri(tmp_path / "a.py")
        roundabout = to_uri(tmp_path / "pkg" / ".." / "a.py")
        assert uri_key(direct) == uri_key(roundabout)

    @pytest.mark.skipif(os.path.normcase("A") == "A", reason="this file system is case-sensitive")
    def test_case_does_not_matter_where_the_file_system_ignores_it(self, tmp_path):
        uri = to_uri(tmp_path / "Module.py")
        assert uri_key(uri) == uri_key(uri.replace("Module", "MODULE"))

    def test_different_files_have_different_keys(self, tmp_path):
        assert uri_key(to_uri(tmp_path / "a.py")) != uri_key(to_uri(tmp_path / "b.py"))

    def test_a_remote_uri_is_its_own_key(self):
        assert uri_key(REMOTE_URI) == REMOTE_URI


class TestProjectRoot:
    def test_the_name_defaults_to_the_directory_name(self, tmp_path):
        assert ProjectRoot.from_path(tmp_path / "service").name == "service"

    def test_a_given_name_is_kept(self, tmp_path):
        assert ProjectRoot.from_path(tmp_path, name="Backend").name == "Backend"

    def test_the_path_comes_back_out_of_the_uri(self, tmp_path):
        assert ProjectRoot.from_path(tmp_path).path == os.path.normpath(str(tmp_path))

    def test_a_directory_that_does_not_exist_is_still_a_root(self, tmp_path):
        root = ProjectRoot.from_path(tmp_path / "not-created-yet")
        assert root.is_local

    def test_a_remote_root_is_not_local_and_has_no_path(self):
        root = ProjectRoot(uri=REMOTE_URI, name="build")
        assert not root.is_local
        assert root.path == ""

    def test_a_file_inside_is_contained(self, tmp_path):
        assert ProjectRoot.from_path(tmp_path).contains(tmp_path / "pkg" / "a.py")

    def test_the_root_contains_itself(self, tmp_path):
        assert ProjectRoot.from_path(tmp_path).contains(tmp_path)

    def test_a_sibling_with_the_same_prefix_is_not_contained(self, tmp_path):
        root = ProjectRoot.from_path(tmp_path / "app")
        assert not root.contains(tmp_path / "app-old" / "a.py")

    def test_a_remote_root_contains_no_local_path(self, tmp_path):
        assert not ProjectRoot(uri=REMOTE_URI, name="build").contains(tmp_path)

    def test_resolve_joins_a_relative_path_onto_the_root(self, tmp_path):
        resolved = ProjectRoot.from_path(tmp_path).resolve("pkg/a.py")
        assert resolved == os.path.normpath(str(tmp_path / "pkg" / "a.py"))

    @pytest.mark.parametrize("escape", ["../outside.py", "pkg/../../outside.py"])
    def test_resolve_refuses_to_leave_the_root(self, tmp_path, escape):
        root = ProjectRoot.from_path(tmp_path / "project")
        with pytest.raises(JEditorServiceException, match="leaves the project root"):
            root.resolve(escape)

    def test_resolve_refuses_an_absolute_path_outside_the_root(self, tmp_path):
        root = ProjectRoot.from_path(tmp_path / "project")
        with pytest.raises(JEditorServiceException, match="leaves the project root"):
            root.resolve(str(tmp_path / "elsewhere" / "a.py"))

    def test_resolve_needs_a_local_root(self):
        with pytest.raises(JEditorServiceException, match="not a local root"):
            ProjectRoot(uri=REMOTE_URI, name="build").resolve("a.py")


class TestWorkspace:
    def test_a_new_workspace_has_no_roots(self):
        workspace = Workspace()
        assert workspace.roots == ()
        assert workspace.primary_root is None
        assert not workspace.is_multi_root

    def test_a_single_root_workspace_is_the_old_project_directory(self, tmp_path):
        workspace = Workspace.single_root(tmp_path)
        assert [root.path for root in workspace.roots] == [os.path.normpath(str(tmp_path))]
        assert workspace.primary_root == workspace.roots[0]
        assert not workspace.is_multi_root

    def test_roots_keep_the_order_they_were_added_in(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path / "zeta")
        workspace.add_root(tmp_path / "alpha")
        assert [root.name for root in workspace.roots] == ["zeta", "alpha"]
        assert workspace.is_multi_root

    def test_the_same_directory_is_not_added_twice(self, tmp_path):
        workspace = Workspace.single_root(tmp_path)
        assert workspace.add_root(tmp_path / "pkg" / "..") is False
        assert len(workspace.roots) == 1

    def test_a_remote_root_sits_beside_a_local_one(self, tmp_path):
        workspace = Workspace.single_root(tmp_path)
        assert workspace.add_root(ProjectRoot(uri=REMOTE_URI, name="build")) is True
        assert [root.is_local for root in workspace.roots] == [True, False]

    @pytest.mark.parametrize("spelling", ["root", "path", "uri"])
    def test_a_root_can_be_removed_however_it_is_named(self, tmp_path, spelling):
        workspace = Workspace.single_root(tmp_path)
        root = workspace.roots[0]
        target = {"root": root, "path": tmp_path, "uri": root.uri}[spelling]
        assert workspace.remove_root(target) is True
        assert workspace.roots == ()

    def test_removing_an_unknown_root_changes_nothing(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "app")
        assert workspace.remove_root(tmp_path / "other") is False
        assert len(workspace.roots) == 1

    def test_a_remote_root_is_removed_by_its_uri(self):
        workspace = Workspace([ProjectRoot(uri=REMOTE_URI, name="build")])
        assert workspace.remove_root(REMOTE_URI) is True

    def test_a_file_belongs_to_the_root_that_holds_it(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path / "frontend")
        workspace.add_root(tmp_path / "backend")
        owner = workspace.root_for(tmp_path / "backend" / "api.py")
        assert owner is not None and owner.name == "backend"

    def test_the_deepest_root_wins_when_roots_nest(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path)
        workspace.add_root(tmp_path / "vendor" / "library")
        owner = workspace.root_for(tmp_path / "vendor" / "library" / "x.py")
        assert owner is not None and owner.name == "library"

    def test_a_file_outside_every_root_has_no_owner(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "app")
        assert workspace.root_for(tmp_path / "elsewhere" / "x.py") is None
        assert workspace.relative_path(tmp_path / "elsewhere" / "x.py") is None

    def test_a_local_document_finds_its_root_by_uri(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path / "frontend")
        workspace.add_root(tmp_path / "backend")
        owner = workspace.root_for_uri(to_uri(tmp_path / "backend" / "api.py"))
        assert owner is not None and owner.name == "backend"

    def test_a_remote_document_finds_its_remote_root(self, tmp_path):
        workspace = Workspace.single_root(tmp_path)
        workspace.add_root(ProjectRoot(uri=REMOTE_URI, name="build"))
        owner = workspace.root_for_uri(f"{REMOTE_URI}/src/main.py")
        assert owner is not None and owner.name == "build"

    def test_the_deepest_remote_root_wins(self):
        workspace = Workspace([
            ProjectRoot(uri=REMOTE_URI, name="build"),
            ProjectRoot(uri=f"{REMOTE_URI}/vendor", name="vendor"),
        ])
        owner = workspace.root_for_uri(f"{REMOTE_URI}/vendor/lib.py")
        assert owner is not None and owner.name == "vendor"

    @pytest.mark.parametrize("uri", [
        f"{REMOTE_URI}-old/src/main.py", "ssh://other-host/srv/project/main.py",
    ])
    def test_a_resource_outside_every_remote_root_has_no_owner(self, uri):
        workspace = Workspace([ProjectRoot(uri=REMOTE_URI, name="build")])
        assert workspace.root_for_uri(uri) is None

    def test_same_named_files_in_two_roots_do_not_collide(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path / "frontend")
        workspace.add_root(tmp_path / "backend")
        first = workspace.relative_path(tmp_path / "frontend" / "src" / "main.py")
        second = workspace.relative_path(tmp_path / "backend" / "src" / "main.py")
        assert first is not None and second is not None
        assert first[1] == second[1] == "src/main.py"
        assert first[0] != second[0]

    def test_setting_the_roots_replaces_them_all_in_one_announcement(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "old")
        workspace.add_root(tmp_path / "extra")
        announced = []
        workspace.changed.subscribe(lambda changed: announced.append(len(changed.roots)))
        assert workspace.set_roots([tmp_path / "new"]) is True
        assert [root.name for root in workspace.roots] == ["new"]
        assert announced == [1]

    def test_setting_the_same_roots_changes_nothing(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "app")
        announced = []
        workspace.changed.subscribe(announced.append)
        assert workspace.set_roots([tmp_path / "app"]) is False
        assert announced == []

    def test_setting_roots_drops_a_repeated_one(self, tmp_path):
        workspace = Workspace()
        workspace.set_roots([tmp_path / "app", tmp_path / "pkg" / ".." / "app", tmp_path / "lib"])
        assert [root.name for root in workspace.roots] == ["app", "lib"]

    def test_roots_of_the_same_name_get_distinct_labels(self, tmp_path):
        workspace = Workspace()
        for parent in ("one", "two", "three"):
            workspace.add_root(tmp_path / parent / "src")
        workspace.add_root(tmp_path / "docs")
        assert [label for label, _root in workspace.labelled_roots()] == [
            "src", "src (2)", "src (3)", "docs"]

    def test_one_root_shows_the_path_inside_it(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "app")
        assert workspace.display_path(tmp_path / "app" / "pkg" / "main.py") == "pkg/main.py"

    def test_several_roots_put_the_label_in_front(self, tmp_path):
        workspace = Workspace()
        workspace.add_root(tmp_path / "frontend")
        workspace.add_root(tmp_path / "backend")
        assert workspace.display_path(tmp_path / "backend" / "src" / "main.py") == "backend/src/main.py"
        assert workspace.display_path(tmp_path / "frontend") == "frontend"

    def test_a_path_outside_every_root_is_shown_in_full(self, tmp_path):
        workspace = Workspace.single_root(tmp_path / "app")
        outside = tmp_path / "elsewhere" / "x.py"
        assert workspace.display_path(outside) == outside.as_posix()

    @pytest.mark.parametrize("roots", [["app"], ["frontend", "backend"], ["one/src", "two/src"]])
    def test_a_shown_path_leads_back_to_the_file(self, tmp_path, roots):
        workspace = Workspace()
        for root in roots:
            workspace.add_root(tmp_path / root)
        target = tmp_path / roots[-1] / "pkg" / "main.py"
        shown = workspace.display_path(target)
        assert workspace.resolve_display_path(shown) == os.path.normpath(str(target))

    @pytest.mark.parametrize("shown", ["unknown-root/main.py", "frontend/../../escape.py"])
    def test_a_shown_path_that_matches_nothing_resolves_to_none(self, tmp_path, shown):
        workspace = Workspace()
        workspace.add_root(tmp_path / "frontend")
        workspace.add_root(tmp_path / "backend")
        assert workspace.resolve_display_path(shown) is None

    def test_an_empty_workspace_resolves_nothing(self):
        assert Workspace().resolve_display_path("main.py") is None

    def test_changes_are_announced_once_each(self, tmp_path):
        workspace = Workspace()
        announced = []
        workspace.changed.subscribe(lambda changed: announced.append(len(changed.roots)))
        workspace.add_root(tmp_path / "a")
        workspace.add_root(tmp_path / "a")
        workspace.remove_root(tmp_path / "a")
        workspace.remove_root(tmp_path / "a")
        assert announced == [1, 0]
