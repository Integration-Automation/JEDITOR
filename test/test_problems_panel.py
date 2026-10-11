"""Tests for severity, project-wide checking and applying fixes."""
from __future__ import annotations

import json
import threading
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.code_scan.ruff_lint import (
    RUFF_SOURCE, apply_fixes, find_ruff_executable, lint_project
)
from je_editor.core.diagnostics.diagnostic_model import Diagnostic as UnifiedDiagnostic
from je_editor.core.diagnostics.diagnostic_model import Severity, TextRange
from je_editor.core.uri.resource_uri import to_uri
from je_editor.utils.lint.ruff_diagnostics import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    Diagnostic,
    parse_ruff_json,
    severity_for_code,
)


# Long enough that a slow machine still finishes; a hang fails rather than blocks.
WORKER_TIMEOUT_MS = 10_000


class TestSeverity:
    @pytest.mark.parametrize("code,expected", [
        ("F401", SEVERITY_ERROR),
        ("E501", SEVERITY_ERROR),
        ("W291", SEVERITY_WARNING),
        ("B008", SEVERITY_WARNING),
        ("S603", SEVERITY_WARNING),
        ("D100", SEVERITY_INFO),
    ])
    def test_code_prefix_decides(self, code, expected):
        assert severity_for_code(code) == expected

    def test_a_syntax_error_is_an_error(self):
        assert severity_for_code("") == SEVERITY_ERROR
        assert severity_for_code("SyntaxError") == SEVERITY_ERROR

    def test_diagnostic_derives_its_level(self):
        diagnostic = Diagnostic(
            line=1, column=1, end_line=1, end_column=2, code="W291", message="x")
        assert diagnostic.level == SEVERITY_WARNING

    def test_an_explicit_severity_wins(self):
        diagnostic = Diagnostic(
            line=1, column=1, end_line=1, end_column=2, code="W291", message="x",
            severity=SEVERITY_ERROR)
        assert diagnostic.level == SEVERITY_ERROR

    def test_ruff_output_carries_the_file(self):
        output = json.dumps([{
            "code": "F401", "message": "unused",
            "filename": "/project/app.py",
            "location": {"row": 1, "column": 1},
            "end_location": {"row": 1, "column": 5},
        }])
        assert parse_ruff_json(output)[0].file_path == "/project/app.py"


class TestProjectLint:
    def test_finds_problems_across_files(self, tmp_path):
        if find_ruff_executable() is None:
            pytest.skip("ruff is not installed in this environment")
        (tmp_path / "one.py").write_text("import os\n", encoding="utf-8")
        (tmp_path / "two.py").write_text("import sys\n", encoding="utf-8")
        diagnostics = lint_project(tmp_path)
        assert len(diagnostics) >= 2
        # Each finding says which file it came from, which is what makes a
        # project-wide list navigable.
        assert all(item.file_path for item in diagnostics)
        assert len({item.file_path for item in diagnostics}) == 2

    def test_a_clean_project_reports_nothing(self, tmp_path):
        if find_ruff_executable() is None:
            pytest.skip("ruff is not installed in this environment")
        (tmp_path / "clean.py").write_text("print('ok')\n", encoding="utf-8")
        assert lint_project(tmp_path) == []

    def test_missing_ruff_yields_nothing(self, tmp_path):
        with patch("je_editor.code_scan.ruff_lint.find_ruff_executable", return_value=None):
            assert lint_project(tmp_path) == []


class TestApplyFixes:
    def test_removes_an_unused_import(self, tmp_path):
        if find_ruff_executable() is None:
            pytest.skip("ruff is not installed in this environment")
        target = tmp_path / "fixable.py"
        target.write_text("import os\nprint('hello')\n", encoding="utf-8")
        assert apply_fixes(target) is True
        assert "import os" not in target.read_text(encoding="utf-8")

    def test_missing_ruff_is_reported(self, tmp_path):
        with patch("je_editor.code_scan.ruff_lint.find_ruff_executable", return_value=None):
            assert apply_fixes(tmp_path) is False


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class _FakeTabWidget:
    def __init__(self, widget=None):
        self._widget = widget

    def currentWidget(self):
        return self._widget


@pytest.fixture()
def panel(app):
    from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
        ProblemsPanelWidget
    )
    window = MagicMock()
    window.tab_widget = _FakeTabWidget(None)
    widget = ProblemsPanelWidget(window)
    yield widget
    widget.close()
    widget.deleteLater()


def _diagnostics() -> list[Diagnostic]:
    return [
        Diagnostic(line=1, column=1, end_line=1, end_column=2, code="F401", message="unused"),
        Diagnostic(line=2, column=1, end_line=2, end_column=2, code="W291", message="space"),
        Diagnostic(line=3, column=1, end_line=3, end_column=2, code="D100", message="docstring"),
    ]


SERVER = "rust-analyzer"


def _server_diagnostics() -> list[UnifiedDiagnostic]:
    """What a language server reported: one finding at each severity."""
    return [
        UnifiedDiagnostic("cannot find value", TextRange.from_lines(4), Severity.ERROR,
                          source=SERVER, code="E0425"),
        UnifiedDiagnostic("unused variable", TextRange.from_lines(5), Severity.WARNING,
                          source=SERVER, code="unused_variables"),
        UnifiedDiagnostic("consider borrowing", TextRange.from_lines(6), Severity.INFORMATION,
                          source=SERVER, code="clippy::needless_pass"),
        UnifiedDiagnostic("could be const", TextRange.from_lines(7), Severity.HINT,
                          source=SERVER, code="clippy::const"),
    ]


def _choose(combo, value) -> None:
    combo.setCurrentIndex(combo.findData(value))


class TestSeverityFilter:
    def test_everything_is_shown_by_default(self, panel):
        panel.set_diagnostics(_diagnostics())
        assert len(panel.visible_diagnostics()) == 3

    def test_filtering_to_errors(self, panel):
        panel.set_diagnostics(_diagnostics())
        _choose(panel.severity_filter, int(Severity.ERROR))
        assert [item.code for item in panel.visible_diagnostics()] == ["F401"]

    def test_filtering_to_warnings(self, panel):
        panel.set_diagnostics(_diagnostics())
        _choose(panel.severity_filter, int(Severity.WARNING))
        assert [item.code for item in panel.visible_diagnostics()] == ["W291"]

    def test_the_tree_follows_the_filter(self, panel):
        panel.set_diagnostics(_diagnostics())
        _choose(panel.severity_filter, int(Severity.INFORMATION))
        assert panel.result_tree.topLevelItemCount() == 1

    def test_the_filter_offers_all_four_severities(self, panel):
        offered = [panel.severity_filter.itemData(index)
                   for index in range(1, panel.severity_filter.count())]
        assert offered == [int(severity) for severity in Severity]

    @pytest.mark.parametrize("severity, code", [
        (Severity.ERROR, "E0425"), (Severity.WARNING, "unused_variables"),
        (Severity.INFORMATION, "clippy::needless_pass"), (Severity.HINT, "clippy::const"),
    ])
    def test_a_server_severity_is_filtered_as_the_server_gave_it(self, panel, severity, code):
        panel.set_diagnostics(_server_diagnostics())
        _choose(panel.severity_filter, int(severity))
        assert [item.code for item in panel.visible_diagnostics()] == [code]

    def test_the_severity_is_named_in_its_column(self, panel):
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import (
            COLUMN_SEVERITY
        )
        panel.set_diagnostics(_server_diagnostics())
        shown = [panel.result_tree.topLevelItem(row).text(COLUMN_SEVERITY)
                 for row in range(panel.result_tree.topLevelItemCount())]
        assert shown == ["Error", "Warning", "Information", "Hint"]


class TestSourceFilter:
    """ruff's findings and a language server's sit in one list and filter alike."""

    @pytest.fixture()
    def mixed(self, panel):
        panel.set_diagnostics(_diagnostics() + _server_diagnostics())
        return panel

    def test_both_sources_are_listed_together(self, mixed):
        assert [item.source for item in mixed.diagnostics()] == [RUFF_SOURCE] * 3 + [SERVER] * 4

    def test_the_filter_offers_the_sources_that_have_findings(self, mixed):
        offered = [mixed.source_filter.itemData(index)
                   for index in range(1, mixed.source_filter.count())]
        assert offered == sorted([RUFF_SOURCE, SERVER])

    def test_one_source_can_be_picked(self, mixed):
        _choose(mixed.source_filter, SERVER)
        assert {item.source for item in mixed.visible_diagnostics()} == {SERVER}
        assert mixed.result_tree.topLevelItemCount() == 4

    def test_severity_and_source_narrow_together(self, mixed):
        _choose(mixed.source_filter, SERVER)
        _choose(mixed.severity_filter, int(Severity.WARNING))
        assert [item.code for item in mixed.visible_diagnostics()] == ["unused_variables"]

    def test_a_severity_filter_cuts_across_both_sources(self, mixed):
        _choose(mixed.severity_filter, int(Severity.ERROR))
        assert [(item.source, item.code) for item in mixed.visible_diagnostics()] == [
            (RUFF_SOURCE, "F401"), (SERVER, "E0425")]

    def test_the_source_is_named_in_its_column(self, mixed):
        from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import COLUMN_SOURCE
        assert mixed.result_tree.topLevelItem(0).text(COLUMN_SOURCE) == RUFF_SOURCE

    def test_a_chosen_source_survives_a_recheck(self, mixed):
        _choose(mixed.source_filter, SERVER)
        mixed.set_diagnostics(_diagnostics() + _server_diagnostics())
        assert mixed.source_filter.currentData() == SERVER

    def test_a_source_that_went_away_falls_back_to_all(self, mixed):
        _choose(mixed.source_filter, SERVER)
        mixed.set_diagnostics(_diagnostics())
        assert mixed.source_filter.currentIndex() == 0
        assert len(mixed.visible_diagnostics()) == 3

    def test_the_order_does_not_depend_on_the_order_reported(self, panel):
        panel.set_diagnostics(_server_diagnostics() + _diagnostics())
        forwards = panel.visible_diagnostics()
        panel.set_diagnostics(list(reversed(_diagnostics() + _server_diagnostics())))
        assert panel.visible_diagnostics() == forwards


class TestFilesAcrossTheProject:
    def test_same_named_files_in_two_folders_are_both_listed(self, panel, tmp_path):
        first, second = tmp_path / "frontend" / "main.py", tmp_path / "backend" / "main.py"
        panel.set_diagnostics([
            Diagnostic(line=1, column=1, end_line=1, end_column=2, code="F401", message="a",
                       file_path=str(first)),
            Diagnostic(line=1, column=1, end_line=1, end_column=2, code="F401", message="b",
                       file_path=str(second)),
        ])
        assert sorted(item.uri for item in panel.diagnostics()) == sorted(
            [to_uri(first), to_uri(second)])

    def test_a_finding_in_another_file_opens_that_file(self, panel, tmp_path):
        target = tmp_path / "pkg" / "module.py"
        panel.set_diagnostics([Diagnostic(
            line=3, column=1, end_line=3, end_column=2, code="F401", message="unused",
            file_path=str(target))])
        panel.jump_to_diagnostic(panel.diagnostics()[0])
        panel._main_window.go_to_new_tab.assert_called_once()
        assert str(panel._main_window.go_to_new_tab.call_args.args[0]) == str(target)


class TestProjectScope:
    """
    The project check spawns ruff over every file, so it runs on a worker
    thread: the panel gets its result through a signal rather than a return
    value, and the window stays responsive while it runs.
    """

    def _run_project_check(self, panel, trigger=None):
        """Start a project check and wait for it to report back."""
        with patch(
            "je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker.lint_project",
            return_value=_diagnostics(),
        ) as mock_lint:
            if trigger is None:
                panel.project_check.setChecked(True)
            else:
                trigger()
            worker = panel._project_worker
            assert worker is not None, "no background check was started"
            worker.wait(WORKER_TIMEOUT_MS)
            QApplication.processEvents()
        return mock_lint

    def test_project_mode_lints_the_root(self, panel, tmp_path):
        assert self._run_project_check(panel).called

    def test_the_result_reaches_the_panel(self, panel):
        self._run_project_check(panel)
        assert len(panel.diagnostics()) == 3

    def test_the_check_does_not_run_on_the_ui_thread(self, panel):
        seen: list[int] = []
        with patch(
            "je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker.lint_project",
            side_effect=lambda root: seen.append(threading.get_ident()) or [],
        ):
            panel.project_check.setChecked(True)
            worker = panel._project_worker
            assert worker is not None
            worker.wait(WORKER_TIMEOUT_MS)
        assert seen and seen[0] != threading.get_ident()

    def test_rechecking_replaces_the_previous_run(self, panel):
        self._run_project_check(panel)
        self._run_project_check(panel, trigger=panel.refresh)
        assert len(panel.diagnostics()) == 3

    def test_fixing_without_a_file_does_nothing(self, panel):
        panel.project_check.setChecked(False)
        assert panel.apply_available_fixes() is False
