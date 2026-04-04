"""Tests for BaseProcessManager shared logic."""
from __future__ import annotations

import queue

from je_editor.pyside_ui.code.base_process_manager import BaseProcessManager


class TestBaseProcessManager:
    def test_init_defaults(self):
        mgr = BaseProcessManager()
        assert mgr.still_running is True
        assert mgr.process is None
        assert isinstance(mgr.run_output_queue, queue.Queue)
        assert isinstance(mgr.run_error_queue, queue.Queue)
        assert mgr.program_encoding == "utf-8"
        assert mgr.program_buffer == 1024

    def test_still_running_property(self):
        mgr = BaseProcessManager()
        mgr.still_running = False
        assert mgr.still_running is False
        mgr.still_running = True
        assert mgr.still_running is True

    def test_print_and_clear_queue(self):
        mgr = BaseProcessManager()
        mgr.run_output_queue.put("test_stdout")
        mgr.run_error_queue.put("test_stderr")
        assert not mgr.run_output_queue.empty()
        mgr.print_and_clear_queue()
        assert mgr.run_output_queue.empty()
        assert mgr.run_error_queue.empty()

    def test_exit_message_prefix_default(self):
        mgr = BaseProcessManager()
        assert mgr._exit_message_prefix() == "Process"

    def test_custom_encoding_and_buffer(self):
        mgr = BaseProcessManager(encoding="ascii", buffer_size=2048)
        assert mgr.program_encoding == "ascii"
        assert mgr.program_buffer == 2048

    def test_exit_program_without_process(self):
        """exit_program should not raise when process is None."""
        mgr = BaseProcessManager()
        mgr.exit_program()
        assert mgr.still_running is False
        assert mgr.process is None
