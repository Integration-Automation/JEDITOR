"""Tests for the debug panel, its controller, breakpoint conditions and the debugging actions."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget

from je_editor.adapters.debug.debugpy_adapter import debugpy_available
from je_editor.adapters.default_services import build_default_services
from je_editor.core.debug.debug_session import (
    Breakpoint, DebugAttachRequest, DebugLaunchRequest, DebugReply, DebugSession, DebugState,
    DebugThread, EvaluateResult, ExceptionInfo, OutputEvent, Scope, StackFrame, StepKind,
    StopEvent, Variable
)
from je_editor.core.events.event_hook import EventHook
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.uri.resource_uri import to_uri
from je_editor.pyside_ui.main_ui.debug_panel import debug_actions
from je_editor.pyside_ui.main_ui.debug_panel.debug_actions import (
    attach_to_process, clear_execution_lines, collect_breakpoints, controller_of,
    edit_breakpoint_condition, show_execution_line, start_debugging
)
from je_editor.pyside_ui.main_ui.debug_panel.debug_controller import DebugController
from je_editor.pyside_ui.main_ui.debug_panel.debug_panel_widget import DebugPanelWidget
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu import build_debug_menu
from je_editor.utils.debugger.attach_address import parse_address

pytestmark = pytest.mark.usefixtures("qapp")
TIMEOUT_MS = 60_000
LOCALS, GLOBALS, ITEMS = 5, 6, 9


class FakeSession:
    """A debug session that answers from a script and notes what it was told."""

    def __init__(self) -> None:
        self.state_changed = EventHook("state")
        self.stopped = EventHook("stopped")
        self.output = EventHook("output")
        self.breakpoints_reported = EventHook("breakpoints")
        self._state = DebugState.IDLE
        self.calls: list[tuple] = []
        self.breakpoints: dict[str, list[Breakpoint]] = {}
        self.source = ""

    def state(self) -> DebugState:
        return self._state

    def move_to(self, state: DebugState) -> None:
        self._state = state
        self.state_changed.emit(state)

    def stop_at(self, reason: str = "breakpoint", thread_id: int = 7) -> None:
        self._state = DebugState.PAUSED
        self.state_changed.emit(DebugState.PAUSED)
        self.stopped.emit(StopEvent(reason, thread_id))

    def launch(self, request: DebugLaunchRequest) -> bool:
        self.calls.append(("launch", request))
        self.move_to(DebugState.RUNNING)
        return True

    def attach(self, request: DebugAttachRequest) -> bool:
        self.calls.append(("attach", request))
        self.move_to(DebugState.RUNNING)
        return True

    def set_breakpoints(self, uri: str, breakpoints) -> None:
        self.breakpoints[uri] = list(breakpoints)

    def resume(self, thread_id: int = 0) -> None:
        self.calls.append(("resume",))
        self.move_to(DebugState.RUNNING)

    def pause(self, thread_id: int = 0) -> None:
        self.calls.append(("pause",))

    def step(self, kind: StepKind, thread_id: int = 0) -> None:
        self.calls.append(("step", kind))

    def terminate(self) -> None:
        self.calls.append(("terminate",))
        self.move_to(DebugState.TERMINATED)

    def threads(self, on_reply) -> None:
        on_reply(DebugReply((DebugThread(7, "MainThread"), DebugThread(8, ""))))

    def stack_trace(self, thread_id: int, on_reply) -> None:
        self.calls.append(("stack", thread_id))
        on_reply(DebugReply((StackFrame(2, "add", self.source, 3), StackFrame(1, "<module>", "", 1))))

    def scopes(self, frame_id: int, on_reply) -> None:
        on_reply(DebugReply((Scope("Locals", LOCALS), Scope("Globals", GLOBALS, True))))

    def variables(self, reference: int, on_reply) -> None:
        self.calls.append(("variables", reference))
        found = {
            LOCALS: (Variable("first", "1", "int"), Variable("items", "[1, 2]", "list", ITEMS)),
            ITEMS: (Variable("0", "1", "int"), Variable("1", "2", "int")),
        }
        on_reply(DebugReply(found.get(reference, ())))

    def evaluate(self, expression: str, frame_id: int, on_reply) -> None:
        self.calls.append(("evaluate", expression, frame_id))
        if expression == "boom":
            on_reply(DebugReply(None, "NameError: boom"))
        else:
            on_reply(DebugReply(EvaluateResult("42", "int")))

    def exception_info(self, thread_id: int, on_reply) -> None:
        on_reply(DebugReply(ExceptionInfo("ZeroDivisionError", "division by zero", "unhandled", "Traceback")))


@pytest.fixture()
def fake():
    return FakeSession()


@pytest.fixture()
def services(fake):
    built = EditorServices()
    built.debug_adapters.register("debugpy", lambda: fake)
    yield built
    built.shutdown()


@pytest.fixture()
def controller(services):
    built = DebugController(services)
    yield built
    built.deleteLater()


@pytest.fixture()
def panel(controller, qtbot):
    built = DebugPanelWidget(controller)
    qtbot.addWidget(built)
    return built


@pytest.fixture()
def paused(controller, fake, panel):
    """A panel showing a program stopped at a breakpoint."""
    controller.launch(DebugLaunchRequest("main.py"), {})
    fake.stop_at()
    return panel


class TestTheAddressToAttachTo:
    @pytest.mark.parametrize("text, expected", [
        ("127.0.0.1:5678", ("127.0.0.1", 5678)), (" build-box:9000 ", ("build-box", 9000)),
        ("5678", ("127.0.0.1", 5678)), ("[::1]:5678", ("[::1]", 5678)),
    ])
    def test_a_usable_address(self, text, expected):
        assert parse_address(text) == expected

    @pytest.mark.parametrize("text", ["", None, "host", "host:", ":5678", "host:0", "host:70000",
                                      "host:12ab", "host:-1", "host:５６７８"])
    def test_an_unusable_address(self, text):
        assert parse_address(text) is None


class TestTheController:
    def test_the_fake_is_a_debug_session(self, fake):
        assert isinstance(fake, DebugSession)

    def test_it_is_available_only_with_its_adapter_registered(self, controller):
        assert controller.available() is True
        assert DebugController(EditorServices()).available() is False

    def test_before_any_debugging_it_is_idle(self, controller):
        assert (controller.state(), controller.is_active()) == (DebugState.IDLE, False)

    def test_launching_hands_the_breakpoints_over_first(self, controller, fake, tmp_path):
        uri = to_uri(tmp_path / "main.py")
        request = DebugLaunchRequest("main.py")
        assert controller.launch(request, {uri: [Breakpoint(uri, 3)]}) is True
        assert (fake.breakpoints, fake.calls) == ({uri: [Breakpoint(uri, 3)]}, [("launch", request)])
        assert controller.is_active() is True

    def test_a_second_launch_while_active_is_refused(self, controller):
        controller.launch(DebugLaunchRequest("main.py"), {})
        assert controller.launch(DebugLaunchRequest("other.py"), {}) is False

    def test_without_an_adapter_nothing_is_launched(self):
        assert DebugController(EditorServices()).launch(DebugLaunchRequest("main.py"), {}) is False

    def test_attaching(self, controller, fake):
        request = DebugAttachRequest(5678)
        assert controller.attach(request, {}) is True
        assert fake.calls == [("attach", request)]

    def test_the_sessions_events_become_signals(self, controller, fake, qtbot):
        controller.launch(DebugLaunchRequest("main.py"), {})
        with qtbot.waitSignal(controller.stopped, timeout=TIMEOUT_MS) as stopped:
            fake.stop_at("step", 4)
        assert stopped.args[0] == StopEvent("step", 4)
        with qtbot.waitSignal(controller.output, timeout=TIMEOUT_MS) as written:
            fake.output.emit(OutputEvent("stdout", "hello"))
        assert written.args == ["stdout", "hello"]

    def test_output_meant_for_tools_is_not_shown(self, controller, fake):
        shown: list = []
        controller.output.connect(lambda category, text: shown.append(text))
        controller.launch(DebugLaunchRequest("main.py"), {})
        fake.output.emit(OutputEvent("telemetry", "debugpy"))
        fake.output.emit(OutputEvent("stderr", "oops"))
        assert shown == ["oops"]

    def test_stepping_needs_a_paused_program(self, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        assert controller.step(StepKind.OVER) is False
        fake.stop_at()
        assert controller.step(StepKind.INTO) is True
        assert fake.calls[-1] == ("step", StepKind.INTO)

    def test_resume_and_pause_follow_the_state(self, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        controller.resume()
        controller.pause()
        fake.stop_at()
        controller.pause()
        controller.resume()
        assert [call[0] for call in fake.calls] == ["launch", "pause", "resume"]

    def test_breakpoints_are_passed_on_only_while_debugging(self, controller, fake, tmp_path):
        uri = to_uri(tmp_path / "main.py")
        controller.set_breakpoints(uri, [Breakpoint(uri, 1)])
        assert fake.breakpoints == {}
        controller.launch(DebugLaunchRequest("main.py"), {})
        controller.set_breakpoints(uri, [Breakpoint(uri, 2)])
        assert fake.breakpoints == {uri: [Breakpoint(uri, 2)]}

    def test_stopping_ends_the_session_and_allows_another(self, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        controller.stop()
        assert (controller.state(), controller.is_active()) == (DebugState.TERMINATED, False)
        assert controller.launch(DebugLaunchRequest("main.py"), {}) is True

    def test_queries_before_any_session_do_nothing(self, controller):
        controller.request_threads()
        controller.request_stack(1)
        controller.request_scopes(1)
        controller.request_variables(1)
        controller.evaluate("x", 0)
        controller.request_exception(1)
        controller.stop()
        assert controller.state() is DebugState.IDLE


class TestThePanel:
    def test_before_debugging_only_nothing_can_be_pressed(self, panel):
        buttons = (panel.continue_button, panel.pause_button, panel.step_over_button,
                   panel.step_into_button, panel.step_out_button, panel.stop_button)
        assert [button.isEnabled() for button in buttons] == [False] * 6
        assert panel.status_label.text() == "Not running"

    def test_while_running_it_can_be_paused_or_stopped(self, controller, panel):
        controller.launch(DebugLaunchRequest("main.py"), {})
        assert (panel.pause_button.isEnabled(), panel.stop_button.isEnabled(),
                panel.continue_button.isEnabled(), panel.evaluate_input.isEnabled()) == (
            True, True, False, False)
        assert panel.status_label.text() == "Running"

    def test_a_stop_fills_the_threads_and_the_stack(self, paused, fake):
        assert paused.status_label.text() == "Paused: breakpoint"
        assert [paused.thread_combobox.itemText(index) for index in range(2)] == ["MainThread", "8"]
        assert paused.thread_combobox.currentData() == 7
        assert [paused.stack_list.item(row).text() for row in range(2)] == ["add", "<module>"]
        assert paused.selected_frame() == StackFrame(2, "add", "", 3)
        assert paused.step_over_button.isEnabled() and not paused.pause_button.isEnabled()

    def test_a_frame_with_a_source_shows_its_file_and_line(self, controller, fake, panel, tmp_path):
        fake.source = to_uri(tmp_path / "main.py")
        chosen: list = []
        panel.frame_selected.connect(lambda path, line: chosen.append((path, line)))
        controller.launch(DebugLaunchRequest("main.py"), {})
        fake.stop_at()
        assert panel.stack_list.item(0).text() == "add  main.py:3"
        assert [(path.replace("\\", "/").rsplit("/", 1)[-1], line) for path, line in chosen] == [
            ("main.py", 3)]

    def test_cheap_scopes_are_opened_and_expensive_ones_wait(self, paused, fake):
        top = [paused.variable_tree.topLevelItem(index) for index in range(2)]
        assert [item.text(0) for item in top] == ["Locals", "Globals"]
        assert [top[0].child(row).text(0) for row in range(top[0].childCount())] == ["first", "items"]
        assert (top[0].child(0).text(1), top[0].child(0).text(2)) == ("1", "int")
        assert top[1].childCount() == 0
        assert ("variables", GLOBALS) not in fake.calls

    def test_a_variable_with_children_is_fetched_when_opened(self, paused, fake):
        items = paused.variable_tree.topLevelItem(0).child(1)
        assert items.childCount() == 0
        items.setExpanded(True)
        assert [items.child(row).text(1) for row in range(items.childCount())] == ["1", "2"]
        items.setExpanded(False)
        items.setExpanded(True)
        assert fake.calls.count(("variables", ITEMS)) == 1

    def test_choosing_another_thread_asks_for_its_stack(self, paused, fake):
        paused.thread_combobox.setCurrentIndex(1)
        paused._on_thread_chosen(1)
        assert ("stack", 8) in fake.calls

    def test_evaluating_in_the_selected_frame(self, paused, fake):
        paused.evaluate_input.setText("first + 41")
        paused._evaluate()
        assert fake.calls[-1] == ("evaluate", "first + 41", 2)
        assert paused.output_view.toPlainText().endswith(">>> first + 41\n42\n")
        assert paused.evaluate_input.text() == ""

    def test_a_failed_evaluation_shows_why(self, paused):
        paused.evaluate_input.setText("boom")
        paused._evaluate()
        assert "NameError: boom" in paused.output_view.toPlainText()

    def test_an_empty_expression_is_not_sent(self, paused, fake):
        before = len(fake.calls)
        paused.evaluate_input.setText("   ")
        paused._evaluate()
        assert len(fake.calls) == before

    def test_stopping_on_an_exception_shows_it(self, controller, fake, panel):
        controller.launch(DebugLaunchRequest("main.py"), {})
        fake.stop_at("exception")
        assert "ZeroDivisionError: division by zero\nTraceback" in panel.output_view.toPlainText()

    def test_program_output_is_appended(self, controller, fake, panel):
        controller.launch(DebugLaunchRequest("main.py"), {})
        fake.output.emit(OutputEvent("stdout", "one\n"))
        fake.output.emit(OutputEvent("stdout", "two\n"))
        assert panel.output_view.toPlainText() == "one\ntwo\n"

    def test_the_buttons_drive_the_session(self, paused, fake):
        paused.step_over_button.click()
        paused.step_into_button.click()
        paused.step_out_button.click()
        paused.continue_button.click()
        paused.stop_button.click()
        assert fake.calls[-5:] == [("step", StepKind.OVER), ("step", StepKind.INTO),
                                   ("step", StepKind.OUT), ("resume",), ("terminate",)]

    def test_resuming_empties_the_stack_and_the_variables(self, paused, controller):
        controller.resume()
        assert (paused.stack_list.count(), paused.variable_tree.topLevelItemCount()) == (0, 0)

    def test_emptying_the_stack_asks_the_adapter_nothing_and_selects_no_frame(
            self, paused, controller, fake):
        # Qt walks the current item down the list while clearing it.
        chosen: list = []
        paused.frame_selected.connect(lambda path, line: chosen.append(line))
        before = len(fake.calls)
        controller.resume()
        assert (fake.calls[before:], chosen) == ([("resume",)], [])

    def test_the_end_is_shown(self, paused, controller):
        controller.stop()
        assert paused.status_label.text() == "Ended"
        assert paused.stop_button.isEnabled() is False

    def test_the_texts_follow_the_language(self, panel):
        from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
        previous = language_wrapper.language
        try:
            language_wrapper.reset_language("Traditional_Chinese")
            panel.retranslate()
            assert (panel.continue_button.text(), panel.status_label.text()) == ("繼續", "尚未執行")
        finally:
            language_wrapper.reset_language(previous)
            panel.retranslate()


@pytest.fixture()
def window(services, controller, tmp_path):
    """A stand-in main window with one real editor tab on a saved file."""
    stand_in = SimpleNamespace(services=services, debug_controller=controller, working_dir=None,
                               python_compiler=None, tab_widget=QTabWidget(), encoding="utf-8")
    stand_in.go_to_new_tab = MagicMock()
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as venv:
        venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        tab = EditorWidget(stand_in)
    stand_in.tab_widget.addTab(tab, "main.py")
    path = tmp_path / "main.py"
    path.write_text("first = 1\nsecond = 2\nthird = 3\n", encoding="utf-8")
    tab.current_file = str(path)
    tab.code_edit.current_file = str(path)
    tab.code_edit.setPlainText(path.read_text(encoding="utf-8"))
    stand_in.tab = tab
    stand_in.edit = tab.code_edit
    stand_in.uri = to_uri(path)
    yield stand_in
    tab.close()
    tab.deleteLater()
    stand_in.tab_widget.deleteLater()


class TestBreakpointsInTheEditor:
    def test_a_breakpoint_starts_without_a_condition(self, window):
        manager = window.edit.breakpoint_manager
        manager.toggle(1)
        assert (manager.breakpoints(), manager.condition(1), manager.condition(0)) == ([(1, "")], "", "")

    def test_a_condition_can_be_set_and_changed(self, window):
        manager = window.edit.breakpoint_manager
        manager.toggle(1)
        manager.set_condition(1, "first > 0")
        manager.set_condition(1, "first > 1")
        assert manager.breakpoints() == [(1, "first > 1")]

    def test_setting_a_condition_on_a_bare_line_adds_the_breakpoint(self, window):
        manager = window.edit.breakpoint_manager
        assert manager.set_condition(2, "third") is True
        assert (manager.lines(), manager.condition(2)) == ([2], "third")

    def test_a_line_that_does_not_exist_gets_nothing(self, window):
        assert window.edit.breakpoint_manager.set_condition(99, "x") is False

    def test_removing_a_breakpoint_removes_its_condition(self, window):
        manager = window.edit.breakpoint_manager
        manager.set_condition(0, "a")
        manager.set_condition(2, "c")
        manager.toggle(0)
        assert manager.breakpoints() == [(2, "c")]
        manager.clear()
        assert manager.breakpoints() == []

    def test_the_condition_follows_its_line_through_an_edit(self, window):
        window.edit.breakpoint_manager.set_condition(1, "second")
        cursor = window.edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.insertText("# added\n")
        assert window.edit.breakpoint_manager.breakpoints() == [(2, "second")]

    def test_the_editor_gives_them_as_one_based_breakpoints(self, window):
        window.edit.breakpoint_manager.set_condition(1, "second")
        assert window.edit.debug_breakpoints() == [Breakpoint(window.uri, 2, "second")]

    def test_a_tab_without_a_file_has_none_to_give(self, window):
        window.edit.breakpoint_manager.toggle(0)
        window.edit.current_file = None
        assert window.edit.debug_breakpoints() == []

    def test_toggling_while_debugging_reaches_the_session(self, window, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        window.edit.toggle_breakpoint()
        assert fake.breakpoints == {window.uri: [Breakpoint(window.uri, 1)]}

    def test_toggling_when_not_debugging_stays_in_the_editor(self, window, fake):
        window.edit.toggle_breakpoint()
        assert (fake.breakpoints, window.edit.sync_debug_breakpoints()) == ({}, False)


class TestTheExecutionLine:
    def test_marking_and_unmarking(self, window):
        assert window.edit.set_execution_line(2) is True
        assert (window.edit.execution_line(), window.edit.textCursor().blockNumber()) == (2, 1)
        assert window.edit.set_execution_line(None) is False
        assert window.edit.execution_line() is None

    def test_a_line_that_does_not_exist_marks_nothing(self, window):
        assert window.edit.set_execution_line(99) is False
        assert window.edit.execution_line() is None

    def test_the_mark_is_painted_as_a_full_line(self, window):
        window.edit.set_execution_line(2)
        blocks = [selection.cursor.blockNumber() for selection in window.edit.extraSelections()]
        assert blocks.count(1) >= 2  # the current line and the execution line

    def test_showing_a_frame_opens_its_file_and_marks_the_line(self, window):
        assert show_execution_line(window, window.tab.current_file, 3) is True
        window.go_to_new_tab.assert_called_once_with(window.tab.current_file)
        assert window.edit.execution_line() == 3

    def test_a_frame_without_a_source_marks_nothing(self, window):
        window.edit.set_execution_line(2)
        assert show_execution_line(window, "", 1) is False
        assert window.edit.execution_line() is None

    def test_clearing_reaches_every_editor(self, window):
        window.edit.set_execution_line(2)
        clear_execution_lines(window)
        assert window.edit.execution_line() is None


class TestSteppingFromTheEditor:
    @pytest.mark.parametrize("action, expected", [
        ("over", ("step", StepKind.OVER)), ("into", ("step", StepKind.INTO)),
        ("out", ("step", StepKind.OUT)), ("continue", ("resume",)), ("quit", ("terminate",)),
    ])
    def test_a_shortcut_goes_to_the_session_while_debugging(self, window, controller, fake,
                                                              action, expected):
        controller.launch(DebugLaunchRequest("main.py"), {})
        fake.stop_at()
        assert window.edit.send_debugger_command(action) is True
        assert fake.calls[-1] == expected

    def test_an_unknown_action_is_not_sent(self, window, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        assert window.edit.send_debugger_command("dance") is False

    def test_without_a_session_it_falls_to_the_pdb_console(self, window):
        with patch.object(window.edit, "_write_debugger_line", return_value=True) as written:
            assert window.edit.send_debugger_command("over") is True
        written.assert_called_once_with("next")


class TestTheActions:
    def test_a_window_without_a_controller_has_none(self):
        assert controller_of(SimpleNamespace()) is None
        assert controller_of(SimpleNamespace(debug_controller=MagicMock())) is None

    def test_a_controller_without_its_adapter_does_not_count(self):
        assert controller_of(SimpleNamespace(debug_controller=DebugController(EditorServices()))) is None

    def test_breakpoints_are_collected_from_every_open_file(self, window):
        window.edit.breakpoint_manager.set_condition(0, "first")
        assert collect_breakpoints(window) == {window.uri: [Breakpoint(window.uri, 1, "first")]}
        assert collect_breakpoints(SimpleNamespace()) == {}

    def test_starting_launches_the_file_with_its_breakpoints(self, window, fake):
        window.edit.breakpoint_manager.toggle(2)
        window.python_compiler = "C:/env/python.exe"
        with patch.object(debug_actions, "show_debug_panel") as shown:
            assert start_debugging(window, window.tab.current_file) is True
        launch = fake.calls[0][1]
        assert (launch.program, launch.interpreter) == (window.tab.current_file, "C:/env/python.exe")
        assert fake.breakpoints == {window.uri: [Breakpoint(window.uri, 3)]}
        shown.assert_called_once_with(window)

    def test_starting_is_refused_without_a_file_or_while_debugging(self, window, controller):
        with patch.object(debug_actions, "show_debug_panel"):
            assert start_debugging(window, None) is False
            assert start_debugging(window, window.tab.current_file) is True
            assert start_debugging(window, window.tab.current_file) is False

    def test_attaching_to_an_address(self, window, fake):
        with patch.object(debug_actions, "show_debug_panel"):
            assert attach_to_process(window, "10.0.0.2:5678") is True
        assert fake.calls == [("attach", DebugAttachRequest(5678, "10.0.0.2"))]

    def test_an_address_that_makes_no_sense_is_explained(self, window, controller, fake):
        told: list = []
        controller.output.connect(lambda _category, text: told.append(text))
        with patch.object(debug_actions, "show_debug_panel"):
            assert attach_to_process(window, "nonsense") is False
        assert (fake.calls, "host:port" in told[0]) == ([], True)

    def test_cancelling_the_address_dialog_attaches_nothing(self, window, fake):
        with patch.object(debug_actions.QInputDialog, "getText", return_value=("1.2.3.4:5", False)):
            assert attach_to_process(window) is False
        assert fake.calls == []

    def test_a_condition_is_set_on_the_carets_line(self, window):
        cursor = window.edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Down)
        window.edit.setTextCursor(cursor)
        assert edit_breakpoint_condition(window, " second > 1 ") is True
        assert window.edit.breakpoint_manager.breakpoints() == [(1, "second > 1")]

    def test_the_condition_dialog_starts_from_the_current_condition(self, window):
        window.edit.breakpoint_manager.set_condition(0, "old")
        with patch.object(debug_actions.QInputDialog, "getText", return_value=("new", True)) as asked:
            assert edit_breakpoint_condition(window) is True
        assert asked.call_args.kwargs["text"] == "old"
        assert "line 1" in asked.call_args.args[2]
        assert window.edit.breakpoint_manager.condition(0) == "new"

    def test_cancelling_the_condition_dialog_changes_nothing(self, window):
        with patch.object(debug_actions.QInputDialog, "getText", return_value=("x", False)):
            assert edit_breakpoint_condition(window) is False
        assert window.edit.breakpoint_manager.breakpoints() == []

    def test_a_condition_set_while_debugging_reaches_the_session(self, window, controller, fake):
        controller.launch(DebugLaunchRequest("main.py"), {})
        edit_breakpoint_condition(window, "first")
        assert fake.breakpoints == {window.uri: [Breakpoint(window.uri, 1, "first")]}

    def test_no_editor_tab_means_no_condition(self):
        assert edit_breakpoint_condition(SimpleNamespace(tab_widget=QTabWidget()), "x") is False


class TestRunDebuggerFromTheMenu:
    def test_the_adapter_is_used_when_there_is_one(self, window, fake):
        with patch.object(build_debug_menu, "choose_file_get_save_file_path", return_value=True), \
                patch.object(debug_actions, "show_debug_panel"):
            build_debug_menu.run_debugger(window)
        assert fake.calls[0][0] == "launch"
        assert window.tab.exec_python_debugger is None

    def test_an_unsaved_file_starts_nothing(self, window, fake):
        with patch.object(build_debug_menu, "choose_file_get_save_file_path", return_value=False):
            build_debug_menu.run_debugger(window)
        assert fake.calls == []

    def test_a_second_run_while_debugging_is_refused_with_a_message(self, window, controller):
        controller.launch(DebugLaunchRequest("main.py"), {})
        with patch.object(build_debug_menu, "please_close_current_running_messagebox") as told:
            build_debug_menu.run_debugger(window)
        told.assert_called_once_with(window)

    def test_without_an_adapter_the_pdb_console_is_started(self, window):
        window.debug_controller = DebugController(EditorServices())
        with patch.object(build_debug_menu, "choose_file_get_save_file_path", return_value=True), \
                patch.object(build_debug_menu, "ExecManager") as manager, \
                patch.object(build_debug_menu, "ProcessInput"):
            build_debug_menu.run_debugger(window)
        manager.return_value.exec_code.assert_called_once_with(
            window.tab.current_file, exec_prefix=["-m", "pdb"])


@pytest.mark.skipif(not debugpy_available(), reason="debugpy is not installed")
class TestAgainstTheRealAdapter:
    def test_a_program_is_debugged_from_the_panel(self, qtbot, tmp_path):
        program = tmp_path / "program.py"
        program.write_text("def add(first, second):\n    total = first + second\n    return total\n"
                           "\n\nprint('sum', add(1, 2))\n", encoding="utf-8")
        services = build_default_services(settings_directory=tmp_path)
        controller = DebugController(services)
        panel = DebugPanelWidget(controller)
        qtbot.addWidget(panel)
        uri = to_uri(program)
        try:
            assert controller.launch(DebugLaunchRequest(str(program)), {uri: [Breakpoint(uri, 2)]})
            qtbot.waitUntil(lambda: panel.stack_list.count() > 0, timeout=TIMEOUT_MS)
            assert panel.stack_list.item(0).text() == "add  program.py:2"
            qtbot.waitUntil(lambda: panel.variable_tree.topLevelItemCount() > 0
                            and panel.variable_tree.topLevelItem(0).childCount() == 2,
                            timeout=TIMEOUT_MS)
            scope = panel.variable_tree.topLevelItem(0)
            assert {scope.child(row).text(0): scope.child(row).text(1) for row in range(2)} == {
                "first": "1", "second": "2"}
            panel.continue_button.click()
            qtbot.waitUntil(lambda: controller.state() is DebugState.TERMINATED, timeout=TIMEOUT_MS)
            QApplication.processEvents()
            assert "sum 3" in panel.output_view.toPlainText()
        finally:
            controller.stop()
            services.shutdown()
