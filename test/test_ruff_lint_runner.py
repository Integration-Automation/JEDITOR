"""Tests for running ruff over a buffer."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from je_editor.code_scan.ruff_lint import (
    find_ruff_executable,
    is_lintable,
    lint_command,
    lint_text,
)

UNUSED_IMPORT = "import os\n\n\nprint('hello')\n"


class TestIsLintable:
    @pytest.mark.parametrize("name", ["a.py", "a.pyi", "PACKAGE/MODULE.PY"])
    def test_python_files(self, name):
        assert is_lintable(name)

    @pytest.mark.parametrize("name", ["notes.txt", "page.html", "Makefile", "a.pyc"])
    def test_other_files(self, name):
        assert not is_lintable(name)

    def test_no_file(self):
        assert not is_lintable(None)


class TestLintCommand:
    def test_passes_the_buffer_through_stdin(self):
        command = lint_command("ruff", Path("/project/app.py"))
        assert command[-1] == "-"
        assert "--stdin-filename" in command

    def test_asks_for_json(self):
        command = lint_command("ruff", "app.py")
        assert command[command.index("--output-format") + 1] == "json"

    def test_is_an_argument_list_not_a_shell_string(self):
        # A shell string would make the file name injectable.
        assert all(isinstance(part, str) for part in lint_command("ruff", "a b.py"))
        assert lint_command("ruff", "a b.py")[0] == "ruff"


class TestLintText:
    def test_reports_an_unused_import(self):
        if find_ruff_executable() is None:
            pytest.skip("ruff is not installed in this environment")
        diagnostics = lint_text(UNUSED_IMPORT, "sample.py")
        assert any(item.code == "F401" for item in diagnostics)

    def test_clean_code_reports_nothing(self):
        if find_ruff_executable() is None:
            pytest.skip("ruff is not installed in this environment")
        assert lint_text("print('hello')\n", "sample.py") == []

    def test_missing_ruff_yields_no_diagnostics(self):
        with patch("je_editor.code_scan.ruff_lint.find_ruff_executable", return_value=None):
            assert lint_text(UNUSED_IMPORT, "sample.py") == []

    def test_a_failing_ruff_yields_no_diagnostics(self):
        # The editor must keep working when the linter cannot run at all.
        with patch(
            "je_editor.code_scan.ruff_lint.find_ruff_executable", return_value="ruff"
        ), patch(
            "je_editor.code_scan.ruff_lint.subprocess.run", side_effect=OSError("boom")
        ):
            assert lint_text(UNUSED_IMPORT, "sample.py") == []
