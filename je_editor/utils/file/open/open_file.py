import typing
from pathlib import Path
from threading import Lock

from je_editor.utils.exception.exceptions import JEditorOpenFileException
from je_editor.utils.logging.loggin_instance import jeditor_logger


def read_file(file_path: str) -> typing.List[typing.Union[str, str]]:
    """
    use to check file is exist and open
    :param file_path: the file we want to read its whole file path
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
    jeditor_logger.info(f"open_file.py read_file file_path: {file_path}")
    lock = Lock()
    try:
        lock.acquire()
        if file_path != "" and file_path is not None:
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                with open(file_path, "r+", encoding="utf-8") as open_read_file:
                    return [file_path, open_read_file.read()]
    except JEditorOpenFileException:
        raise JEditorOpenFileException
    finally:
        lock.release()
