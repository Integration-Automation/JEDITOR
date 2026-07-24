"""Tests for indentation-based fold region computation."""
from __future__ import annotations

import textwrap

from je_editor.utils.code_folding.fold_regions import (
    FoldRegion,
    compute_fold_regions,
    line_indent,
    region_at_line,
)


def _regions(source: str) -> list[FoldRegion]:
    return compute_fold_regions(textwrap.dedent(source).split("\n"))


class TestLineIndent:
    """Indent measurement, including blanks and tabs."""

    def test_no_indent(self):
        assert line_indent("def run():") == 0

    def test_space_indent(self):
        assert line_indent("    return 1") == 4

    def test_blank_line_is_none(self):
        assert line_indent("   ") is None

    def test_empty_line_is_none(self):
        assert line_indent("") is None

    def test_tab_is_expanded(self):
        # A leading tab expands to the tab width, larger than a single space.
        assert line_indent("\tx = 1") > line_indent(" x = 1")


class TestComputeFoldRegions:
    """Region detection from indentation."""

    def test_no_regions_in_flat_code(self):
        assert _regions("a = 1\nb = 2\nc = 3\n") == []

    def test_simple_function_is_foldable(self):
        regions = _regions("""
            def run():
                x = 1
                y = 2
            """)
        # Line 0 is blank (dedent leading newline); header is line 1.
        assert any(region.start == 1 and region.end == 3 for region in regions)

    def test_header_indent_is_recorded(self):
        regions = _regions("def run():\n    x = 1\n")
        assert regions[0].indent == 0

    def test_nested_regions_are_found(self):
        regions = _regions("""
            class A:
                def m(self):
                    x = 1
            """)
        starts = {region.start for region in regions}
        # both the class (line 1) and the method (line 2) are headers
        assert {1, 2} <= starts

    def test_trailing_blank_lines_are_excluded(self):
        regions = _regions("def run():\n    x = 1\n\n\n")
        region = region_at_line(regions, 0)
        assert region is not None
        assert region.end == 1  # not the blank lines after

    def test_blank_line_inside_block_is_included(self):
        regions = _regions("def run():\n    x = 1\n\n    y = 2\n")
        region = region_at_line(regions, 0)
        assert region.end == 3  # spans across the internal blank line

    def test_single_line_is_not_foldable(self):
        assert _regions("x = 1\n") == []

    def test_dedent_ends_the_region(self):
        regions = _regions("def a():\n    x = 1\ndef b():\n    y = 2\n")
        region_a = region_at_line(regions, 0)
        assert region_a.start == 0 and region_a.end == 1

    def test_body_lines_are_the_hidden_lines(self):
        region = FoldRegion(start=2, end=5, indent=0)
        assert list(region.body_lines) == [3, 4, 5]

    def test_empty_input(self):
        assert compute_fold_regions([]) == []

    def test_region_at_line_returns_none_when_absent(self):
        regions = _regions("def run():\n    x = 1\n")
        assert region_at_line(regions, 99) is None

    def test_deeply_nested_staircase(self):
        lines = [("    " * depth) + f"if x{depth}:" for depth in range(6)]
        lines.append("    " * 6 + "pass")
        regions = compute_fold_regions(lines)
        # every 'if' line heads a region that reaches the final 'pass'
        assert all(region.end == 6 for region in regions)
        assert {region.start for region in regions} == set(range(6))
