import json
from pathlib import Path
from threading import Lock
from typing import Union

from je_editor.utils.exception.exception_tags import cant_find_json_error
from je_editor.utils.exception.exception_tags import cant_save_json_error
from je_editor.utils.exception.exceptions import JEditorJsonException

_lock = Lock()


def read_json(json_file_path: str) -> Union[list, dict]:
    """
    use to read action file
    :param json_file_path json file's path to read
    """
    _lock.acquire()
    try:
        file_path = Path(json_file_path)
        if file_path.exists() and file_path.is_file():
            with open(json_file_path) as read_file:
                return json.loads(read_file.read())
    except JEditorJsonException:
        raise JEditorJsonException(cant_find_json_error)
    finally:
        _lock.release()


def write_json(json_save_path: str, data_to_output: Union[list, dict]) -> None:
    """
    use to save action file
    :param json_save_path  json save path
    :param data_to_output data to output
    """
    _lock.acquire()
    try:
        with open(json_save_path, "w+") as file_to_write:
            file_to_write.write(json.dumps(data_to_output, indent=4))
    except JEditorJsonException:
        raise JEditorJsonException(cant_save_json_error)
    finally:
        _lock.release()
