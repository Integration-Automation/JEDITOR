import os
import time
from pathlib import Path
from threading import Lock
from threading import Thread
from tkinter import filedialog

from je_editor.utils.exception.je_editor_exceptions import JEditorSaveFileException

cwd = os.getcwd()
lock = Lock()


def write_file(file, content):
    try:
        lock.acquire()
        if file != "":
            with open(file, "w+") as file_to_write:
                file_to_write.write(content)
    except JEditorSaveFileException:
        raise JEditorSaveFileException
    finally:
        lock.release()


def save_file(content):
    file = filedialog.asksaveasfilename(title="Save File",
                                        initialdir=cwd,
                                        defaultextension="*.*",
                                        filetypes=(("all files", "*.*"), ("je editor files", "*.jee")))
    write_file(file, content)
    return file


class SaveThread(Thread):

    def __init__(self, file, tkinter_text, auto_save=False):
        super().__init__()
        self.file = file
        self.path = None
        self.tkinter_text = tkinter_text
        self.auto_save = auto_save
        self.setDaemon(True)
        print("auto save init")

    def run(self):
        if self.file is not None:
            self.auto_save = True
            self.path = Path(self.file)
        while self.auto_save:
            time.sleep(15)
            print("auto saved")
            if self.path.exists() and self.path.is_file():
                write_file(self.file, self.tkinter_text.get("1.0", "end-1c"))
            else:
                break
