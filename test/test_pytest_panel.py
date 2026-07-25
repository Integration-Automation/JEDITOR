"""Tests for parsing pytest output and showing it in the test panel."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.test_runner.pytest_output import (
    PytestResult,
    failure_for_result,
    parse_failures,
    parse_results,
    parse_summary,
)

SAMPLE_OUTPUT = """
============================= test session starts =============================
collected 3 items

test/test_alpha.py::TestAlpha::test_one PASSED                           [ 33%]
test/test_alpha.py::TestAlpha::test_two FAILED                           [ 66%]
test/test_beta.py::test_three SKIPPED                                    [100%]

=================================== FAILURES ==================================
D:\\project\\test\\test_alpha.py:42: AssertionError: expected 1 got 2
=========================== short test summary info ===========================
========================= 1 failed, 1 passed, 1 skipped in 0.42s ==============
"""


class TestParseResults:
    def test_every_reported_test_is_read(self):
        assert len(parse_results(SAMPLE_OUTPUT)) == 3

    def test_outcomes_are_kept(self):
        outcomes = [result.outcome for result in parse_results(SAMPLE_OUTPUT)]
        assert outcomes == ["PASSED", "FAILED", "SKIPPED"]

    def test_node_is_split_into_file_and_name(self):
        result = parse_results(SAMPLE_OUTPUT)[0]
        assert result.file_path == "test/test_alpha.py"
        assert result.name == "TestAlpha::test_one"

    def test_failed_flag(self):
        results = parse_results(SAMPLE_OUTPUT)
        assert results[1].failed is True
        assert results[0].failed is False
        assert results[2].failed is False

    def test_an_error_counts_as_a_failure(self):
        assert parse_results("test/x.py::test_a ERROR [100%]")[0].failed is True

    def test_output_without_results(self):
        assert parse_results("collected 0 items\n") == []

    def test_empty_output(self):
        assert parse_results("") == []


class TestParseFailures:
    def test_failure_location_is_read(self):
        failures = parse_failures(SAMPLE_OUTPUT)
        assert len(failures) == 1
        assert failures[0].line == 42
        assert failures[0].path.endswith("test_alpha.py")

    def test_message_is_kept(self):
        assert "expected 1 got 2" in parse_failures(SAMPLE_OUTPUT)[0].message

    def test_result_lines_are_not_mistaken_for_locations(self):
        assert parse_failures("test/test_a.py::test_one PASSED [100%]") == []

    def test_duplicates_are_dropped(self):
        repeated = "x.py:10: boom\nx.py:10: boom\n"
        assert len(parse_failures(repeated)) == 1

    def test_no_failures(self):
        assert parse_failures("all good\n") == []


class TestParseSummary:
    def test_summary_is_read(self):
        assert "1 failed" in parse_summary(SAMPLE_OUTPUT)

    def test_output_without_a_summary(self):
        assert parse_summary("nothing here\n") == ""


class TestFailureForResult:
    def test_matches_by_file(self):
        results = parse_results(SAMPLE_OUTPUT)
        failure = failure_for_result(results[1], parse_failures(SAMPLE_OUTPUT))
        assert failure is not None and failure.line == 42

    def test_passing_test_has_no_failure(self):
        results = parse_results(SAMPLE_OUTPUT)
        assert failure_for_result(results[0], parse_failures(SAMPLE_OUTPUT)) is None

    def test_failure_in_another_file_is_not_matched(self):
        result = PytestResult(node_id="test/test_other.py::test_x", outcome="FAILED")
        assert failure_for_result(result, parse_failures(SAMPLE_OUTPUT)) is None


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def panel(app, tmp_path):
    from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import TestPanelWidget
    widget = TestPanelWidget(main_window=None, working_dir=str(tmp_path))
    yield widget
    widget.close()
    widget.deleteLater()


class TestTestPanel:
    def test_starts_empty(self, panel):
        assert panel.results() == []
        assert panel.result_tree.topLevelItemCount() == 0

    def test_output_fills_the_tree(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert panel.result_tree.topLevelItemCount() == 3

    def test_failures_are_listed_first(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert panel.result_tree.topLevelItem(0).text(0) == "FAILED"

    def test_summary_reaches_the_status_label(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert "1 failed" in panel.status_label.text()

    def test_output_without_tests_says_so(self, panel):
        panel.apply_output("collected 0 items\n")
        assert panel.status_label.text() != ""
        assert panel.results() == []

    def test_opening_without_a_window_is_safe(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert panel.open_result(panel.results()[0]) is False

    def test_opening_a_failure_jumps_to_its_line(self, app, tmp_path):
        from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import TestPanelWidget
        window = MagicMock()
        window.tab_widget = MagicMock()
        window.tab_widget.currentWidget.return_value = None
        panel = TestPanelWidget(main_window=window, working_dir=str(tmp_path))
        panel.apply_output(SAMPLE_OUTPUT)
        failed = [result for result in panel.results() if result.failed][0]
        assert panel.open_result(failed) is True
        window.go_to_new_tab.assert_called_once()
        panel.close()
        panel.deleteLater()

    def test_command_is_an_argument_list(self):
        from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import pytest_command
        command = pytest_command()
        assert command[1:3] == ["-m", "pytest"]
        assert "-v" in command and "--tb=line" in command
