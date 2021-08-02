import os
from threading import Lock
from threading import Thread

from PyQt5.QtWidgets import QFileDialog

cwd = os.getcwd()


def open_file(source):
    file = QFileDialog.getOpenFileName(None, "choose file", cwd)
    lock = Lock()
    lock.acquire()
    if file[0] != "":
        with open(file[0], "r+") as read_file:
            source(read_file.read())
    lock.release()
    return file


