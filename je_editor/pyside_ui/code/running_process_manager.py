from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
    from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager

from typing import List, Union


class RunInstanceManager(object):

    def __init__(self):
        jeditor_logger.info("Init RunInstanceManager")
        self.instance_list: List[Union[ExecManager, ShellManager]] = list()

    def close_all_instance(self):
        jeditor_logger.info("RunInstanceManager close_all_instance")
        for manager in self.instance_list:
            if manager.process is not None:
                manager.process.terminate()
            manager.main_window.exec_program = None
            manager.main_window.exec_shell = None
            manager.main_window.exec_python_debugger = None


run_instance_manager = RunInstanceManager()
