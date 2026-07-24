"""Tests for identifier naming-style conversion."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.case_convert.case_convert import (
    split_words,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


class TestSplitWords:
    def test_snake(self):
        assert split_words("my_var_name") == ["my", "var", "name"]

    def test_kebab(self):
        assert split_words("my-var-name") == ["my", "var", "name"]

    def test_camel(self):
        assert split_words("myVarName") == ["my", "Var", "Name"]

    def test_pascal(self):
        assert split_words("MyVarName") == ["My", "Var", "Name"]

    def test_acronym_preserved(self):
        assert split_words("parseHTTPResponse") == ["parse", "HTTP", "Response"]

    def test_digits(self):
        assert split_words("value2Name") == ["value2", "Name"]

    def test_mixed_separators(self):
        assert split_words("mix_of-styles here") == ["mix", "of", "styles", "here"]

    def test_empty(self):
        assert split_words("") == []


class TestToSnakeCase:
    def test_from_camel(self):
        assert to_snake_case("myVarName") == "my_var_name"

    def test_from_pascal(self):
        assert to_snake_case("MyVarName") == "my_var_name"

    def test_from_kebab(self):
        assert to_snake_case("my-var-name") == "my_var_name"

    def test_acronym(self):
        assert to_snake_case("parseHTTPResponse") == "parse_http_response"


class TestToCamelCase:
    def test_from_snake(self):
        assert to_camel_case("my_var_name") == "myVarName"

    def test_from_pascal(self):
        assert to_camel_case("MyVarName") == "myVarName"

    def test_empty(self):
        assert to_camel_case("") == ""


class TestToPascalCase:
    def test_from_snake(self):
        assert to_pascal_case("my_var_name") == "MyVarName"

    def test_from_kebab(self):
        assert to_pascal_case("my-var-name") == "MyVarName"


class TestToKebabCase:
    def test_from_camel(self):
        assert to_kebab_case("myVarName") == "my-var-name"


class TestRoundTrips:
    def test_snake_to_camel_to_snake(self):
        assert to_snake_case(to_camel_case("my_var_name")) == "my_var_name"

    def test_camel_to_pascal_to_camel(self):
        assert to_camel_case(to_pascal_case("myVarName")) == "myVarName"


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


class TestEditorCaseConvert:
    def test_snake_case_selection(self, editor):
        editor.setPlainText("myVarName")
        _select(editor, 0, 9)
        editor.to_snake_case_selection()
        assert editor.toPlainText() == "my_var_name"

    def test_camel_case_selection(self, editor):
        editor.setPlainText("my_var_name")
        _select(editor, 0, 11)
        editor.to_camel_case_selection()
        assert editor.toPlainText() == "myVarName"

    def test_pascal_case_selection(self, editor):
        editor.setPlainText("my_var")
        _select(editor, 0, 6)
        editor.to_pascal_case_selection()
        assert editor.toPlainText() == "MyVar"

    def test_kebab_case_selection(self, editor):
        editor.setPlainText("myVar")
        _select(editor, 0, 5)
        editor.to_kebab_case_selection()
        assert editor.toPlainText() == "my-var"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("myVarName")
        _select(editor, 0, 9)
        editor.to_snake_case_selection()
        editor.undo()
        assert editor.toPlainText() == "myVarName"
