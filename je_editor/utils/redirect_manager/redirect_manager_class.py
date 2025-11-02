import logging
import queue
import sys

from je_editor.utils.logging.loggin_instance import jeditor_logger


class RedirectStdOut(logging.Handler):
    """
    功能說明 (Function Description):
    - 將標準輸出 (stdout) 重導向到 queue
    - Redirect standard output (stdout) to a queue
    """

    def __init__(self):
        super().__init__()

    def write(self, content_to_write) -> None:
        # 將輸出內容放入 RedirectManager 的 stdout queue
        # Put output content into RedirectManager's stdout queue
        redirect_manager_instance.std_out_queue.put(content_to_write)

    def emit(self, record: logging.LogRecord) -> None:
        # 將 logging 訊息格式化後放入 stdout queue
        # Put formatted logging record into stdout queue
        redirect_manager_instance.std_out_queue.put(self.format(record))


class RedirectStdErr(logging.Handler):
    """
    功能說明 (Function Description):
    - 將標準錯誤輸出 (stderr) 重導向到 queue
    - Redirect standard error (stderr) to a queue
    """

    def __init__(self):
        super().__init__()

    def write(self, content_to_write) -> None:
        # 將錯誤輸出內容放入 RedirectManager 的 stderr queue
        # Put error output content into RedirectManager's stderr queue
        redirect_manager_instance.std_err_queue.put(content_to_write)

    def emit(self, record: logging.LogRecord) -> None:
        # 將 logging 訊息格式化後放入 stderr queue
        # Put formatted logging record into stderr queue
        redirect_manager_instance.std_err_queue.put(self.format(record))


class RedirectManager(object):
    """
    功能說明 (Function Description):
    - 管理 stdout 與 stderr 的重導向
    - 提供 set_redirect 與 restore_std 方法
    - Manage redirection of stdout and stderr
    - Provides set_redirect and restore_std methods
    """

    def __init__(self):
        jeditor_logger.info("Init RedirectManager")
        # 建立 stdout 與 stderr 的 queue
        # Create queues for stdout and stderr
        self.std_err_queue = queue.Queue()
        self.std_out_queue = queue.Queue()

    @staticmethod
    def set_redirect() -> None:
        """
        啟用重導向
        Redirect stdout and stderr to queues
        """
        jeditor_logger.info("RedirectManager set_redirect")
        redirect_out = RedirectStdOut()
        redirect_err = RedirectStdErr()

        # 將 sys.stdout / sys.stderr 指向自訂 handler
        # Redirect sys.stdout / sys.stderr to custom handlers
        sys.stdout = redirect_out
        sys.stderr = redirect_err

        # 建立一個 logger 並綁定 stderr handler
        # Create a logger and bind stderr handler
        default_logger = logging.getLogger("JEditor_RedirectManager")
        default_logger.addHandler(redirect_err)

        # 過濾掉不需要重導向的 logger
        # Skip specific loggers from being redirected
        skip_logger_list = [
            "JEditor", "FrontEngine",
            "AutomationIDE", "TestPioneer",
            "langchain", "langchain_core", "langchain_openai"
        ]
        for name in logging.root.manager.loggerDict.keys():
            if name in skip_logger_list:
                continue
            else:
                logging.getLogger(name).addHandler(redirect_err)

    @staticmethod
    def restore_std() -> None:
        """
        重設 stdout 與 stderr
        Restore stdout and stderr to default
        """
        jeditor_logger.info("RedirectManager restore_std")
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


# 建立全域 RedirectManager 實例
# Create a global instance of RedirectManager
redirect_manager_instance = RedirectManager()
