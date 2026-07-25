"""Tests for parsing ruff's JSON output into diagnostics."""
from __future__ import annotations

import json

from je_editor.utils.lint.ruff_diagnostics import (
    SYNTAX_ERROR_CODE,
    Diagnostic,
    diagnostics_by_line,
    message_for_line,
    parse_ruff_json,
)


def _entry(**overrides) -> dict:
    entry = {
        "code": "F401",
        "message": "`os` imported but unused",
        "filename": "/project/app.py",
        "location": {"row": 1, "column": 8},
        "end_location": {"row": 1, "column": 10},
        "fix": None,
        "noqa_row": 1,
        "url": "https://docs.astral.sh/ruff/rules/unused-import",
    }
    entry.update(overrides)
    return entry


class TestParseRuffJson:
    def test_single_finding(self):
        found = parse_ruff_json(json.dumps([_entry()]))
        assert found == [Diagnostic(
            line=1, column=8, end_line=1, end_column=10,
            code="F401", message="`os` imported but unused")]

    def test_several_findings_keep_their_order(self):
        output = json.dumps([
            _entry(location={"row": 3, "column": 1}),
            _entry(location={"row": 1, "column": 1}),
        ])
        assert [item.line for item in parse_ruff_json(output)] == [3, 1]

    def test_empty_output(self):
        assert parse_ruff_json("") == []
        assert parse_ruff_json("   \n") == []

    def test_empty_json_array(self):
        assert parse_ruff_json("[]") == []

    def test_invalid_json_is_ignored(self):
        assert parse_ruff_json("ruff: command failed") == []

    def test_json_object_instead_of_array_is_ignored(self):
        assert parse_ruff_json('{"error": "boom"}') == []

    def test_entry_without_a_message_is_skipped(self):
        assert parse_ruff_json(json.dumps([_entry(message=None)])) == []

    def test_entry_that_is_not_an_object_is_skipped(self):
        assert parse_ruff_json(json.dumps(["nonsense", _entry()])) == [
            parse_ruff_json(json.dumps([_entry()]))[0]]

    def test_syntax_error_without_a_code(self):
        found = parse_ruff_json(json.dumps([_entry(code=None, message="SyntaxError: bad")]))
        assert found[0].code == SYNTAX_ERROR_CODE
        assert found[0].label == "SyntaxError SyntaxError: bad"

    def test_missing_location_falls_back_to_the_first_line(self):
        found = parse_ruff_json(json.dumps([_entry(location=None, end_location=None)]))
        assert (found[0].line, found[0].column) == (1, 1)

    def test_missing_end_location_falls_back_to_the_start(self):
        found = parse_ruff_json(json.dumps([_entry(end_location=None)]))
        assert (found[0].end_line, found[0].end_column) == (1, 8)

    def test_end_before_start_is_clamped(self):
        found = parse_ruff_json(json.dumps([
            _entry(location={"row": 5, "column": 2}, end_location={"row": 2, "column": 1})]))
        assert found[0].end_line == 5

    def test_non_integer_position_is_ignored(self):
        found = parse_ruff_json(json.dumps([_entry(location={"row": "x", "column": None})]))
        assert (found[0].line, found[0].column) == (1, 1)

    def test_label_includes_the_code(self):
        assert parse_ruff_json(json.dumps([_entry()]))[0].label.startswith("F401 ")


class TestGrouping:
    def test_diagnostics_by_line(self):
        output = json.dumps([
            _entry(location={"row": 2, "column": 1}),
            _entry(location={"row": 2, "column": 5}),
            _entry(location={"row": 7, "column": 1}),
        ])
        grouped = diagnostics_by_line(parse_ruff_json(output))
        assert sorted(grouped) == [2, 7]
        assert len(grouped[2]) == 2

    def test_message_for_line_joins_every_finding(self):
        output = json.dumps([
            _entry(location={"row": 2, "column": 1}, message="first"),
            _entry(location={"row": 2, "column": 5}, message="second"),
        ])
        message = message_for_line(parse_ruff_json(output), 2)
        assert "first" in message and "second" in message
        assert message.count("\n") == 1

    def test_message_for_a_clean_line(self):
        assert message_for_line(parse_ruff_json(json.dumps([_entry()])), 99) is None

    def test_message_with_no_diagnostics(self):
        assert message_for_line([], 1) is None
