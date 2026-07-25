"""Tests for the lint manager, the editor's underlines, and the problems panel."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QApplication

from je_editor.utils.lint.ruff_diagnostics import Diagnostic

SAMPLE = Diagnostic(
    line=1, column=1, end_line=1, end_column=7, code="F401", message="unused import")
OTHER = Diagnostic(
    line=2, column=1, end_line=2, end_column=4, code="E701", message="multiple statements")


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
    code_editor.close()
    code_editor.deleteLater()


class TestLintManagerState:
    def test_starts_empty(self, editor):
        assert editor.lint_manager.diagnostics() == []

    def test_set_diagnostics_reports_a_change(self, editor):
        assert editor.lint_manager.set_diagnostics([SAMPLE]) is True
        assert editor.lint_manager.set_diagnostics([SAMPLE]) is False

    def test_for_line(self, editor):
        editor.lint_manager.set_diagnostics([SAMPLE, OTHER])
        assert editor.lint_manager.for_line(1) == [SAMPLE]
        assert editor.lint_manager.for_line(3) == []

    def test_message_for_line(self, editor):
        editor.lint_manager.set_diagnostics([SAMPLE])
        assert "unused import" in editor.lint_manager.message_for_line(1)
        assert editor.lint_manager.message_for_line(2) is None

    def test_clear_reports_whether_anything_went(self, editor):
        editor.lint_manager.set_diagnostics([SAMPLE])
        assert editor.lint_manager.clear() is True
        assert editor.lint_manager.clear() is False

    def test_diagnostics_returns_a_copy(self, editor):
        editor.lint_manager.set_diagnostics([SAMPLE])
        editor.lint_manager.diagnostics().clear()
        assert editor.lint_manager.diagnostics() == [SAMPLE]

    def test_a_non_python_file_is_not_checked(self, editor):
        editor.current_file = "notes.txt"
        assert editor.request_lint() is False

    def test_no_file_is_not_checked(self, editor):
        editor.current_file = None
        assert editor.request_lint() is False

    def test_requesting_a_check_clears_stale_diagnostics(self, editor):
        editor.lint_manager.set_diagnostics([SAMPLE])
        editor.current_file = "notes.txt"
        editor.request_lint()
        assert editor.lint_manager.diagnostics() == []


class TestUnderlines:
    def _wave_selections(self, editor):
        wave = QTextCharFormat.UnderlineStyle.WaveUnderline
        return [
            selection for selection in editor.extraSelections()
            if selection.format.underlineStyle() == wave
        ]

    def test_diagnostics_are_underlined(self, editor):
        editor.setPlainText("import os\nx=1\n")
        editor.lint_manager.set_diagnostics([SAMPLE])
        editor.refresh_lint_display()
        assert len(self._wave_selections(editor)) == 1

    def test_underline_covers_the_reported_range(self, editor):
        # The range is checked on the cursor the editor builds, rather than on
        # the one inside an ExtraSelection, whose C++ object dies with the list.
        editor.setPlainText("import os\nx=1\n")
        cursor = editor._diagnostic_cursor(editor.document(), SAMPLE)
        assert cursor.selectedText() == "import"

    def test_range_on_a_missing_line_is_refused(self, editor):
        editor.setPlainText("x = 1\n")
        missing = Diagnostic(
            line=99, column=1, end_line=99, end_column=4, code="E1", message="gone")
        assert editor._diagnostic_cursor(editor.document(), missing) is None

    def test_no_diagnostics_means_no_underline(self, editor):
        editor.setPlainText("x = 1\n")
        editor.lint_manager.set_diagnostics([])
        editor.refresh_lint_display()
        assert self._wave_selections(editor) == []

    def test_a_diagnostic_past_the_end_is_skipped(self, editor):
        editor.setPlainText("x = 1\n")
        editor.lint_manager.set_diagnostics([
            Diagnostic(line=99, column=1, end_line=99, end_column=4, code="E1", message="gone")])
        editor.refresh_lint_display()
        assert self._wave_selections(editor) == []

    def test_zero_width_range_still_marks_a_character(self, editor):
        editor.setPlainText("x = 1\n")
        editor.lint_manager.set_diagnostics([
            Diagnostic(line=1, column=1, end_line=1, end_column=1, code="E2", message="here")])
        editor.refresh_lint_display()
        assert len(self._wave_selections(editor)) == 1

    def test_current_line_highlight_survives_alongside_underlines(self, editor):
        editor.setPlainText("import os\n")
        editor.lint_manager.set_diagnostics([SAMPLE])
        editor.highlight_current_line()
        assert len(editor.extraSelections()) > len(self._wave_selections(editor))

    def test_caret_line_message_becomes_the_tooltip(self, editor):
        editor.setPlainText("import os\nx = 1\n")
        editor.lint_manager.set_diagnostics([SAMPLE])
        editor.refresh_lint_display()
        assert "unused import" in editor.toolTip()


class _FakeTabWidget:
    def __init__(self, widget=None):
        self._widget = widget

    def currentWidget(self):
        return self._widget


class TestProblemsPanel:
    def test_lists_the_current_editor_diagnostics(self, app, editor):
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
            ProblemsPanelWidget
        )
        tab = MagicMock(spec=EditorWidget)
        tab.code_edit = editor
        editor.current_file = None
        editor.lint_manager.set_diagnostics([SAMPLE, OTHER])
        window = MagicMock()
        window.tab_widget = _FakeTabWidget(tab)
        with patch.object(editor, "request_lint", return_value=False):
            panel = ProblemsPanelWidget(window)
        assert panel.result_tree.topLevelItemCount() == 2
        assert panel.result_tree.topLevelItem(0).text(0) == "F401"
        panel.close()
        panel.deleteLater()

    def test_no_editor_tab_shows_nothing(self, app):
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
            ProblemsPanelWidget
        )
        window = MagicMock()
        window.tab_widget = _FakeTabWidget(None)
        panel = ProblemsPanelWidget(window)
        assert panel.diagnostics() == []
        assert panel.result_tree.topLevelItemCount() == 0
        panel.close()
        panel.deleteLater()

    def test_double_click_jumps_to_the_line(self, app, editor):
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
            ProblemsPanelWidget
        )
        editor.setPlainText("import os\nx = 1\ny = 2\n")
        editor.lint_manager.set_diagnostics([OTHER])
        tab = MagicMock(spec=EditorWidget)
        tab.code_edit = editor
        window = MagicMock()
        window.tab_widget = _FakeTabWidget(tab)
        with patch.object(editor, "request_lint", return_value=False):
            panel = ProblemsPanelWidget(window)
        assert panel.jump_to_diagnostic(OTHER) is True
        assert editor.textCursor().blockNumber() == 1
        panel.close()
        panel.deleteLater()
