"""Tests for the console process adapter's lifecycle and teardown."""
from __future__ import annotations

import pytest

from je_editor.pyside_ui.main_ui.console_widget.qprocess_adapter import ConsoleProcessAdapter


@pytest.mark.usefixtures("qapp")
class TestConsoleProcessAdapter:
    """Start, stop and shutdown behaviour."""

    def test_not_running_before_start(self):
        adapter = ConsoleProcessAdapter()
        assert not adapter.is_running()

    def test_send_command_without_shell_reports_system_message(self, qtbot):
        adapter = ConsoleProcessAdapter()
        with qtbot.waitSignal(adapter.system, timeout=2000) as blocker:
            adapter.send_command("echo hi")
        assert blocker.args == ["Shell not running"]

    def test_stop_without_shell_is_a_no_op(self):
        ConsoleProcessAdapter().stop()

    def test_shutdown_without_shell_is_a_no_op(self):
        ConsoleProcessAdapter().shutdown()

    def test_shell_starts_and_shuts_down(self, qtbot):
        adapter = ConsoleProcessAdapter()
        with qtbot.waitSignal(adapter.started, timeout=5000):
            adapter.start_shell()
        assert adapter.is_running()
        adapter.shutdown()
        assert not adapter.is_running()

    def test_starting_twice_reports_already_running(self, qtbot):
        adapter = ConsoleProcessAdapter()
        with qtbot.waitSignal(adapter.started, timeout=5000):
            adapter.start_shell()
        with qtbot.waitSignal(adapter.system, timeout=2000) as blocker:
            adapter.start_shell()
        adapter.shutdown()
        assert blocker.args == ["Shell already running"]

    def test_pending_codepage_timer_dies_with_the_adapter(self, qtbot):
        """
        介面卡被刪除後，尚未觸發的 UTF-8 code page 呼叫不能再存取已刪除的 QProcess。
        A pending UTF-8 code page call must not touch the QProcess after deletion.
        """
        adapter = ConsoleProcessAdapter()
        with qtbot.waitSignal(adapter.started, timeout=5000):
            adapter.start_shell()
        adapter.shutdown()
        adapter.deleteLater()
        del adapter
        # 等到延遲呼叫早該觸發之後；若 timer 沒有綁定 context 就會在此拋出
        # Wait past the delay; an unbound timer would raise inside the event loop here
        qtbot.wait(900)

    def test_enable_utf8_codepage_is_skipped_when_not_running(self, qtbot):
        adapter = ConsoleProcessAdapter()
        with qtbot.waitSignal(adapter.system, timeout=2000) as blocker:
            adapter._enable_utf8_codepage()
            adapter.send_command("probe")
        # 沒有 shell 時不會送出 chcp，只會看到 send_command 的提示
        # With no shell the codepage command is skipped; only send_command reports
        assert blocker.args == ["Shell not running"]

    def test_kill_if_still_running_is_safe_without_shell(self):
        ConsoleProcessAdapter()._kill_if_still_running()
