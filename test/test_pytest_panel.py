"""Tests for parsing pytest output and showing it in the test panel."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.test_runner.pytest_output import (
    PytestResult,
    failure_for_result,
    parse_coverage,
    parse_failures,
    parse_results,
    parse_summary,
    parse_tracebacks,
    traceback_for_result,
    traceback_name,
)

# What --tb=short actually looks like: a banner, then one block per failure
# headed by the test's name between underscores.
TRACEBACK_OUTPUT = """
============================= test session starts =============================
test/test_alpha.py::TestAlpha::test_two FAILED                           [ 50%]
test/test_beta.py::test_three FAILED                                     [100%]

=================================== FAILURES ==================================
_________________________ TestAlpha.test_two __________________________________
test/test_alpha.py:42: in test_two
    assert total == 2
E   AssertionError: assert 1 == 2
______________________________ test_three _____________________________________
test/test_beta.py:11: in test_three
    raise ValueError("nope")
E   ValueError: nope
---------- coverage: platform win32, python 3.11.9 -----------
Name                 Stmts   Miss  Cover
----------------------------------------
je_editor/thing.py      40      4    90%
TOTAL                 1200     84    93%
========================= 2 failed in 0.42s ===================================
"""

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


class TestFencedTitles:
    """
    Banners and headings are found by scanning rather than by a regex: the
    pattern for them backtracks exponentially on a line of nothing but fence
    characters, and pytest's output is full of those.
    """

    def test_a_banner_title_is_read(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("===== FAILURES =====", "=-") == "FAILURES"

    def test_a_dashed_banner_is_read(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("--- coverage: win32 ---", "=-") == "coverage: win32"

    def test_a_heading_is_read(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("____ TestThing.test_case ____", "_") == "TestThing.test_case"

    def test_a_line_of_only_fence_characters_has_an_empty_title(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("=" * 200, "=-") == ""

    def test_an_ordinary_line_is_not_fenced(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("assert 1 == 2", "=-") is None

    def test_one_fence_character_is_not_enough(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("=title=", "=-") is None

    def test_a_blank_line_is_not_fenced(self):
        from je_editor.utils.test_runner.pytest_output import fenced_title
        assert fenced_title("   ", "=-") is None


class TestParseTracebacks:
    """The panel shows why a test failed, not only that it did."""

    def test_each_failure_gets_its_own_block(self):
        assert set(parse_tracebacks(TRACEBACK_OUTPUT)) == {"TestAlpha.test_two", "test_three"}

    def test_the_block_holds_the_assertion(self):
        blocks = parse_tracebacks(TRACEBACK_OUTPUT)
        assert "assert 1 == 2" in blocks["TestAlpha.test_two"]

    def test_a_block_stops_at_the_next_failure(self):
        blocks = parse_tracebacks(TRACEBACK_OUTPUT)
        assert "ValueError" not in blocks["TestAlpha.test_two"]

    def test_the_section_ends_at_the_next_banner(self):
        blocks = parse_tracebacks(TRACEBACK_OUTPUT)
        assert "2 failed" not in blocks["test_three"]

    def test_output_without_failures_has_no_blocks(self):
        assert parse_tracebacks(SAMPLE_OUTPUT.replace("FAILURES", "warnings summary")) == {}

    def test_empty_output_has_no_blocks(self):
        assert parse_tracebacks("") == {}


class TestTracebackNames:
    def test_a_class_based_test_joins_with_a_dot(self):
        assert traceback_name("test/test_a.py::TestThing::test_case") == "TestThing.test_case"

    def test_a_plain_test_keeps_its_name(self):
        assert traceback_name("test/test_a.py::test_case") == "test_case"

    def test_something_without_a_node_separator_is_unchanged(self):
        assert traceback_name("test_case") == "test_case"

    def test_a_result_finds_its_traceback(self):
        blocks = parse_tracebacks(TRACEBACK_OUTPUT)
        result = PytestResult(node_id="test/test_alpha.py::TestAlpha::test_two",
                              outcome="FAILED")
        assert "assert 1 == 2" in traceback_for_result(result, blocks)

    def test_a_passing_test_has_no_traceback(self):
        blocks = parse_tracebacks(TRACEBACK_OUTPUT)
        result = PytestResult(node_id="test/test_alpha.py::TestAlpha::test_one",
                              outcome="PASSED")
        assert traceback_for_result(result, blocks) == ""


class TestParseCoverage:
    def test_the_total_is_read(self):
        assert parse_coverage(TRACEBACK_OUTPUT) == "93%"

    def test_output_without_coverage_reports_nothing(self):
        assert parse_coverage(SAMPLE_OUTPUT) == ""

    def test_a_per_file_line_is_not_mistaken_for_the_total(self):
        assert parse_coverage("je_editor/thing.py      40      4    90%") == ""


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


class TestTracebackPane:
    """Seeing why a test failed without leaving the panel."""

    def test_it_starts_empty(self, panel):
        assert panel.traceback_view.toPlainText() == ""

    def test_selecting_a_failure_shows_its_traceback(self, panel):
        panel.apply_output(TRACEBACK_OUTPUT)
        panel.result_tree.setCurrentItem(panel.result_tree.topLevelItem(0))
        assert "assert 1 == 2" in panel.traceback_view.toPlainText()

    def test_each_failure_shows_its_own(self, panel):
        panel.apply_output(TRACEBACK_OUTPUT)
        panel.result_tree.setCurrentItem(panel.result_tree.topLevelItem(1))
        assert "ValueError" in panel.traceback_view.toPlainText()

    def test_a_passing_test_shows_nothing(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        rows = [panel.result_tree.topLevelItem(index)
                for index in range(panel.result_tree.topLevelItemCount())]
        passing = next(row for row in rows if row.text(0) == "PASSED")
        panel.result_tree.setCurrentItem(passing)
        assert panel.traceback_view.toPlainText() == ""

    def test_a_new_run_clears_the_previous_traceback(self, panel):
        panel.apply_output(TRACEBACK_OUTPUT)
        panel.result_tree.setCurrentItem(panel.result_tree.topLevelItem(0))
        panel.apply_output(SAMPLE_OUTPUT)
        assert panel.traceback_view.toPlainText() == ""


class TestCoverageOption:
    def test_it_is_off_by_default(self, panel):
        assert panel.coverage_check.isChecked() is False

    def test_the_command_leaves_coverage_out_by_default(self):
        from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import pytest_command
        assert not any(argument.startswith("--cov") for argument in pytest_command())

    def test_asking_for_coverage_adds_the_flags(self):
        from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import pytest_command
        command = pytest_command(with_coverage=True)
        assert "--cov=." in command and "--cov-report=term" in command

    def test_the_total_reaches_the_status_label(self, panel):
        panel.apply_output(TRACEBACK_OUTPUT)
        assert "93%" in panel.status_label.text()

    def test_a_run_without_coverage_leaves_the_summary_alone(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert "%" not in panel.status_label.text()


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
        assert "-v" in command and "--tb=short" in command

    def test_command_can_target_specific_tests(self):
        from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import pytest_command
        command = pytest_command(["test/test_a.py::test_one"])
        assert command[-1] == "test/test_a.py::test_one"


class TestTargetedRuns:
    def test_failed_node_ids_are_collected(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert panel.failed_node_ids() == ["test/test_alpha.py::TestAlpha::test_two"]

    def test_rerunning_failures_without_any_does_nothing(self, panel):
        panel.apply_output("collected 0 items\n")
        assert panel.start_failure_run() is False

    def test_running_the_selection_without_one_does_nothing(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.result_tree.clearSelection()
        assert panel.start_selected_run() is False

    def test_selected_node_ids_follow_the_tree(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.result_tree.topLevelItem(0).setSelected(True)
        assert panel.selected_node_ids() == ["test/test_alpha.py::TestAlpha::test_two"]


class TestFiltering:
    def test_an_empty_filter_shows_everything(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        assert len(panel.visible_results()) == 3

    def test_filtering_narrows_the_list(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.filter_edit.setText("beta")
        assert [result.file_path for result in panel.visible_results()] == ["test/test_beta.py"]
        assert panel.result_tree.topLevelItemCount() == 1

    def test_filtering_is_case_insensitive(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.filter_edit.setText("ALPHA")
        assert len(panel.visible_results()) == 2

    def test_a_filter_matching_nothing_empties_the_list(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.filter_edit.setText("nothing matches this")
        assert panel.visible_results() == []

    def test_failures_still_come_first_when_filtered(self, panel):
        panel.apply_output(SAMPLE_OUTPUT)
        panel.filter_edit.setText("alpha")
        assert panel.visible_results()[0].failed is True
