"""Tests for encode/decode transforms and their editor commands."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.encode_decode.encode_decode import (
    base64_decode,
    base64_encode,
    html_escape,
    html_unescape,
    json_string_escape,
    json_string_unescape,
    url_decode,
    url_encode,
)


class TestBase64:
    def test_encode(self):
        assert base64_encode("hello") == "aGVsbG8="

    def test_decode(self):
        assert base64_decode("aGVsbG8=") == "hello"

    def test_round_trip_unicode(self):
        assert base64_decode(base64_encode("哈囉 🌏")) == "哈囉 🌏"

    def test_decode_invalid_returns_none(self):
        assert base64_decode("not valid base64!!!") is None

    def test_decode_non_utf8_returns_none(self):
        # 0xff is valid base64 for a byte that is not valid UTF-8.
        assert base64_decode("/w==") is None

    def test_decode_ignores_surrounding_whitespace(self):
        assert base64_decode("  aGVsbG8=  ") == "hello"


class TestUrl:
    def test_encode(self):
        assert url_encode("a b/c?d=e") == "a%20b%2Fc%3Fd%3De"

    def test_decode(self):
        assert url_decode("a%20b%2Fc") == "a b/c"

    def test_round_trip(self):
        original = "path/to file?x=1&y=2"
        assert url_decode(url_encode(original)) == original

    def test_encode_unicode(self):
        assert url_decode(url_encode("café")) == "café"


class TestHtml:
    def test_escape(self):
        assert html_escape("<a href='x'>&") == "&lt;a href=&#x27;x&#x27;&gt;&amp;"

    def test_unescape(self):
        assert html_unescape("&lt;a&gt;&amp;") == "<a>&"

    def test_round_trip(self):
        original = "<div class=\"x\"> & </div>"
        assert html_unescape(html_escape(original)) == original


class TestJsonString:
    def test_escape_wraps_in_quotes(self):
        assert json_string_escape("a\nb") == '"a\\nb"'

    def test_unescape(self):
        assert json_string_unescape('"a\\nb"') == "a\nb"

    def test_round_trip(self):
        original = 'tab\there "quote" \\ backslash'
        assert json_string_unescape(json_string_escape(original)) == original

    def test_unescape_invalid_returns_none(self):
        assert json_string_unescape("not a json string") is None

    def test_unescape_non_string_json_returns_none(self):
        # Valid JSON, but a number, not a string.
        assert json_string_unescape("123") is None


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def editor(app):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.close()
    code_editor.deleteLater()


def _select(editor, start: int, end: int) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestEditorEncodeDecode:
    def test_base64_encode_selection(self, editor):
        editor.setPlainText("hello")
        _select(editor, 0, 5)
        editor.base64_encode_selection()
        assert editor.toPlainText() == "aGVsbG8="

    def test_base64_decode_selection(self, editor):
        editor.setPlainText("aGVsbG8=")
        _select(editor, 0, 8)
        editor.base64_decode_selection()
        assert editor.toPlainText() == "hello"

    def test_base64_decode_failure_is_noop(self, editor):
        editor.setPlainText("!!!bad!!!")
        _select(editor, 0, 9)
        editor.base64_decode_selection()
        assert editor.toPlainText() == "!!!bad!!!"

    def test_url_encode_selection(self, editor):
        editor.setPlainText("a b")
        _select(editor, 0, 3)
        editor.url_encode_selection()
        assert editor.toPlainText() == "a%20b"

    def test_encode_is_single_undo_step(self, editor):
        editor.setPlainText("hello")
        _select(editor, 0, 5)
        editor.base64_encode_selection()
        editor.undo()
        assert editor.toPlainText() == "hello"

    def test_no_selection_is_noop(self, editor):
        editor.setPlainText("hello")
        cursor = editor.textCursor()
        cursor.setPosition(2)
        editor.setTextCursor(cursor)
        editor.base64_encode_selection()
        assert editor.toPlainText() == "hello"

    def test_html_escape_selection(self, editor):
        editor.setPlainText("<b>")
        _select(editor, 0, 3)
        editor.html_escape_selection()
        assert editor.toPlainText() == "&lt;b&gt;"

    def test_json_escape_selection(self, editor):
        editor.setPlainText("a\tb")
        _select(editor, 0, 3)
        editor.json_escape_selection()
        assert editor.toPlainText() == '"a\\tb"'

    def test_json_unescape_failure_is_noop(self, editor):
        editor.setPlainText("plain text")
        _select(editor, 0, 10)
        editor.json_unescape_selection()
        assert editor.toPlainText() == "plain text"

    def test_swapcase_selection(self, editor):
        editor.setPlainText("Hello World")
        _select(editor, 0, 11)
        editor.swapcase_selection()
        assert editor.toPlainText() == "hELLO wORLD"

    def test_titlecase_selection(self, editor):
        editor.setPlainText("hello world")
        _select(editor, 0, 11)
        editor.titlecase_selection()
        assert editor.toPlainText() == "Hello World"
