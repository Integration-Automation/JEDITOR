"""Tests for the git change-marker manager and its editor wiring."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.file_diff.line_status import (
    LINE_ADDED, LINE_MODIFIED, LINE_REMOVED_ABOVE
)


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
    code_editor.diff_marker_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


class TestDiffMarkerManager:
    def test_no_baseline_means_no_markers(self, editor):
        editor.setPlainText("a\nb\n")
        assert editor.diff_marker_manager.statuses() == {}
        assert not editor.diff_marker_manager.has_baseline

    def test_baseline_marks_the_changed_line(self, editor):
        editor.setPlainText("a\nB\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        assert editor.diff_marker_manager.status(1) == LINE_MODIFIED
        assert editor.diff_marker_manager.status(0) is None

    def test_added_line_after_the_baseline_is_marked(self, editor):
        editor.setPlainText("a\nb\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        assert editor.diff_marker_manager.status(2) == LINE_ADDED

    def test_deletion_marks_the_following_line(self, editor):
        editor.setPlainText("a\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        assert editor.diff_marker_manager.status(1) == LINE_REMOVED_ABOVE

    def test_refresh_tracks_later_edits(self, editor):
        editor.setPlainText("a\nb\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        assert editor.diff_marker_manager.statuses() == {}
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.refresh()
        assert editor.diff_marker_manager.status(1) == LINE_MODIFIED

    def test_refresh_reports_whether_anything_changed(self, editor):
        editor.setPlainText("a\n")
        editor.diff_marker_manager.set_baseline("a\n")
        assert editor.diff_marker_manager.refresh() is False
        editor.setPlainText("b\n")
        assert editor.diff_marker_manager.refresh() is True
        assert editor.diff_marker_manager.refresh() is False

    def test_clear_forgets_the_baseline(self, editor):
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        editor.diff_marker_manager.clear()
        assert not editor.diff_marker_manager.has_baseline
        assert editor.diff_marker_manager.statuses() == {}

    def test_setting_a_none_baseline_drops_the_markers(self, editor):
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        editor.diff_marker_manager.set_baseline(None)
        assert editor.diff_marker_manager.statuses() == {}

    def test_statuses_returns_a_copy(self, editor):
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        editor.diff_marker_manager.statuses()[1] = "tampered"
        assert editor.diff_marker_manager.status(1) == LINE_MODIFIED


class TestChangeNavigationWiring:
    def _place_cursor(self, editor, line: int) -> None:
        block = editor.document().findBlockByNumber(line)
        cursor = editor.textCursor()
        cursor.setPosition(block.position())
        editor.setTextCursor(cursor)

    def test_next_change_moves_the_caret(self, editor):
        editor.setPlainText("a\nB\nc\nD\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\nd\n")
        self._place_cursor(editor, 0)
        assert editor.next_change() is True
        assert editor.textCursor().blockNumber() == 1

    def test_previous_change_moves_the_caret(self, editor):
        editor.setPlainText("a\nB\nc\nD\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\nd\n")
        self._place_cursor(editor, 3)
        assert editor.previous_change() is True
        assert editor.textCursor().blockNumber() == 1

    def test_navigation_without_changes_does_nothing(self, editor):
        editor.setPlainText("a\nb\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        assert editor.next_change() is False
        assert editor.previous_change() is False


class TestGutterWiring:
    def test_gutter_is_wider_than_the_bookmark_and_fold_columns(self, editor):
        from je_editor.pyside_ui.code.plaintext_code_edit import code_edit_plaintext
        minimum = (code_edit_plaintext._BOOKMARK_MARKER_WIDTH
                   + code_edit_plaintext._FOLD_MARKER_WIDTH
                   + code_edit_plaintext._DIFF_MARKER_WIDTH)
        assert editor.line_number_width() > minimum

    def test_every_status_has_a_colour(self, editor):
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import (
            _DIFF_MARKER_COLOR_KEYS
        )
        from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
            actually_color_dict
        )
        for status in (LINE_ADDED, LINE_MODIFIED, LINE_REMOVED_ABOVE):
            assert actually_color_dict.get(_DIFF_MARKER_COLOR_KEYS[status]) is not None

    def test_painting_the_gutter_with_markers_does_not_raise(self, editor):
        editor.setPlainText("a\nB\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\nd\n")
        editor.show()
        editor.line_number.update()
        QApplication.processEvents()
        editor.hide()

    def test_edits_schedule_a_refresh_only_with_a_baseline(self, editor):
        editor.setPlainText("a\n")
        assert not editor._diff_timer.isActive()
        editor.diff_marker_manager.set_baseline("a\n")
        editor.setPlainText("b\n")
        assert editor._diff_timer.isActive()


class TestBaselineLoading:
    def test_no_file_clears_the_baseline(self, editor):
        editor.setPlainText("a\nB\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        editor.current_file = None
        editor.load_git_baseline()
        assert not editor.diff_marker_manager.has_baseline

    def test_loading_a_file_outside_a_repository_leaves_no_baseline(self, editor, tmp_path):
        loose = tmp_path / "loose.py"
        loose.write_text("print('x')\n", encoding="utf-8")
        editor.current_file = str(loose)
        editor.load_git_baseline()
        editor.diff_marker_manager.stop()
        assert not editor.diff_marker_manager.has_baseline

    def test_stop_is_safe_without_a_loader(self, editor):
        editor.diff_marker_manager.stop()
        editor.diff_marker_manager.stop()
