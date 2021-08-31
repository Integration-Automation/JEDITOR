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
                return read_file.read()
    except JEditorContentFileException:
        raise JEditorContentFileException
    finally:
        lock.release()


def write_output_content():
    try:
        lock.acquire()
        with open(cwd + "/je_editor_content.json", "w+") as file_to_write:
            file_to_write.write(json.dumps(editor_data))
    except JEditorContentFileException:
        raise JEditorContentFileException
    finally:
        lock.release()


def save_content_and_quit(file):
    editor_data["last_file"] = file
    write_output_content()


def open_content_and_start():
    temp_content = read_output_content()
    if temp_content is not None:
        editor_data["last_file"] = json.loads(temp_content).get("last_file")
    return editor_data.get("last_file")
