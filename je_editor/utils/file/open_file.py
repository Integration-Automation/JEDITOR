import os
from pathlib import Path
from threading import Lock

from PyQt5.QtWidgets import QFileDialog

from je_editor.utils.exception.je_editor_exceptions import JEditorOpenFileException

cwd = os.getcwd()
lock = Lock()


def read_file(file, source):
    try:
        lock.acquire()
        if file[0] != "" and file[0] is not None:
            file_path = Path(file[0])
            if file_path.exists() and file_path.is_file():
                with open(file[0], "r+") as open_read_file:
                    source(open_read_file.read())
        return file
    except JEditorOpenFileException:
        raise JEditorOpenFileException
    finally:
        lock.release()


def open_file(source):
    file = QFileDialog.getOpenFileName(None, "choose file", cwd)
    return read_file(file, source)
