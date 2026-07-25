"""Tests for the minimap's geometry and its wiring into the editor."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget

from je_editor.utils.minimap.minimap_layout import (
    LINE_PIXELS,
    MINIMAP_WIDTH,
    bar_offset,
    bar_width,
    line_at_row,
    row_for_line,
    sample_step,
    viewport_band,
)


class TestSampleStep:
    def test_short_file_draws_every_line(self):
        assert sample_step(10, 400) == 1

    def test_long_file_samples(self):
        # 1000 lines into 200 pixels: 100 drawable rows, so every 10th line.
        assert sample_step(1000, 200) == 10

    def test_rounding_never_loses_the_tail(self):
        step = sample_step(101, 200)
        assert step >= 1
        assert row_for_line(100, step) <= 200

    def test_empty_document(self):
        assert sample_step(0, 200) == 1

    def test_zero_height(self):
        assert sample_step(100, 0) == 1


class TestRowMapping:
    def test_line_to_row_without_sampling(self):
        assert row_for_line(5, 1) == 5 * LINE_PIXELS

    def test_line_to_row_with_sampling(self):
        assert row_for_line(20, 10) == 2 * LINE_PIXELS

    def test_row_back_to_line(self):
        assert line_at_row(row_for_line(30, 1), 1, 100) == 30

    def test_row_beyond_the_document_is_clamped(self):
        assert line_at_row(10_000, 1, 50) == 49

    def test_negative_row_is_clamped(self):
        assert line_at_row(-20, 1, 50) == 0

    def test_empty_document(self):
        assert line_at_row(40, 1, 0) == 0


class TestBars:
    def test_bar_follows_the_line_length(self):
        assert bar_width("abcd") == 4

    def test_blank_line_has_no_bar(self):
        assert bar_width("") == 0
        assert bar_width("    ") == 0

    def test_trailing_space_does_not_lengthen_the_bar(self):
        assert bar_width("ab   ") == 2

    def test_bar_is_capped_at_the_minimap_width(self):
        assert bar_width("x" * 500) == MINIMAP_WIDTH

    def test_indentation_offsets_the_bar(self):
        assert bar_offset("    code") == 4

    def test_unindented_line_starts_at_the_edge(self):
        assert bar_offset("code") == 0


class TestViewportBand:
    def test_band_starts_at_the_first_visible_line(self):
        top, _height = viewport_band(10, 30, 1)
        assert top == row_for_line(10, 1)

    def test_band_covers_the_visible_lines(self):
        _top, height = viewport_band(0, 30, 1)
        assert height == row_for_line(30, 1)

    def test_band_is_never_invisible(self):
        _top, height = viewport_band(0, 0, 50)
        assert height >= LINE_PIXELS


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def editor_widget(app):
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
    widget.code_edit.setPlainText("\n".join(f"line {index}" for index in range(200)))
    yield widget
    widget.code_edit.lint_manager.stop()
    widget.code_edit.diff_marker_manager.stop()
    widget.code_edit.blame_manager.stop()
    widget.deleteLater()


class TestMinimapWiring:
    def test_starts_hidden(self, editor_widget):
        assert editor_widget.minimap is None

    def test_toggling_on_adds_it(self, editor_widget):
        assert editor_widget.toggle_minimap() is True
        assert editor_widget.minimap is not None

    def test_toggling_off_removes_it(self, editor_widget):
        editor_widget.toggle_minimap()
        assert editor_widget.toggle_minimap() is False
        assert editor_widget.minimap is None

    def test_painting_does_not_raise(self, editor_widget):
        editor_widget.toggle_minimap()
        editor_widget.show()
        QApplication.processEvents()
        editor_widget.hide()

    def test_clicking_maps_to_a_line_in_range(self, editor_widget):
        editor_widget.toggle_minimap()
        minimap = editor_widget.minimap
        line = minimap.line_at_position(20)
        assert 0 <= line < editor_widget.code_edit.blockCount()

    def test_markers_report_diagnostics(self, editor_widget):
        from je_editor.utils.lint.ruff_diagnostics import Diagnostic
        editor_widget.toggle_minimap()
        editor_widget.code_edit.lint_manager.set_diagnostics([
            Diagnostic(line=4, column=1, end_line=4, end_column=3, code="F401", message="x")])
        assert editor_widget.minimap.marker_lines()["diagnostic"] == [3]

    def test_markers_report_git_changes(self, editor_widget):
        editor_widget.toggle_minimap()
        editor_widget.code_edit.setPlainText("a\nCHANGED\nc\n")
        editor_widget.code_edit.diff_marker_manager.set_baseline("a\nb\nc\n")
        assert editor_widget.minimap.marker_lines()["change"] == [1]

    def test_markers_report_occurrences_of_the_word_under_the_caret(self, editor_widget):
        editor_widget.toggle_minimap()
        editor_widget.code_edit.setPlainText("total = 1\nx = total\ny = total\n")
        cursor = editor_widget.code_edit.textCursor()
        cursor.setPosition(2)
        editor_widget.code_edit.setTextCursor(cursor)
        assert editor_widget.minimap.marker_lines()["occurrence"] == [0, 1, 2]

    def test_no_markers_when_there_is_nothing_to_mark(self, editor_widget):
        editor_widget.toggle_minimap()
        editor_widget.code_edit.setPlainText("alpha\nbeta\n")
        markers = editor_widget.minimap.marker_lines()
        assert markers["diagnostic"] == [] and markers["change"] == []

    def test_painting_with_markers_does_not_raise(self, editor_widget):
        from je_editor.utils.lint.ruff_diagnostics import Diagnostic
        editor_widget.toggle_minimap()
        editor_widget.code_edit.setPlainText("a\nCHANGED\nc\n")
        editor_widget.code_edit.diff_marker_manager.set_baseline("a\nb\nc\n")
        editor_widget.code_edit.lint_manager.set_diagnostics([
            Diagnostic(line=1, column=1, end_line=1, end_column=2, code="E1", message="x")])
        editor_widget.show()
        QApplication.processEvents()
        editor_widget.hide()

    def test_an_empty_document_is_safe_to_map(self, editor_widget):
        editor_widget.code_edit.setPlainText("")
        editor_widget.toggle_minimap()
        assert editor_widget.minimap.line_at_position(50) == 0
