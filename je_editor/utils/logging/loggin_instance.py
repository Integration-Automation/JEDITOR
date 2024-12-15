import logging
from logging.handlers import RotatingFileHandler

logging.root.setLevel(logging.DEBUG)
jeditor_logger = logging.getLogger("JEditor")
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')


class JEditorLoggingHandler(RotatingFileHandler):

    # redirect logging stderr output to queue

    def __init__(self, filename: str = "JEditor.log", mode="w",
                 maxBytes:int=1073741824, backupCount:int=0):
        super().__init__(filename=filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount)
        self.formatter = formatter
        self.setLevel(logging.DEBUG)

    def emit(self, record: logging.LogRecord) -> None:
        print(self.format(record))


# File handler
file_handler = JEditorLoggingHandler()
file_handler.setFormatter(formatter)
jeditor_logger.addHandler(file_handler)


