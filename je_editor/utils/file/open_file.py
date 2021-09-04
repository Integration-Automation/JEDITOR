import os
from pathlib import Path
from threading import Lock
from tkinter import filedialog

from je_editor.utils.exception.je_editor_exceptions import JEditorOpenFileException

cwd = os.getcwd()
lock = Lock()


def read_file(file):
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
    file = filedialog.askopenfilename(title="Open File",
                                      initialdir=cwd,
                                      defaultextension="*.*",
                                      filetypes=(("all files", "*.*"), ("je editor files", "*.jee")))
    if len(file) == 0:
        return ""
    return read_file(file)
