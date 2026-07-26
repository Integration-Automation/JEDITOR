"""Tests for indent-guide columns and trailing-whitespace detection."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.indentation.indent_guides import (
    MAX_GUIDES_PER_LINE,
    guide_columns,
    leading_space_width,
    trailing_whitespace_start,
)


class TestLeadingSpaceWidth:
    def test_spaces(self):
        assert leading_space_width("    code", 4) == 4

    def test_no_indent(self):
        assert leading_space_width("code", 4) == 0

    def test_tab_advances_to_the_next_stop(self):
        assert leading_space_width("\tcode", 4) == 4

    def test_space_then_tab_fills_the_stop(self):
        # Two spaces then a tab lands on the next multiple of four, not 2 + 4.
        assert leading_space_width("  \tcode", 4) == 4

    def test_only_leading_whitespace_counts(self):
        assert leading_space_width("  a  b", 4) == 2


class TestGuideColumns:
    def test_one_level(self):
        assert guide_columns("    code", 4) == [4]

    def test_two_levels(self):
        assert guide_columns("        code", 4) == [4, 8]

    def test_unindented_line_has_no_guides(self):
        assert guide_columns("code", 4) == []

    def test_blank_line_has_no_guides(self):
        assert guide_columns("", 4) == []
        assert guide_columns("      ", 4) == []

    def test_partial_indentation_rounds_down(self):
        assert guide_columns("      code", 4) == [4]

    def test_tab_indentation(self):
        assert guide_columns("\t\tcode", 4) == [4, 8]

    def test_guides_are_capped(self):
        deep = " " * (4 * (MAX_GUIDES_PER_LINE + 10)) + "code"
        assert len(guide_columns(deep, 4)) == MAX_GUIDES_PER_LINE

    def test_invalid_indent_size(self):
        assert guide_columns("    code", 0) == []


class TestTrailingWhitespace:
    def test_trailing_spaces(self):
        assert trailing_whitespace_start("code   ") == 4

    def test_trailing_tab(self):
        assert trailing_whitespace_start("code\t") == 4

    def test_clean_line(self):
        assert trailing_whitespace_start("code") is None

    def test_empty_line_is_not_reported(self):
        assert trailing_whitespace_start("") is None

    def test_whitespace_only_line_is_reported_from_the_start(self):
        assert trailing_whitespace_start("    ") == 0

    def test_inner_spaces_are_not_trailing(self):
        assert trailing_whitespace_start("a  b") is None


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
    code_editor.close()
    code_editor.deleteLater()


class TestPainting:
    def test_painting_indented_text_with_trailing_spaces_does_not_raise(self, editor):
        editor.setPlainText("def run():\n    x = 1   \n        y = 2\n")
        editor.show()
        QApplication.processEvents()
        editor.hide()

    def test_settings_can_turn_the_overlays_off(self, editor):
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        original = (
            user_setting_dict.get("show_indent_guides", True),
            user_setting_dict.get("show_trailing_whitespace", True),
        )
        user_setting_dict["show_indent_guides"] = False
        user_setting_dict["show_trailing_whitespace"] = False
        try:
            editor.setPlainText("    x = 1   \n")
            editor.show()
            QApplication.processEvents()
            editor.hide()
        finally:
            user_setting_dict["show_indent_guides"] = original[0]
            user_setting_dict["show_trailing_whitespace"] = original[1]

    def test_every_overlay_colour_is_defined(self, app):
        from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
            actually_color_dict
        )
        for key in ("indent_guide_color", "trailing_whitespace_color"):
            assert actually_color_dict.get(key) is not None
