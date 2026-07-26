"""Tests for severity, project-wide checking and applying fixes."""
from __future__ import annotations

import json
import threading
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.code_scan.ruff_lint import apply_fixes, find_ruff_executable, lint_project
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


class TestSeverityFilter:
    def test_everything_is_shown_by_default(self, panel):
        panel._diagnostics = _diagnostics()
        assert len(panel.visible_diagnostics()) == 3

    def test_filtering_to_errors(self, panel):
        panel._diagnostics = _diagnostics()
        panel.severity_filter.setCurrentIndex(panel.severity_filter.findData(SEVERITY_ERROR))
        assert [item.code for item in panel.visible_diagnostics()] == ["F401"]

    def test_filtering_to_warnings(self, panel):
        panel._diagnostics = _diagnostics()
        panel.severity_filter.setCurrentIndex(panel.severity_filter.findData(SEVERITY_WARNING))
        assert [item.code for item in panel.visible_diagnostics()] == ["W291"]

    def test_the_tree_follows_the_filter(self, panel):
        panel._diagnostics = _diagnostics()
        panel.severity_filter.setCurrentIndex(panel.severity_filter.findData(SEVERITY_INFO))
        assert panel.result_tree.topLevelItemCount() == 1


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
