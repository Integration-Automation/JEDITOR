import json
import os
from pathlib import Path
from threading import Lock

from je_editor.utils.exception.je_editor_exceptions import JEditorContentFileException

cwd = os.getcwd()
lock = Lock()

editor_data = {
    "last_file": None
}


def read_output_content():
    try:
        lock.acquire()
        file_path = Path(cwd + "/je_editor_content.json")
        if file_path.exists() and file_path.is_file():
            with open(cwd + "/je_editor_content.json", "r+") as read_file:
                lock.release()
                return read_file.read()
        return None
    except JEditorContentFileException:
        lock.release()
        raise JEditorContentFileException


def write_output_content():
    try:
        lock.acquire()
        with open(cwd + "/je_editor_content.json", "w+") as file_to_write:
            file_to_write.write(json.dumps(editor_data))
        lock.release()
    except JEditorContentFileException:
        lock.release()
        raise JEditorContentFileException


def save_content_and_quit(file):
    editor_data["last_file"] = file[0]
    write_output_content()


def open_content_and_start():
    editor_data["last_file"] = json.loads(read_output_content()).get("last_file")
    return [editor_data.get("last_file")]

