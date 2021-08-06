import os
import time
from pathlib import Path
from threading import Lock
from threading import Thread

from PyQt5.QtWidgets import QFileDialog

from je_editor.utils.exception.je_editor_exceptions import JEditorSaveFileException

cwd = os.getcwd()
lock = Lock()


def write_file(file, source):
    try:
        lock.acquire()
        if file[0] != "":
            with open(file[0], "w+") as file_to_write:
                file_to_write.write(source())
    except JEditorSaveFileException:
        raise JEditorSaveFileException
    finally:
        lock.release()


def save_file(source):
    file = QFileDialog.getSaveFileName(None, "choose file", cwd)
    write_file(file, source)
    return file


class SaveThread(Thread):

    def __init__(self, file, source, auto_save=False):
        super().__init__()
        self.file = file
        self.path = None
        self.source = source
        self.auto_save = auto_save
        self.setDaemon(True)

    def run(self) -> None:
        if self.file[0] != "":
            self.auto_save = True
            self.path = Path(self.file[0])
        while self.auto_save:
            time.sleep(15)
            if self.path.exists() and self.path.is_file():
                write_file(self.file, self.source)
            self.run()
