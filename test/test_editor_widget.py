"""Tests for EditorWidget (requires QApplication)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget


@pytest.fixture(scope="module")
def app():
    """Ensure QApplication exists."""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@pytest.fixture()
def editor_widget(app):
    """Create an EditorWidget with a minimal mocked main window."""
    mock_main = MagicMock()
    mock_main.working_dir = None
    mock_main.tab_widget = QTabWidget()
    mock_main.python_compiler = None

    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        widget = EditorWidget(mock_main)
        mock_main.tab_widget.addTab(widget, "Test")

    yield widget
    widget.close()
    widget.deleteLater()
    mock_main.tab_widget.deleteLater()


class TestEditorWidgetModifiedTracking:
    def test_initial_not_modified(self, editor_widget):
        assert editor_widget._is_modified is False

    def test_text_change_sets_modified(self, editor_widget):
        editor_widget.code_edit.setPlainText("test")
        assert editor_widget._is_modified is True

    def test_mark_saved_clears_modified(self, editor_widget):
        editor_widget.code_edit.setPlainText("test2")
        assert editor_widget._is_modified is True
        editor_widget.mark_saved()
        assert editor_widget._is_modified is False

    def test_tab_title_asterisk(self, editor_widget):
        editor_widget._is_modified = False
        idx = editor_widget.tab_manager.indexOf(editor_widget)
        editor_widget.tab_manager.setTabText(idx, "Test")
        editor_widget.code_edit.setPlainText("trigger change")
        title = editor_widget.tab_manager.tabText(idx)
        assert title.endswith(" *")

    def test_mark_saved_removes_asterisk(self, editor_widget):
        editor_widget.code_edit.setPlainText("trigger again")
        editor_widget.mark_saved()
        idx = editor_widget.tab_manager.indexOf(editor_widget)
        title = editor_widget.tab_manager.tabText(idx)
        assert not title.endswith(" *")


class TestEditorWidgetOpenFile:
    def test_open_existing_file(self, editor_widget, tmp_path):
        f = tmp_path / "test_open.py"
        f.write_text("x = 1\n", encoding="utf-8")
        result = editor_widget.open_an_file(f)
        assert result is True
        assert "x = 1" in editor_widget.code_edit.toPlainText()

    def test_open_same_file_twice_switches_tab(self, editor_widget, tmp_path):
        f = tmp_path / "test_dup.py"
        f.write_text("y = 2\n", encoding="utf-8")
        editor_widget.open_an_file(f)
        result = editor_widget.open_an_file(f)
        assert result is False  # should switch instead of re-open


class TestFileWatcher:
    def test_watcher_added_on_open(self, editor_widget, tmp_path):
        f = tmp_path / "watched.py"
        f.write_text("z = 3\n", encoding="utf-8")
        editor_widget.open_an_file(f)
        assert str(f) in editor_widget._file_watcher.files()
