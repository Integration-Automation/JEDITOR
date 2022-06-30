import os
from pathlib import Path
from threading import Lock
from tkinter import filedialog

from je_editor.utils.exception.exceptions import JEditorOpenFileException


def read_file(file):
    """
    :param file: the file we want to read it's whole file path
    :return: read's file and file content
    try
        lock thread
        find file is exist ? and is file ?
        if both is true
            try to open it and read
            return file and content
    finally
        release lock
    """
    lock = Lock()
    try:
        lock.acquire()
        if file != "" and file is not None:
            file_path = Path(file)
            if file_path.exists() and file_path.is_file():
                with open(file, "r+") as open_read_file:
                    return [file, open_read_file.read()]
    except JEditorOpenFileException:
        raise JEditorOpenFileException
    finally:
        lock.release()


def open_file():
    """
    :return: read's file and file content or ""
    open tkinter ask open file dialog
    if not choose
        len(file) = 0 or ""
        :return ""
    """
    cwd = os.getcwd()
    file = filedialog.askopenfilename(title="Open File",
                                      initialdir=cwd,
                                      defaultextension="*.*",
                                      filetypes=(("all files", "*.*"), ("je editor files", "*.jee")))
    if len(file) == 0:
        return ""
    return read_file(file)
