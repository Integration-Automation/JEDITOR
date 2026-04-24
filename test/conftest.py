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
