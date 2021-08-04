import os
from threading import Lock
from threading import Thread

from PyQt5.QtWidgets import QFileDialog
from je_editor.utils.exception.je_editor_exceptions import JEditorOpenFileException
from je_editor.utils.exception.je_editor_exception_tag import je_editor_open_file_error
cwd = os.getcwd()


def open_file(source):
    try:
        file = QFileDialog.getOpenFileName(None, "choose file", cwd)
        lock = Lock()
        lock.acquire()
        if file[0] != "":
            with open(file[0], "r+") as read_file:
                source(read_file.read())
        lock.release()
        return file
    except JEditorOpenFileException:
        raise JEditorOpenFileException


