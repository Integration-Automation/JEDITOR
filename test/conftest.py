"""
Shared pytest fixtures for JEditor tests.
Provides a QApplication instance (via pytest-qt) and common helpers.
"""
from __future__ import annotations

import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

# Exclude old integration test scripts from pytest collection
# Use multiple glob patterns to work across platforms (forward/back slashes)
collect_ignore_glob = [
    "**/start_qt_ui.py",
    "**/extend_test.py",
]


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication for the whole test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(autouse=True)
def _no_toolbar_threads_left_running():
    """
    Wait for the toolbar's git scans before letting a test end.

    Building a toolbar starts one, and the real window waits for them in its
    close handler. A test that builds one and walks away leaves a thread running
    into the next test, where Qt destroys it mid-flight and aborts the process.
    Doing it here covers every test rather than each fixture remembering to.
    """
    yield
    from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
        stop_background_threads
    )
    stop_background_threads()


@pytest.fixture()
def tmp_dir(tmp_path):
    """Provide a temporary directory and chdir into it, restoring after."""
    original = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original)


@pytest.fixture()
def tmp_file(tmp_path):
    """Create a temporary Python file with sample content."""
    f = tmp_path / "test_sample.py"
    f.write_text("print('hello')\n", encoding="utf-8")
    return f
