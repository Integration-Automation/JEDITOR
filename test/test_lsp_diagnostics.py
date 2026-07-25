"""Tests for showing language-server diagnostics through the lint display."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.lint.ruff_diagnostics import (
    SYNTAX_ERROR_CODE,
    diagnostic_from_entry,
    diagnostics_from_entries,
)
from je_editor.utils.lsp.lsp_protocol import diagnostic_entries

SERVER_NOTIFICATION = {
    "diagnostics": [
        {
            "range": {"start": {"line": 3, "character": 4}, "end": {"line": 3, "character": 9}},
            "message": "Cannot find name 'foo'",
            "code": 2304,
        }
    ]
}


class TestServerDiagnosticShape:
    def test_range_becomes_one_based(self):
        entry = diagnostic_entries(SERVER_NOTIFICATION)[0]
        assert entry["line"] == 4 and entry["column"] == 5
        assert entry["end_line"] == 4 and entry["end_column"] == 10

    def test_numeric_code_is_kept_as_text(self):
        assert diagnostic_entries(SERVER_NOTIFICATION)[0]["code"] == "2304"

    def test_entry_without_a_range_still_works(self):
        entry = diagnostic_entries({"diagnostics": [{"message": "broken"}]})[0]
        assert entry["line"] == 1 and entry["column"] == 1

    def test_entry_without_a_message_is_dropped(self):
        assert diagnostic_entries({"diagnostics": [{"range": {}}]}) == []


class TestConversionToTheEditorShape:
    def test_server_entry_becomes_a_diagnostic(self):
        diagnostic = diagnostic_from_entry(diagnostic_entries(SERVER_NOTIFICATION)[0])
        assert diagnostic.line == 4
        assert diagnostic.code == "2304"
        assert "Cannot find name" in diagnostic.message

    def test_batch_conversion(self):
        assert len(diagnostics_from_entries(diagnostic_entries(SERVER_NOTIFICATION))) == 1

    def test_entry_without_a_code_falls_back(self):
        diagnostic = diagnostic_from_entry({"line": 2, "message": "no code here"})
        assert diagnostic.code == SYNTAX_ERROR_CODE

    def test_missing_columns_default_to_the_line_start(self):
        diagnostic = diagnostic_from_entry({"line": 5, "message": "somewhere"})
        assert diagnostic.column == 1 and diagnostic.end_line == 5

    def test_unusable_entries_are_dropped(self):
        assert diagnostic_from_entry({"message": "no line"}) is None
        assert diagnostic_from_entry({"line": 0, "message": "bad line"}) is None
        assert diagnostic_from_entry("nonsense") is None

    def test_non_list_batch(self):
        assert diagnostics_from_entries("nonsense") == []


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
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.blame_manager.stop()
    code_editor.lsp_client.stop()
    code_editor.close()
    code_editor.deleteLater()


class TestEditorShowsServerDiagnostics:
    def test_diagnostics_reach_the_lint_manager(self, editor):
        editor.setPlainText("const value = foo;\n")
        assert editor.apply_server_diagnostics(diagnostic_entries({
            "diagnostics": [{
                "range": {"start": {"line": 0, "character": 6},
                          "end": {"line": 0, "character": 11}},
                "message": "unused", "code": 6133,
            }]
        })) is True
        assert editor.lint_manager.diagnostics()[0].message == "unused"

    def test_the_same_diagnostics_twice_change_nothing(self, editor):
        entries = diagnostic_entries(SERVER_NOTIFICATION)
        editor.setPlainText("\n".join("line" for _ in range(10)))
        editor.apply_server_diagnostics(entries)
        assert editor.apply_server_diagnostics(entries) is False

    def test_underlines_are_drawn_for_server_diagnostics(self, editor):
        from PySide6.QtGui import QTextCharFormat
        editor.setPlainText("const value = foo;\n")
        editor.apply_server_diagnostics(diagnostic_entries({
            "diagnostics": [{
                "range": {"start": {"line": 0, "character": 1},
                          "end": {"line": 0, "character": 5}},
                "message": "here",
            }]
        }))
        wave = QTextCharFormat.UnderlineStyle.WaveUnderline
        assert any(
            selection.format.underlineStyle() == wave
            for selection in editor.extraSelections())

    def test_a_lint_pass_does_not_wipe_server_diagnostics(self, editor):
        # The ruff pass skips non-Python files; without a guard it would clear
        # whatever the language server had just reported.
        editor.current_file = "app.ts"
        editor.setPlainText("const value = foo;\n")
        editor.apply_server_diagnostics(diagnostic_entries(SERVER_NOTIFICATION))
        with patch.object(type(editor.lsp_client), "running", property(lambda _self: True)):
            editor.request_lint()
        assert editor.lint_manager.diagnostics() != []

    def test_without_a_server_a_lint_pass_still_clears(self, editor):
        editor.current_file = "notes.txt"
        editor.apply_server_diagnostics(diagnostic_entries(SERVER_NOTIFICATION))
        editor.request_lint()
        assert editor.lint_manager.diagnostics() == []
