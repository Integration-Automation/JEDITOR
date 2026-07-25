"""Tests for the same-file split view."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from je_editor.pyside_ui.code.split_view.split_editor_view import SplitEditorView


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def source(app):
    editor = QPlainTextEdit()
    editor.setPlainText("first\nsecond\nthird\n")
    yield editor
    editor.deleteLater()


class TestSplitEditorView:
    def test_shows_the_same_content(self, source):
        view = SplitEditorView(source)
        assert view.toPlainText() == source.toPlainText()
        view.close()
        view.deleteLater()

    def test_shares_one_document(self, source):
        view = SplitEditorView(source)
        assert view.document() is source.document()
        view.close()
        view.deleteLater()

    def test_an_edit_in_the_split_reaches_the_main_editor(self, source):
        view = SplitEditorView(source)
        view.setPlainText("rewritten\n")
        assert source.toPlainText() == "rewritten\n"
        view.close()
        view.deleteLater()

    def test_an_edit_in_the_main_editor_reaches_the_split(self, source):
        view = SplitEditorView(source)
        source.setPlainText("from the main editor\n")
        assert view.toPlainText() == "from the main editor\n"
        view.close()
        view.deleteLater()

    def test_carets_are_independent(self, source):
        view = SplitEditorView(source)
        cursor = view.textCursor()
        cursor.setPosition(view.document().findBlockByNumber(2).position())
        view.setTextCursor(cursor)
        assert view.textCursor().blockNumber() == 2
        assert source.textCursor().blockNumber() == 0
        view.close()
        view.deleteLater()

    def test_closing_releases_the_shared_document(self, source):
        view = SplitEditorView(source)
        view.close()
        # The main editor keeps its document and stays usable.
        source.setPlainText("still fine\n")
        assert source.toPlainText() == "still fine\n"
        view.deleteLater()


@pytest.fixture()
def editor_widget(app):
    from PySide6.QtWidgets import QTabWidget
    main_window = MagicMock()
    main_window.working_dir = None
    main_window.tab_widget = QTabWidget()
    main_window.python_compiler = None
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        widget = EditorWidget(main_window)
    yield widget
    widget.code_edit.lint_manager.stop()
    widget.code_edit.diff_marker_manager.stop()
    widget.code_edit.blame_manager.stop()
    widget.deleteLater()


class TestToggleSplitView:
    def test_starts_without_a_split(self, editor_widget):
        assert editor_widget.split_view is None

    def test_toggling_on_adds_the_view(self, editor_widget):
        assert editor_widget.toggle_split_view() is True
        assert editor_widget.split_view is not None
        assert editor_widget.split_view.document() is editor_widget.code_edit.document()

    def test_toggling_off_removes_it(self, editor_widget):
        editor_widget.toggle_split_view()
        assert editor_widget.toggle_split_view() is False
        assert editor_widget.split_view is None

    def test_the_main_editor_survives_closing_the_split(self, editor_widget):
        editor_widget.code_edit.setPlainText("content\n")
        editor_widget.toggle_split_view()
        editor_widget.toggle_split_view()
        editor_widget.code_edit.setPlainText("still editable\n")
        assert editor_widget.code_edit.toPlainText() == "still editable\n"

    def test_split_shows_edits_made_after_opening(self, editor_widget):
        editor_widget.toggle_split_view()
        editor_widget.code_edit.setPlainText("typed later\n")
        assert editor_widget.split_view.toPlainText() == "typed later\n"
