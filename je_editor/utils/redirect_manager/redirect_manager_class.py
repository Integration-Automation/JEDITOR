import logging
import queue
import sys


class RedirectStdOut(logging.Handler):

    # redirect logging std output to queue

    def __init__(self):
        super().__init__()

    def write(self, content_to_write) -> None:
        redirect_manager_instance.std_out_queue.put(content_to_write)

    def emit(self, record: logging.LogRecord) -> None:
        redirect_manager_instance.std_out_queue.put(self.format(record))


class RedirectStdErr(logging.Handler):

    # redirect logging stderr output to queue

    def __init__(self):
        super().__init__()

    def write(self, content_to_write) -> None:
        redirect_manager_instance.std_err_queue.put(content_to_write)

    def emit(self, record: logging.LogRecord) -> None:
        redirect_manager_instance.std_err_queue.put(self.format(record))


class RedirectManager(object):
    # Redirect all output to queue
    def __init__(self):
        self.std_err_queue = queue.Queue()
        self.std_out_queue = queue.Queue()

    @staticmethod
    def set_redirect() -> None:
        """
        :return: None
        """
        redirect_out = RedirectStdOut()
        redirect_err = RedirectStdErr()
        sys.stdout = redirect_out
        sys.stderr = redirect_err
        default_logger = logging.getLogger()
        default_logger.addHandler(redirect_err)
        for name in logging.root.manager.loggerDict.keys():
            logging.getLogger(name).addHandler(redirect_err)

    @staticmethod
    def restore_std() -> None:
        """
        reset redirect
        :return: None
        """
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


redirect_manager_instance = RedirectManager()
