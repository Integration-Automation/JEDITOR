"""Tests for folding the languages that delimit blocks with braces."""
from __future__ import annotations

import pytest

from je_editor.utils.code_folding.brace_regions import (
    compute_brace_fold_regions, fold_regions_for, uses_braces
)


def _regions(source: str, suffix: str = ".ts"):
    return compute_brace_fold_regions(source.split("\n"), suffix)


class TestWhichLanguagesUseBraces:
    @pytest.mark.parametrize("suffix", [".js", ".ts", ".rs", ".go", ".c", ".java"])
    def test_the_c_family_does(self, suffix):
        assert uses_braces(suffix) is True

    @pytest.mark.parametrize("suffix", [".py", ".yaml", ".toml", ".sh", ""])
    def test_the_indented_ones_do_not(self, suffix):
        assert uses_braces(suffix) is False

    def test_the_suffix_is_matched_case_insensitively(self):
        assert uses_braces(".TS") is True


class TestBracePairs:
    def test_a_block_folds_from_its_opening_brace(self):
        regions = _regions("function f() {\n    body();\n}\n")
        assert (regions[0].start, regions[0].end) == (0, 1)

    def test_the_closing_brace_stays_visible(self):
        regions = _regions("function f() {\n    a();\n    b();\n}\n")
        assert 3 not in regions[0].body_lines

    def test_a_brace_on_its_own_line_still_opens_a_region(self):
        # Indentation folding gets this wrong: the header is no more indented
        # than its body's first line.
        regions = _regions("function f()\n{\n    body();\n}\n")
        assert (regions[0].start, regions[0].end) == (1, 2)

    def test_nested_blocks_each_fold(self):
        regions = _regions("a {\n    b {\n        c();\n    }\n}\n")
        assert [(region.start, region.end) for region in regions] == [(0, 3), (1, 2)]

    def test_a_one_line_block_is_not_foldable(self):
        assert _regions("function f() { body(); }\n") == []

    def test_an_empty_block_is_not_foldable(self):
        assert _regions("function f() {\n}\n") == []

    def test_an_unclosed_brace_yields_nothing(self):
        assert _regions("function f() {\n    body();\n") == []

    def test_a_stray_closing_brace_is_ignored(self):
        assert _regions("}\n") == []

    def test_the_header_indent_is_recorded(self):
        regions = _regions("    if (x) {\n        y();\n    }\n")
        assert regions[0].indent == 4


class TestBracesThatDoNotCount:
    """A brace inside a string or comment would throw every pair out of step."""

    def test_a_brace_in_a_string_is_ignored(self):
        assert _regions('const a = "{";\nconst b = 2;\n') == []

    def test_a_brace_in_a_line_comment_is_ignored(self):
        assert _regions("// {\nconst b = 2;\n") == []

    def test_a_brace_in_a_block_comment_is_ignored(self):
        assert _regions("/* { */\nconst b = 2;\n") == []

    def test_a_block_comment_spanning_lines_is_ignored(self):
        assert _regions("/*\n{\n*/\nconst b = 2;\n") == []

    def test_an_escaped_quote_does_not_end_the_string(self):
        assert _regions('const a = "\\"{";\nconst b = 2;\n') == []

    def test_a_real_block_after_a_string_still_folds(self):
        regions = _regions('const a = "{";\nfunction f() {\n    body();\n}\n')
        assert (regions[0].start, regions[0].end) == (1, 2)

    def test_a_hash_comment_language_uses_its_own_marker(self):
        # Go uses //, so a # is just text; the braces on the line still count.
        regions = compute_brace_fold_regions(
            "func f() { // {\n    body()\n}".split("\n"), ".go")
        assert (regions[0].start, regions[0].end) == (0, 1)


class TestChoosingHowToFold:
    def test_a_brace_language_folds_on_braces(self):
        regions = fold_regions_for("function f()\n{\n    body();\n}".split("\n"), ".ts")
        assert (regions[0].start, regions[0].end) == (1, 2)

    def test_python_still_folds_on_indentation(self):
        regions = fold_regions_for("def f():\n    body()\n".split("\n"), ".py")
        assert (regions[0].start, regions[0].end) == (0, 1)

    def test_a_file_without_a_suffix_folds_on_indentation(self):
        regions = fold_regions_for("header\n    body\n".split("\n"), "")
        assert (regions[0].start, regions[0].end) == (0, 1)
