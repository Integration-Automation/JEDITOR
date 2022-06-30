import os
import time
from pathlib import Path
from threading import Lock
from threading import Thread
from tkinter import filedialog

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


def save_file(content):
    """
    :param content: content we want to write or ""
    :return: choose file
    open tkinter ask save file dialog
    if not choose
        len(file) = 0 or ""
        :return ""
    """
    cwd = os.getcwd()
    file = filedialog.asksaveasfilename(title="Save File",
                                        initialdir=cwd,
                                        defaultextension="*.*",
                                        filetypes=(("all files", "*.*"), ("je editor files", "*.jee")))
    if len(file) == 0:
        return ""
    write_file(file, content)
    return file


class SaveThread(Thread):

    def __init__(self, file, tkinter_text, auto_save=False):
        """
        :param file: file we want to auto save
        :param tkinter_text: tkinter text
        :param auto_save: not need to change
        """
        super().__init__()
        self.file = file
        self.path = None
        self.tkinter_text = tkinter_text
        self.auto_save = auto_save
        # set daemon
        self.setDaemon(True)

    def run(self):
        # loop and save current edit file
        print("auto save start")
        if self.file is not None:
            self.auto_save = True
            self.path = Path(self.file)
        while self.auto_save and self.file is not None:
            time.sleep(15)
            if self.path.exists() and self.path.is_file():
                print("auto saved file: ", str(self.file))
                write_file(self.file, self.tkinter_text.get("1.0", "end-1c"))
            else:
                break
