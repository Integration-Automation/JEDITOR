"""Tests for the unified diagnostic model, its store, and the bridge to the older shape."""
from __future__ import annotations

import pytest

from je_editor.core.diagnostics.diagnostic_model import (
    Diagnostic, DiagnosticStore, Position, QuickFix, RelatedInformation, Severity,
    TextEdit, TextRange, filter_diagnostics
)
from je_editor.core.diagnostics.legacy_diagnostics import from_legacy, to_legacy, unify
from je_editor.core.uri.resource_uri import to_path, to_uri
from je_editor.utils.lint.ruff_diagnostics import (
    SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_WARNING
)
from je_editor.utils.lint.ruff_diagnostics import Diagnostic as LegacyDiagnostic
from je_editor.utils.lint.ruff_diagnostics import parse_ruff_json
from je_editor.utils.lsp.lsp_protocol import diagnostic_entries

RUFF = "ruff"
SERVER = "rust-analyzer"
# What ruff's JSON output looks like for one unused import
RUFF_OUTPUT = (
    '[{"code": "F401", "message": "`os` imported but unused", '
    '"location": {"row": 1, "column": 8}, "end_location": {"row": 1, "column": 10}}]'
)
# The parameters of one ``publishDiagnostics`` notification from a language server
SERVER_NOTIFICATION = {"diagnostics": [{
    "range": {"start": {"line": 4, "character": 0}, "end": {"line": 4, "character": 6}},
    "severity": 2, "code": "unused_variables", "message": "unused variable: `x`",
}]}


def finding(message: str, line: int = 1, severity: Severity = Severity.ERROR,
            code: str = "") -> Diagnostic:
    return Diagnostic(message, TextRange.from_lines(line), severity, code=code)


@pytest.fixture()
def uri(tmp_path):
    return to_uri(tmp_path / "sample.py")


@pytest.fixture()
def other_uri(tmp_path):
    return to_uri(tmp_path / "other.py")


class TestSeverity:
    @pytest.mark.parametrize("lsp_number, expected", [
        (1, Severity.ERROR), (2, Severity.WARNING), (3, Severity.INFORMATION), (4, Severity.HINT),
    ])
    def test_the_numbers_are_the_ones_lsp_uses(self, lsp_number, expected):
        assert Severity(lsp_number) is expected

    def test_a_more_severe_level_sorts_first(self):
        assert sorted(Severity) == [
            Severity.ERROR, Severity.WARNING, Severity.INFORMATION, Severity.HINT]


class TestTextRange:
    def test_a_single_point_is_an_empty_range(self):
        span = TextRange.from_lines(3, 5)
        assert span.start == span.end == Position(3, 5)

    def test_all_four_numbers_are_kept(self):
        span = TextRange.from_lines(3, 5, 4, 2)
        assert (span.start, span.end) == (Position(3, 5), Position(4, 2))

    @pytest.mark.parametrize("line, column", [(0, 0), (-4, 7), (2, -1)])
    def test_numbers_below_one_are_raised_to_one(self, line, column):
        span = TextRange.from_lines(line, column)
        assert span.start.line >= 1 and span.start.column >= 1

    @pytest.mark.parametrize("end_line, end_column", [(2, 9), (5, 3)])
    def test_an_end_before_the_start_falls_back_to_the_start(self, end_line, end_column):
        span = TextRange.from_lines(5, 4, end_line, end_column)
        assert span.end == span.start


class TestDiagnostic:
    def test_the_label_leads_with_the_code(self):
        assert finding("unused import", code="F401").label == "F401 unused import"

    def test_the_label_is_the_message_when_there_is_no_code(self):
        assert finding("unexpected token").label == "unexpected token"

    def test_it_carries_related_locations_and_fixes(self, uri):
        related = RelatedInformation(uri, TextRange.from_lines(9), "first defined here")
        fix = QuickFix("Remove the import", (TextEdit(TextRange.from_lines(1, 1, 2, 1), ""),))
        diagnostic = Diagnostic("redefinition", TextRange.from_lines(12), related=(related,),
                                fixes=(fix,))
        assert diagnostic.related[0].message == "first defined here"
        assert diagnostic.fixes[0].edits[0].new_text == ""


class TestFilterDiagnostics:
    @pytest.fixture()
    def mixed(self):
        return [
            Diagnostic("hint", TextRange.from_lines(4), Severity.HINT, source=SERVER),
            Diagnostic("error", TextRange.from_lines(3), Severity.ERROR, source=RUFF),
            Diagnostic("info", TextRange.from_lines(2), Severity.INFORMATION, source=SERVER),
            Diagnostic("warning", TextRange.from_lines(1), Severity.WARNING, source=RUFF),
        ]

    def test_no_filter_keeps_everything_in_position_order(self, mixed):
        assert [item.message for item in filter_diagnostics(mixed)] == [
            "warning", "info", "error", "hint"]

    @pytest.mark.parametrize("severity, message", [
        (Severity.ERROR, "error"), (Severity.WARNING, "warning"),
        (Severity.INFORMATION, "info"), (Severity.HINT, "hint"),
    ])
    def test_each_severity_can_be_picked_alone(self, mixed, severity, message):
        assert [item.message for item in filter_diagnostics(mixed, [severity])] == [message]

    def test_several_severities_can_be_picked_together(self, mixed):
        kept = filter_diagnostics(mixed, [Severity.ERROR, Severity.WARNING])
        assert [item.message for item in kept] == ["warning", "error"]

    def test_a_source_can_be_picked(self, mixed):
        kept = filter_diagnostics(mixed, sources=[SERVER])
        assert [item.message for item in kept] == ["info", "hint"]

    def test_severity_and_source_narrow_together(self, mixed):
        kept = filter_diagnostics(mixed, [Severity.HINT, Severity.ERROR], [SERVER])
        assert [item.message for item in kept] == ["hint"]

    def test_an_empty_filter_keeps_nothing(self, mixed):
        assert filter_diagnostics(mixed, severities=[]) == []

    def test_the_order_does_not_depend_on_the_order_given(self, mixed):
        assert filter_diagnostics(mixed) == filter_diagnostics(list(reversed(mixed)))

    def test_on_one_line_the_more_severe_finding_comes_first(self):
        same_line = [finding("minor", severity=Severity.HINT), finding("major")]
        assert [item.message for item in filter_diagnostics(same_line)] == ["major", "minor"]


class TestDiagnosticStore:
    def test_a_report_is_stamped_with_its_source_and_resource(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("unused import")])
        stored = store.select()[0]
        assert (stored.source, stored.uri) == (RUFF, uri)

    def test_a_new_report_replaces_the_previous_one(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("first"), finding("second", 2)])
        store.publish(RUFF, uri, [finding("third")])
        assert [item.message for item in store.select()] == ["third"]

    def test_one_source_does_not_replace_another(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("from ruff")])
        store.publish(SERVER, uri, [finding("from the server", 2)])
        assert [item.source for item in store.select()] == [RUFF, SERVER]
        assert store.sources() == sorted([RUFF, SERVER])

    def test_an_empty_report_clears_that_source_only(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("from ruff")])
        store.publish(SERVER, uri, [finding("from the server")])
        assert store.publish(RUFF, uri, []) is True
        assert [item.source for item in store.select()] == [SERVER]

    def test_publishing_the_same_report_again_changes_nothing(self, uri):
        store = DiagnosticStore()
        announced = []
        store.changed.subscribe(announced.append)
        assert store.publish(RUFF, uri, [finding("same")]) is True
        assert store.publish(RUFF, uri, [finding("same")]) is False
        assert store.publish(SERVER, uri, []) is False
        assert announced == [uri]

    def test_two_resources_are_kept_apart(self, uri, other_uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("here")])
        store.publish(RUFF, other_uri, [finding("there")])
        assert [item.message for item in store.select(uri=uri)] == ["here"]
        assert [item.message for item in store.select(uri=other_uri)] == ["there"]
        assert len(store) == 2

    def test_another_spelling_of_the_path_reaches_the_same_report(self, tmp_path):
        store = DiagnosticStore()
        store.publish(RUFF, to_uri(tmp_path / "sample.py"), [finding("first")])
        store.publish(RUFF, to_uri(tmp_path / "pkg" / ".." / "sample.py"), [finding("second")])
        assert [item.message for item in store.select()] == ["second"]

    def test_the_store_filters_by_severity_and_source(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("error"), finding("warning", 2, Severity.WARNING)])
        store.publish(SERVER, uri, [finding("hint", 3, Severity.HINT)])
        assert [item.message for item in store.select([Severity.WARNING])] == ["warning"]
        assert [item.message for item in store.select(sources=[SERVER])] == ["hint"]

    def test_counts_cover_every_severity(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("a"), finding("b", 2), finding("c", 3, Severity.HINT)])
        assert store.counts() == {
            Severity.ERROR: 2, Severity.WARNING: 0, Severity.INFORMATION: 0, Severity.HINT: 1}

    def test_clearing_a_source_leaves_the_others(self, uri, other_uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("ruff here")])
        store.publish(RUFF, other_uri, [finding("ruff there")])
        store.publish(SERVER, uri, [finding("server here")])
        assert store.clear(source=RUFF) is True
        assert [item.message for item in store.select()] == ["server here"]

    def test_clearing_a_resource_leaves_the_others(self, uri, other_uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("here")])
        store.publish(RUFF, other_uri, [finding("there")])
        assert store.clear(uri=uri) is True
        assert [item.message for item in store.select()] == ["there"]

    def test_clearing_announces_each_resource_once(self, uri, other_uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [finding("a")])
        store.publish(SERVER, uri, [finding("b")])
        store.publish(RUFF, other_uri, [finding("c")])
        announced = []
        store.changed.subscribe(announced.append)
        assert store.clear() is True
        assert sorted(announced) == sorted([uri, other_uri])
        assert len(store) == 0

    def test_clearing_an_empty_store_reports_nothing_dropped(self):
        store = DiagnosticStore()
        announced = []
        store.changed.subscribe(announced.append)
        assert store.clear() is False
        assert announced == []


class TestLegacyBridge:
    @pytest.mark.parametrize("legacy_severity, expected", [
        (SEVERITY_ERROR, Severity.ERROR), (SEVERITY_WARNING, Severity.WARNING),
        (SEVERITY_INFO, Severity.INFORMATION),
    ])
    def test_an_explicit_severity_is_carried_over(self, legacy_severity, expected):
        legacy = LegacyDiagnostic(1, 1, 1, 2, "X1", "message", severity=legacy_severity)
        assert from_legacy(legacy, RUFF).severity is expected

    @pytest.mark.parametrize("code, expected", [
        ("F401", Severity.ERROR), ("W291", Severity.WARNING), ("D100", Severity.INFORMATION),
    ])
    def test_a_severity_derived_from_the_rule_code_is_carried_over(self, code, expected):
        legacy = LegacyDiagnostic(1, 1, 1, 2, code, "message")
        assert from_legacy(legacy, RUFF).severity is expected

    def test_position_code_message_and_source_are_carried_over(self, uri):
        legacy = LegacyDiagnostic(3, 5, 4, 2, "F401", "unused import")
        converted = from_legacy(legacy, RUFF, uri)
        assert converted.range == TextRange(Position(3, 5), Position(4, 2))
        assert (converted.code, converted.message, converted.source) == (
            "F401", "unused import", RUFF)

    def test_the_resource_falls_back_to_the_given_uri(self, uri):
        legacy = LegacyDiagnostic(1, 1, 1, 1, "F401", "buffer only")
        assert from_legacy(legacy, RUFF, uri).uri == uri

    def test_a_file_path_on_the_older_diagnostic_wins(self, tmp_path, uri):
        target = tmp_path / "project_wide.py"
        legacy = LegacyDiagnostic(1, 1, 1, 1, "F401", "from a project check",
                                  file_path=str(target))
        assert from_legacy(legacy, RUFF, uri).uri == to_uri(target)

    def test_a_round_trip_gives_back_an_equivalent_older_diagnostic(self, tmp_path):
        legacy = LegacyDiagnostic(3, 5, 4, 2, "W291", "trailing whitespace",
                                  file_path=to_path(to_uri(tmp_path / "a.py")))
        back = to_legacy(from_legacy(legacy, RUFF))
        assert back.level == legacy.level
        assert (back.line, back.column, back.end_line, back.end_column, back.code,
                back.message, back.file_path) == (
            legacy.line, legacy.column, legacy.end_line, legacy.end_column, legacy.code,
            legacy.message, legacy.file_path)

    def test_a_hint_becomes_information_in_the_older_shape(self):
        assert to_legacy(finding("consider renaming", severity=Severity.HINT)).level == SEVERITY_INFO

    def test_a_diagnostic_without_a_resource_has_no_file_path(self):
        assert to_legacy(finding("buffer only")).file_path == ""


class TestUnify:
    def test_a_unified_diagnostic_is_kept_as_it_is(self, uri):
        already = Diagnostic("from a server", TextRange.from_lines(2), Severity.HINT,
                             source=SERVER, uri=uri)
        assert unify([already], RUFF, "file:///ignored.py") == [already]

    def test_an_older_diagnostic_gains_the_source_and_the_resource(self, uri):
        legacy = LegacyDiagnostic(1, 1, 1, 2, "F401", "unused")
        converted = unify([legacy], RUFF, uri)[0]
        assert (converted.source, converted.uri, converted.code) == (RUFF, uri, "F401")

    def test_a_mixed_list_keeps_its_order(self, uri):
        already = Diagnostic("second", TextRange.from_lines(2), source=SERVER)
        legacy = LegacyDiagnostic(1, 1, 1, 2, "F401", "first")
        assert [item.message for item in unify([legacy, already], RUFF, uri)] == [
            "first", "second"]

    def test_an_empty_list_stays_empty(self):
        assert unify([], RUFF) == []


class TestBothSourcesShareTheModel:
    """
    ruff output and a language server's notification land in one store.

    The existing LSP parser does not carry the server's severity through yet, so
    the fixture supplies it; reading it from the notification is the diagnostics
    milestone's job.
    """

    @pytest.fixture()
    def store(self, uri):
        store = DiagnosticStore()
        store.publish(RUFF, uri, [
            from_legacy(item, RUFF) for item in parse_ruff_json(RUFF_OUTPUT)])
        store.publish(SERVER, uri, [
            Diagnostic(entry["message"],
                       TextRange.from_lines(entry["line"], entry["column"], entry["end_line"],
                                            entry["end_column"]),
                       Severity.WARNING, code=entry["code"])
            for entry in diagnostic_entries(SERVER_NOTIFICATION)])
        return store

    def test_both_are_listed_together_in_position_order(self, store):
        assert [(item.source, item.code, item.range.start.line) for item in store.select()] == [
            (RUFF, "F401", 1), (SERVER, "unused_variables", 5)]

    def test_a_severity_filter_cuts_across_both_sources(self, store):
        assert [item.source for item in store.select([Severity.WARNING])] == [SERVER]
        assert [item.source for item in store.select([Severity.ERROR])] == [RUFF]
