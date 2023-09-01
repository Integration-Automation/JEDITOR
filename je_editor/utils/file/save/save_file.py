from threading import Lock

from je_editor.utils.exception.exceptions import JEditorSaveFileException


def write_file(file_path: str, content: str) -> None:
    """
    :param file_path: file we want to write
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
        if file_path != "" and file_path is not None:
            with open(file_path, "w+") as file_to_write:
                file_to_write.write(content)
    except JEditorSaveFileException:
        raise JEditorSaveFileException
    finally:
        lock.release()
