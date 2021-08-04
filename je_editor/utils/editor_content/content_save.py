import os
import json
from pathlib import Path
from threading import Lock

from je_editor.utils.exception.je_editor_exceptions import JEditorContentFileException

cwd = os.getcwd()
lock = Lock()

editor_data = {
    "last_file": None
}


def read_output_content(path):
    try:
        lock.acquire()
        file_path = Path(path)
        if file_path.exists() and file_path.is_file():
            with open(path, "r+") as read_file:
                lock.release()
                return read_file.read()
    except JEditorContentFileException:
        lock.release()
        raise JEditorContentFileException


def write_output_content(content):
    try:
        lock.acquire()
        with open(cwd, "w+") as file_to_write:
            file_to_write.write(content)
        lock.release()
    except JEditorContentFileException:
        lock.release()
        raise JEditorContentFileException


def save_content_and_quit(file):
    editor_data["last_file"] = file[0]

