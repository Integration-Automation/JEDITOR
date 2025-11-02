from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
    from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager

from typing import List, Union


class RunInstanceManager(object):
    """
    管理程式執行與 Shell 執行的實例
    Manager for ExecManager and ShellManager instances
    """

    def __init__(self):
        # 初始化，建立一個空的實例清單
        # Initialize with an empty instance list
        jeditor_logger.info("Init RunInstanceManager")
        self.instance_list: List[Union[ExecManager, ShellManager]] = list()

    def close_all_instance(self):
        """
        關閉所有執行中的實例，並清理 main_window 的執行狀態
        Close all running instances and reset main_window execution states
        """
        jeditor_logger.info("RunInstanceManager close_all_instance")
        for manager in self.instance_list:
            # 若子程序仍存在，則終止
            # Terminate process if still running
            if manager.process is not None:
                manager.process.terminate()
            # 清理 main_window 的執行狀態
            # Reset execution states in main_window
            manager.main_window.exec_program = None
            manager.main_window.exec_shell = None
            manager.main_window.exec_python_debugger = None


# 建立全域唯一的 RunInstanceManager 實例
# Create a global singleton instance of RunInstanceManager
run_instance_manager = RunInstanceManager()
