import time
from pathlib import Path
from threading import Lock
from threading import Thread

from je_editor.utils.exception.exceptions import JEditorSaveFileException


def write_file(file, content):
    """
    :param file: file we want to write
    :param content: content write in file
    try
        lock thread
        if file not empty string
            write content to file
    finally
        release lock
    """
    lock = Lock()
    content = str(content)
    try:
        lock.acquire()
        if file != "" and file is not None:
            with open(file, "w+") as file_to_write:
                file_to_write.write(content)
    except JEditorSaveFileException:
        raise JEditorSaveFileException
    finally:
        lock.release()


class SaveThread(Thread):

    def __init__(self, file_to_save, text_to_write, auto_save=False):
        """
        :param file_to_save: file we want to auto save
        :param text_to_write: text that will be output to file
        :param auto_save: enable auto save or not
        """
        super().__init__()
        self.file = file_to_save
        self.path = None
        self.text_to_write = text_to_write
        self.auto_save = auto_save
        # set daemon
        self.daemon = True

    def run(self):
        # loop and save current edit file
        if self.file is not None:
            self.auto_save = True
            self.path = Path(self.file)
        while self.auto_save and self.file is not None:
            time.sleep(5)
            if self.path.exists() and self.path.is_file():
                write_file(self.file, self.text_to_write)
            else:
                break
