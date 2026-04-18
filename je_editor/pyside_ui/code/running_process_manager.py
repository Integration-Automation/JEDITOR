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

    def __init__(self) -> None:
        # 初始化，建立一個空的實例清單
        # Initialize with an empty instance list
        jeditor_logger.info("Init RunInstanceManager")
        self.instance_list: List[Union[ExecManager, ShellManager]] = list()

    def remove_instance(self, instance: Union[ExecManager, ShellManager]) -> None:
        """
        從清單中移除已結束的實例
        Remove a finished instance from the list
        """
        try:
            self.instance_list.remove(instance)
        except ValueError:
            pass

    def close_all_instance(self) -> None:
        """
        關閉所有執行中的實例，透過各自的 exit_program 正確清理 timer、thread 與 process
        Close all running instances via their own exit_program for proper cleanup
        """
        jeditor_logger.info("RunInstanceManager close_all_instance")
        for manager in list(self.instance_list):
            # 停止 timer / Stop timer
            if manager.timer is not None:
                manager.timer.stop()
            # 透過 manager 自身清理 (停止 thread、清空 queue、終止 process)
            # Use manager's own cleanup (stop threads, clear queues, terminate process)
            manager.exit_program()
            # 清理 main_window 的執行狀態
            # Reset execution states in main_window
            if manager.main_window is not None:
                manager.main_window.exec_program = None
                manager.main_window.exec_shell = None
                manager.main_window.exec_python_debugger = None
        self.instance_list.clear()


# 建立全域唯一的 RunInstanceManager 實例
# Create a global singleton instance of RunInstanceManager
run_instance_manager = RunInstanceManager()
