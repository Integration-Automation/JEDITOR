"""Tests for text statistics and their formatting."""
from __future__ import annotations

import pytest

from je_editor.utils.text_stats.text_statistics import text_statistics


class TestTextStatistics:
    def test_empty_text(self):
        stats = text_statistics("")
        assert (stats.lines, stats.words, stats.characters) == (0, 0, 0)

    def test_single_line(self):
        stats = text_statistics("hello world")
        assert stats.lines == 1
        assert stats.words == 2
        assert stats.characters == 11
        assert stats.characters_no_spaces == 10

    def test_multiple_lines(self):
        stats = text_statistics("a\nb\nc")
        assert stats.lines == 3
        assert stats.words == 3

    def test_trailing_newline_counts_line(self):
        # "a\n" -> two lines by count("\n")+1 convention
        assert text_statistics("a\n").lines == 2

    def test_words_split_on_any_whitespace(self):
        stats = text_statistics("a\tb  c\nd")
        assert stats.words == 4

    def test_characters_include_whitespace(self):
        assert text_statistics("a b").characters == 3

    def test_characters_no_spaces_excludes_all_whitespace(self):
        assert text_statistics("a \t\nb").characters_no_spaces == 2

    def test_unicode_counts_as_one_char(self):
        stats = text_statistics("café 🌏")
        assert stats.characters == 6  # c a f é space 🌏
        assert stats.words == 2

    def test_only_whitespace(self):
        stats = text_statistics("   \n  ")
        assert stats.words == 0
        assert stats.characters_no_spaces == 0
        assert stats.lines == 2


@pytest.mark.usefixtures("qapp")
class TestFormatStatistics:
    def test_format_contains_counts(self):
        from je_editor.pyside_ui.main_ui.menu.text_menu.build_text_menu import format_statistics
        stats = text_statistics("hello world\nfoo")
        message = format_statistics(stats, "Selection")
        assert "Selection" in message
        assert "3" in message   # words
        assert "2" in message   # lines
