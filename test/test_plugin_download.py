"""Tests that a downloaded plugin can only land inside the plugins directory."""
from __future__ import annotations

import pytest

from je_editor.pyside_ui.main_ui.plugin_browser import github_api
from je_editor.pyside_ui.main_ui.plugin_browser.github_api import (
    _safe_destination, download_plugin_file, fetch_repo_tree
)

# 遠端 repo 自己填的檔名，不是使用者打的
# Names the remote repository fills in, not ones the user typed
ESCAPING_NAMES = (
    "../evil.py",
    "../../evil.py",
    "sub/evil.py",
    "sub\\evil.py",
    "C:/Windows/evil.py",
    "/etc/evil.py",
    "..",
    "",
)


class TestTheDownloadDestination:
    def test_a_plain_name_lands_in_the_directory(self, tmp_path):
        assert _safe_destination(str(tmp_path), "good.py") == (tmp_path / "good.py").resolve()

    @pytest.mark.parametrize("name", ESCAPING_NAMES)
    def test_a_name_that_escapes_is_rejected(self, tmp_path, name):
        with pytest.raises(ValueError):
            _safe_destination(str(tmp_path), name)


class TestDownloadingAPlugin:
    @pytest.fixture(autouse=True)
    def no_network(self, monkeypatch):
        """Answer every download with a fixed body instead of reaching GitHub."""
        monkeypatch.setattr(github_api, "_download_text", lambda url: "PLUGIN_NAME = 'x'\n")

    def test_a_plain_name_is_written(self, tmp_path):
        saved = download_plugin_file("https://example.invalid/x.py", str(tmp_path), "good.py")
        assert (tmp_path / "good.py").read_text(encoding="utf-8") == "PLUGIN_NAME = 'x'\n"
        assert saved == str((tmp_path / "good.py").resolve())

    @pytest.mark.parametrize("name", ESCAPING_NAMES)
    def test_an_escaping_name_writes_nothing(self, tmp_path, name):
        destination = tmp_path / "plugins"
        destination.mkdir()
        with pytest.raises(ValueError):
            download_plugin_file("https://example.invalid/x.py", str(destination), name)
        assert list(tmp_path.rglob("*.py")) == []


class TestTheBranchToRead:
    @pytest.fixture()
    def requested(self, monkeypatch):
        """Record the URL asked for instead of reaching GitHub."""
        seen = []
        monkeypatch.setattr(github_api, "_fetch_contents_recursive",
                            lambda url: seen.append(url) or [])
        return seen

    def test_no_branch_asks_for_the_default(self, requested):
        fetch_repo_tree("owner", "repo")
        assert "?ref=" not in requested[0]

    def test_a_branch_is_asked_for_by_name(self, requested):
        fetch_repo_tree("owner", "repo", "develop")
        assert requested[0].endswith("?ref=develop")

    def test_a_branch_name_is_escaped(self, requested):
        fetch_repo_tree("owner", "repo", "feature/a b")
        assert requested[0].endswith("?ref=feature%2Fa%20b")
