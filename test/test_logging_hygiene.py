"""Tests for what the editor writes to logs, and what it leaves alone."""
from __future__ import annotations

import logging
import subprocess
import sys
import textwrap

import pytest

from je_editor.utils.file.save.save_file import write_file

DISTINCTIVE_LINE = "an unusually distinctive line the log must never carry"


class TestSavingDoesNotLogTheFile:
    """
    A save records the path, not the file.

    Logging the content copies every file the user edits into JEditor.log, and
    the f-string builds that copy on every save whatever the log level is.
    """

    @pytest.fixture()
    def written(self, tmp_path, caplog):
        target = tmp_path / "saved.txt"
        with caplog.at_level(logging.INFO, logger="JEditor"):
            write_file(str(target), f"{DISTINCTIVE_LINE}\n")
        return caplog.text

    def test_the_save_is_recorded(self, written):
        assert "write_file" in written

    def test_the_path_is_recorded(self, written):
        assert "saved.txt" in written

    def test_the_content_is_not_recorded(self, written):
        assert DISTINCTIVE_LINE not in written

    def test_the_file_is_still_written(self, tmp_path):
        target = tmp_path / "saved.txt"
        write_file(str(target), f"{DISTINCTIVE_LINE}\n")
        assert target.read_text(encoding="utf-8") == f"{DISTINCTIVE_LINE}\n"


class TestImportingDoesNotReconfigureLogging:
    """
    Importing a module must not touch the root logger.

    JEditor is embedded in other applications, and ``logging.basicConfig`` at
    import time changes logging for the whole host process, not just this one.
    A subprocess is used because under pytest the root logger already has
    handlers, which makes ``basicConfig`` a silent no-op.
    """

    PROBE = textwrap.dedent(
        """
        import logging
        before = (logging.root.level, len(logging.root.handlers))
        import je_editor.pyside_ui.git_ui.git_client.git_branch_tree_widget  # noqa: F401
        after = (logging.root.level, len(logging.root.handlers))
        print(before, after)
        """
    )

    @pytest.fixture(scope="class")
    def probe_result(self):
        # This interpreter running a literal defined above; no shell, no input
        # from anywhere outside this file.
        finished = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
            [sys.executable, "-c", self.PROBE],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=180,
        )
        if finished.returncode != 0:
            pytest.skip(f"probe could not import the module: {finished.stderr[-400:]}")
        before, after = finished.stdout.strip().rsplit(") (", 1)
        return f"{before})", f"({after}"

    def test_the_root_level_is_left_alone(self, probe_result):
        before, after = probe_result
        assert before.split(",")[0] == after.split(",")[0]

    def test_no_root_handler_is_added(self, probe_result):
        before, after = probe_result
        assert before.split(",")[1] == after.split(",")[1]
