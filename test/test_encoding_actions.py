"""Tests for applying an encoding or line-ending choice to the current tab."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import (
    apply_encoding,
    apply_line_ending_choice,
    current_editor_tab,
)
from je_editor.utils.encodings.text_codec import LINE_ENDING_CRLF, LINE_ENDING_LF


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class _FakeTabWidget:
    def __init__(self, widget=None):
        self._widget = widget

    def currentWidget(self):
        return self._widget


@pytest.fixture()
def editor_tab(app):
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from PySide6.QtWidgets import QPlainTextEdit
    tab = MagicMock(spec=EditorWidget)
    tab.code_edit = QPlainTextEdit()
    tab.current_file = None
    tab.file_encoding = "utf-8"
    tab.line_ending = LINE_ENDING_LF
    tab.code_save_thread = None
    tab._is_modified = False
    yield tab
    tab.code_edit.deleteLater()


def _window(tab):
    window = MagicMock()
    window.tab_widget = _FakeTabWidget(tab)
    return window


class TestCurrentEditorTab:
    def test_finds_an_editor_tab(self, editor_tab):
        assert current_editor_tab(_window(editor_tab)) is editor_tab

    def test_other_tab_types_are_ignored(self, app):
        assert current_editor_tab(_window(object())) is None

    def test_window_without_tabs(self, app):
        window = MagicMock()
        window.tab_widget = None
        assert current_editor_tab(window) is None


class TestApplyEncoding:
    def test_sets_the_tab_encoding(self, editor_tab):
        assert apply_encoding(_window(editor_tab), "big5") is True
        assert editor_tab.file_encoding == "big5"

    def test_without_an_editor_tab(self, app):
        assert apply_encoding(_window(object()), "big5") is False

    def test_rereads_an_unmodified_file(self, editor_tab, tmp_path):
        path = tmp_path / "big5.txt"
        path.write_bytes("中文\n".encode("big5"))
        editor_tab.current_file = str(path)
        editor_tab._is_modified = False
        apply_encoding(_window(editor_tab), "big5")
        assert editor_tab.code_edit.toPlainText() == "中文\n"
        assert editor_tab.file_encoding == "big5"

    def test_unsaved_changes_are_never_discarded(self, editor_tab, tmp_path):
        path = tmp_path / "sample.txt"
        path.write_text("on disk\n", encoding="utf-8")
        editor_tab.current_file = str(path)
        editor_tab.code_edit.setPlainText("unsaved work")
        editor_tab._is_modified = True
        apply_encoding(_window(editor_tab), "utf-8")
        assert editor_tab.code_edit.toPlainText() == "unsaved work"
        assert editor_tab.file_encoding == "utf-8"

    def test_an_encoding_that_cannot_decode_leaves_the_text_alone(self, editor_tab, tmp_path):
        path = tmp_path / "big5.txt"
        path.write_bytes("中文\n".encode("big5"))
        editor_tab.current_file = str(path)
        editor_tab.code_edit.setPlainText("previous text")
        apply_encoding(_window(editor_tab), "ascii")
        assert editor_tab.code_edit.toPlainText() == "previous text"

    def test_auto_save_follows_the_encoding(self, editor_tab):
        thread = MagicMock()
        editor_tab.code_save_thread = thread
        apply_encoding(_window(editor_tab), "big5")
        assert thread.encoding == "big5"


class TestApplyLineEnding:
    def test_sets_the_tab_line_ending(self, editor_tab):
        assert apply_line_ending_choice(_window(editor_tab), LINE_ENDING_CRLF) is True
        assert editor_tab.line_ending == LINE_ENDING_CRLF

    def test_without_an_editor_tab(self, app):
        assert apply_line_ending_choice(_window(object()), LINE_ENDING_CRLF) is False

    def test_auto_save_follows_the_line_ending(self, editor_tab):
        thread = MagicMock()
        editor_tab.code_save_thread = thread
        apply_line_ending_choice(_window(editor_tab), LINE_ENDING_CRLF)
        assert thread.line_ending == LINE_ENDING_CRLF

    def test_the_text_itself_is_untouched(self, editor_tab):
        editor_tab.code_edit.setPlainText("a\nb\n")
        apply_line_ending_choice(_window(editor_tab), LINE_ENDING_CRLF)
        assert editor_tab.code_edit.toPlainText() == "a\nb\n"
