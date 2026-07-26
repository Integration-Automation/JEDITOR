"""Tests for what the status bar says about the current tab."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from je_editor.utils.status.status_text import (
    PLAIN_TEXT, cursor_position, encoding_name, language_name, line_ending_display
)


class TestLanguageName:
    @pytest.mark.parametrize("path,expected", [
        ("app.py", "Python"),
        ("stub.pyi", "Python"),
        ("script.pyw", "Python"),
        ("main.rs", "Rust"),
        ("index.ts", "TypeScript"),
        ("data.json", "JSON"),
        ("query.sql", "SQL"),
    ])
    def test_a_known_suffix_names_its_language(self, path, expected):
        assert language_name(path) == expected

    def test_the_suffix_is_matched_case_insensitively(self):
        assert language_name("APP.PY") == "Python"

    def test_an_unknown_suffix_is_plain_text(self):
        assert language_name("notes.qqq") == PLAIN_TEXT

    def test_a_file_without_a_suffix_is_plain_text(self):
        assert language_name("Makefile") == PLAIN_TEXT

    def test_an_unsaved_buffer_is_plain_text(self):
        assert language_name(None) == PLAIN_TEXT

    def test_a_full_path_still_resolves(self):
        assert language_name("/home/user/project/main.go") == "Go"


class TestEncodingName:
    def test_it_is_upper_cased(self):
        assert encoding_name("utf-8") == "UTF-8"

    def test_nothing_falls_back_to_the_default(self):
        assert encoding_name(None) == "UTF-8"

    def test_another_encoding_is_shown_as_given(self):
        assert encoding_name("big5") == "BIG5"


class TestLineEndingDisplay:
    @pytest.mark.parametrize("ending,expected", [
        ("\r\n", "CRLF"), ("\n", "LF"), ("\r", "CR"),
    ])
    def test_each_ending_has_a_name(self, ending, expected):
        assert line_ending_display(ending) == expected

    def test_nothing_falls_back_to_lf(self):
        assert line_ending_display(None) == "LF"


class TestCursorPosition:
    def test_it_reads_as_line_and_column(self):
        assert cursor_position(3, 12) == "Ln 3, Col 12"

    def test_positions_below_one_are_clamped(self):
        assert cursor_position(0, 0) == "Ln 1, Col 1"


@pytest.fixture()
def editor_tab(qapp, qtbot):
    """An EditorWidget with a mocked main window, as the other tab tests use."""
    from PySide6.QtWidgets import QTabWidget
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
    qtbot.addWidget(mock_main.tab_widget)
    yield mock_main, widget
    widget.close()


def _status_window(tab_widget):
    """A bare main window with just the status-bar labels the refresh touches."""
    from PySide6.QtWidgets import QLabel
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    window = EditorMain.__new__(EditorMain)
    window.tab_widget = tab_widget
    window._language_label = QLabel()
    window._line_ending_label = QLabel()
    window._encoding_label = QLabel()
    window._cursor_pos_label = QLabel()
    return window


class TestTheStatusBarReadsTheTab:
    """
    It has to describe the tab in front of the user. The encoding label used to
    read the global setting and the line-ending label re-read the file from disk
    on every tab change, so neither followed a change made from the menu.
    """

    def test_the_language_comes_from_the_file(self, editor_tab):
        _window, widget = editor_tab
        widget.current_file = "app.py"
        window = _status_window(_window.tab_widget)
        window.refresh_status_bar()
        assert window._language_label.text() == "Python"

    def test_an_unsaved_buffer_is_plain_text(self, editor_tab):
        _window, widget = editor_tab
        widget.current_file = None
        window = _status_window(_window.tab_widget)
        window.refresh_status_bar()
        assert window._language_label.text() == PLAIN_TEXT

    def test_the_line_ending_comes_from_the_tab(self, editor_tab):
        _window, widget = editor_tab
        widget.line_ending = "\r\n"
        window = _status_window(_window.tab_widget)
        window.refresh_status_bar()
        assert window._line_ending_label.text() == "CRLF"

    def test_the_encoding_comes_from_the_tab(self, editor_tab):
        _window, widget = editor_tab
        widget.file_encoding = "big5"
        window = _status_window(_window.tab_widget)
        window.refresh_status_bar()
        assert window._encoding_label.text() == "BIG5"

    def test_the_caret_position_is_shown(self, editor_tab):
        _window, widget = editor_tab
        widget.code_edit.setPlainText("one\ntwo\n")
        cursor = widget.code_edit.textCursor()
        cursor.setPosition(5)
        widget.code_edit.setTextCursor(cursor)
        window = _status_window(_window.tab_widget)
        window.refresh_status_bar()
        assert window._cursor_pos_label.text() == "Ln 2, Col 2"

    def test_a_tab_that_is_not_an_editor_shows_defaults(self, qapp, qtbot):
        from PySide6.QtWidgets import QTabWidget, QWidget
        tabs = QTabWidget()
        qtbot.addWidget(tabs)
        tabs.addTab(QWidget(), "Browser")
        window = _status_window(tabs)
        window.refresh_status_bar()
        assert window._language_label.text() == PLAIN_TEXT
        assert window._encoding_label.text() == "UTF-8"
        assert window._cursor_pos_label.text() == "Ln 1, Col 1"


class TestRefreshingFromTheMenu:
    """
    Changing the encoding or line ending has to move the status bar with it.
    The labels used to read the global setting and the bytes on disk, so a menu
    change left them describing the file as it was opened.
    """

    def test_the_line_ending_choice_asks_for_a_refresh(self, editor_tab):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import (
            apply_line_ending_choice
        )
        window, widget = editor_tab
        assert apply_line_ending_choice(window, "\r\n") is True
        assert widget.line_ending == "\r\n"
        window.refresh_status_bar.assert_called()

    def test_the_encoding_choice_asks_for_a_refresh(self, editor_tab):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import (
            apply_encoding
        )
        window, widget = editor_tab
        assert apply_encoding(window, "big5") is True
        assert widget.file_encoding == "big5"
        window.refresh_status_bar.assert_called()

    def test_a_window_without_a_status_bar_is_tolerated(self, editor_tab):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import (
            apply_line_ending_choice
        )
        window, _widget = editor_tab
        window.refresh_status_bar = None
        assert apply_line_ending_choice(window, "\n") is True
