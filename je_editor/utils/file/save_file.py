import os
import time
from threading import Lock
from threading import Thread

from PyQt5.QtWidgets import QFileDialog

cwd = os.getcwd()


def write_file(file, source):
    lock = Lock()
    lock.acquire()
    if file[0] != "":
        with open(file[0], "w+") as write_file:
            write_file.write(source())
    lock.release()


def save_file(source):
    file = QFileDialog.getSaveFileName(None, "choose file", cwd)
    write_file(file, source)
    return file


class SaveThread(Thread):

    def __init__(self, file, source, auto_save=False):
        super().__init__()
        self.file = file
        self.source = source
        self.auto_save = auto_save
        self.setDaemon(True)

    def run(self) -> None:
        if self.file[0] != "":
            self.auto_save = True
        while self.auto_save:
            time.sleep(15)
            write_file(self.file, self.source)
            self.run()
