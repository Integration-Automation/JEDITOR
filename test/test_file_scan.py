"""Tests for the shared project scan rules and the quick open file indexer."""
from __future__ import annotations

from je_editor.utils.file_scan.file_indexer import (
    MAX_INDEX_DEPTH,
    build_file_entries,
    index_project_files,
)
from je_editor.utils.file_scan.ignore_rules import (
    is_binary_file,
    is_ignored_directory,
    is_ignored_file,
)


class TestIgnoreRules:
    """Directory, suffix and binary detection rules."""

    def test_vcs_directory_is_ignored(self):
        assert is_ignored_directory(".git")

    def test_cache_directory_is_ignored(self):
        assert is_ignored_directory("__pycache__")

    def test_source_directory_is_kept(self):
        assert not is_ignored_directory("je_editor")

    def test_dot_directory_not_in_list_is_kept(self):
        # .github holds editable workflow files, so it must stay searchable.
        assert not is_ignored_directory(".github")

    def test_compiled_suffix_is_ignored(self):
        assert is_ignored_file("module.pyc")

    def test_suffix_check_is_case_insensitive(self):
        assert is_ignored_file("IMAGE.PNG")

    def test_source_file_is_kept(self):
        assert not is_ignored_file("main.py")

    def test_extensionless_file_is_kept(self):
        assert not is_ignored_file("Makefile")

    def test_text_file_is_not_binary(self, tmp_path):
        text_file = tmp_path / "sample.py"
        text_file.write_text("print('hi')\n", encoding="utf-8")
        assert not is_binary_file(text_file)

    def test_null_byte_file_is_binary(self, tmp_path):
        binary_file = tmp_path / "sample.bin"
        binary_file.write_bytes(b"MZ\x00\x90")
        assert is_binary_file(binary_file)

    def test_missing_file_is_reported_as_binary(self, tmp_path):
        # Unreadable files are reported binary so callers skip them safely.
        assert is_binary_file(tmp_path / "does_not_exist.py")


class TestIndexProjectFiles:
    """Walking, pruning, limiting and cancellation."""

    @staticmethod
    def _make_project(tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "helper.py").write_text("y = 2\n", encoding="utf-8")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "main.cpython-311.pyc").write_bytes(b"\x00")
        (tmp_path / "assets").mkdir()
        (tmp_path / "assets" / "logo.png").write_bytes(b"\x89PNG")
        return tmp_path

    def test_missing_root_returns_empty(self, tmp_path):
        assert index_project_files(tmp_path / "nope") == []

    def test_file_as_root_returns_empty(self, tmp_path):
        target = tmp_path / "main.py"
        target.write_text("x = 1\n", encoding="utf-8")
        assert index_project_files(target) == []

    def test_finds_nested_source_files(self, tmp_path):
        found = index_project_files(self._make_project(tmp_path))
        assert "main.py" in found
        assert "pkg/helper.py" in found

    def test_ignored_directories_are_pruned(self, tmp_path):
        found = index_project_files(self._make_project(tmp_path))
        assert not any(path.startswith("__pycache__") for path in found)

    def test_ignored_suffixes_are_skipped(self, tmp_path):
        found = index_project_files(self._make_project(tmp_path))
        assert "assets/logo.png" not in found

    def test_paths_use_forward_slashes(self, tmp_path):
        found = index_project_files(self._make_project(tmp_path))
        assert all("\\" not in path for path in found)

    def test_results_are_sorted(self, tmp_path):
        found = index_project_files(self._make_project(tmp_path))
        assert found == sorted(found)

    def test_limit_caps_the_result(self, tmp_path):
        for index in range(20):
            (tmp_path / f"file_{index}.py").write_text("x = 1\n", encoding="utf-8")
        assert len(index_project_files(tmp_path, limit=5)) == 5

    def test_should_stop_aborts_the_walk(self, tmp_path):
        self._make_project(tmp_path)
        assert index_project_files(tmp_path, should_stop=lambda: True) == []

    def test_depth_limit_prunes_deep_trees(self, tmp_path):
        deep = tmp_path
        for level in range(MAX_INDEX_DEPTH + 3):
            deep = deep / f"level_{level}"
            deep.mkdir()
        (deep / "buried.py").write_text("x = 1\n", encoding="utf-8")
        assert "buried.py" not in [path.rsplit("/", 1)[-1] for path in index_project_files(tmp_path)]


class TestBuildFileEntries:
    """Entry shaping for the fuzzy picker."""

    def test_title_is_the_file_name(self):
        entries = build_file_entries(["pkg/helper.py"])
        assert entries[0].title == "helper.py"

    def test_path_is_the_relative_path(self):
        entries = build_file_entries(["pkg/helper.py"])
        assert entries[0].path == "pkg/helper.py"

    def test_payload_starts_empty(self):
        assert build_file_entries(["main.py"])[0].payload is None

    def test_empty_input_yields_no_entries(self):
        assert build_file_entries([]) == []
