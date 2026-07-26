"""Tests for diffing the open file against its committed version."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.file_diff.unified import unified_diff_text


class TestUnifiedDiffText:
    def test_identical_text_produces_no_diff(self):
        assert unified_diff_text("a\nb\n", "a\nb\n") == ""

    def test_changed_line_appears_on_both_sides(self):
        diff = unified_diff_text("a\nb\n", "a\nB\n")
        assert "-b" in diff
        assert "+B" in diff

    def test_added_line_is_marked(self):
        diff = unified_diff_text("a\n", "a\nb\n")
        assert "+b" in diff

    def test_removed_line_is_marked(self):
        diff = unified_diff_text("a\nb\n", "a\n")
        assert "-b" in diff

    def test_header_names_both_sides(self):
        diff = unified_diff_text("a\n", "b\n", "app.py")
        assert "a/app.py" in diff and "HEAD" in diff
        assert "b/app.py" in diff and "working copy" in diff

    def test_header_without_a_file_name(self):
        diff = unified_diff_text("a\n", "b\n")
        assert "HEAD" in diff and "working copy" in diff

    def test_context_lines_are_limited(self):
        baseline = "".join(f"line{index}\n" for index in range(40))
        current = baseline.replace("line20", "CHANGED")
        diff = unified_diff_text(baseline, current, context_lines=1)
        assert "line19" in diff
        assert "line10" not in diff

    def test_empty_baseline_shows_the_whole_file_as_added(self):
        diff = unified_diff_text("", "a\nb\n")
        assert "+a" in diff and "+b" in diff


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


class _FakeTabWidget:
    def __init__(self, widget=None):
        self._widget = widget
        self.added = []

    def currentWidget(self):
        return self._widget

    def count(self):
        return len(self.added)

    def addTab(self, widget, label):
        self.added.append((widget, label))


def _window_with(editor, monkey_editor_widget=True):
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab = MagicMock(spec=EditorWidget) if monkey_editor_widget else object()
    if monkey_editor_widget:
        tab.code_edit = editor
    window = MagicMock()
    window.tab_widget = _FakeTabWidget(tab)
    return window


class TestHeadDiffTab:
    def test_diff_text_uses_the_editor_baseline(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import head_diff_text
        editor.setPlainText("a\nCHANGED\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        diff = head_diff_text(_window_with(editor))
        assert "-b" in diff and "+CHANGED" in diff

    def test_no_baseline_means_no_diff(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import head_diff_text
        editor.setPlainText("a\n")
        assert head_diff_text(_window_with(editor)) == ""

    def test_unchanged_file_means_no_diff(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import head_diff_text
        editor.setPlainText("a\nb\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        assert head_diff_text(_window_with(editor)) == ""

    def test_a_non_editor_tab_means_no_diff(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import head_diff_text
        assert head_diff_text(_window_with(editor, monkey_editor_widget=False)) == ""


class TestStagedDiffTab:
    """
    Staging hunk by hunk is only meaningful if what went into the index can be
    seen; the diff against HEAD shows every change, staged or not. The comparison
    existed but nothing opened it.
    """

    def test_a_staged_difference_opens_a_tab(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import (
            add_staged_diff_tab
        )
        editor.staged_diff_text = lambda: "--- a\n+++ b\n-old\n+new\n"
        window = _window_with(editor)
        assert add_staged_diff_tab(window) is True
        assert len(window.tab_widget.added) == 1

    def test_no_difference_opens_nothing(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import (
            add_staged_diff_tab
        )
        editor.staged_diff_text = lambda: ""
        window = _window_with(editor)
        assert add_staged_diff_tab(window) is False
        assert window.tab_widget.added == []

    def test_a_non_editor_tab_opens_nothing(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import (
            add_staged_diff_tab
        )
        assert add_staged_diff_tab(_window_with(editor, monkey_editor_widget=False)) is False

    def test_opening_the_tab_without_changes_does_nothing(self, editor):
        from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import add_head_diff_tab
        editor.setPlainText("a\n")
        editor.diff_marker_manager.set_baseline("a\n")
        window = _window_with(editor)
        assert add_head_diff_tab(window) is False
        assert window.tab_widget.added == []
