"""Tests for the editor's right-click menu and go-to-definition."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.lsp.lsp_protocol import definition_location, path_from_uri


class TestDefinitionParsing:
    def test_single_location(self):
        location = definition_location({
            "uri": "file:///project/app.ts",
            "range": {"start": {"line": 9, "character": 4}},
        })
        assert location == {"path": "/project/app.ts", "line": 10, "column": 5}

    def test_list_of_locations_takes_the_first(self):
        location = definition_location([
            {"uri": "file:///a.ts", "range": {"start": {"line": 0, "character": 0}}},
            {"uri": "file:///b.ts", "range": {"start": {"line": 5, "character": 0}}},
        ])
        assert location["path"] == "/a.ts"

    def test_location_link_form(self):
        location = definition_location([{
            "targetUri": "file:///project/app.rs",
            "targetSelectionRange": {"start": {"line": 2, "character": 1}},
        }])
        assert location["path"] == "/project/app.rs" and location["line"] == 3

    def test_windows_uri_drops_the_leading_slash(self):
        assert path_from_uri("file:///D:/project/app.ts") == "D:/project/app.ts"

    def test_percent_encoding_is_decoded(self):
        assert path_from_uri("file:///project/my%20app.ts") == "/project/my app.ts"

    def test_unusable_results(self):
        assert definition_location(None) is None
        assert definition_location([]) is None
        assert definition_location({"uri": "file:///a.ts"}) is None
        assert definition_location({"range": {"start": {"line": 1}}}) is None

    def test_non_file_uri(self):
        assert path_from_uri("http://example.com/a.ts") == ""


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


def _labels(menu) -> list[str]:
    return [action.text() for action in menu.actions()]


class TestContextMenu:
    def test_menu_keeps_the_standard_editing_actions(self, editor):
        editor.setPlainText("some text")
        menu = editor.build_context_menu()
        assert any("Paste" in label or "貼上" in label for label in _labels(menu))
        menu.deleteLater()

    def test_menu_adds_the_editor_actions(self, editor):
        menu = editor.build_context_menu()
        labels = " ".join(_labels(menu))
        assert "Comment" in labels
        assert "Bookmark" in labels
        assert "Definition" in labels
        menu.deleteLater()

    def test_revert_is_disabled_without_a_baseline(self, editor):
        menu = editor.build_context_menu()
        revert = [a for a in menu.actions() if "Revert" in a.text()][0]
        assert revert.isEnabled() is False
        menu.deleteLater()

    def test_revert_is_enabled_with_a_baseline(self, editor):
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        menu = editor.build_context_menu()
        revert = [a for a in menu.actions() if "Revert" in a.text()][0]
        assert revert.isEnabled() is True
        menu.deleteLater()

    def test_definition_is_disabled_without_a_server(self, editor):
        menu = editor.build_context_menu()
        definition = [a for a in menu.actions() if "Definition" in a.text()][0]
        assert definition.isEnabled() is False
        menu.deleteLater()

    def test_toggle_comment_from_the_menu_edits_the_line(self, editor):
        editor.setPlainText("value = 1\n")
        menu = editor.build_context_menu()
        comment = [a for a in menu.actions() if "Comment" in a.text()][0]
        comment.trigger()
        assert editor.toPlainText().lstrip().startswith("#")
        menu.deleteLater()

    def test_go_to_definition_without_a_server_is_refused(self, editor):
        assert editor.go_to_definition() is False
