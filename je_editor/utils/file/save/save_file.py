import os
from threading import Lock

# 匯入自訂例外與日誌工具
# Import custom exception and logging utility
from je_editor.utils.encodings.text_codec import (
    DEFAULT_ENCODING, LINE_ENDING_LF, apply_line_ending
)
from je_editor.utils.exception.exceptions import JEditorSaveFileException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 模組層級的鎖，確保多執行緒安全
# Module-level lock for thread safety
_file_write_lock = Lock()


def write_file_with_encoding(
        file_path: str, content: str,
        encoding: str = DEFAULT_ENCODING, line_ending: str = LINE_ENDING_LF) -> None:
    """
    以指定的編碼與行尾寫入檔案
    Write a file using a given encoding and line-ending style.

    編輯器內部一律以 ``\\n`` 換行，寫出前轉回檔案原本的樣式，存檔才不會把整份
    檔案的行尾都改掉。
    The editor always uses ``\\n``; converting back before writing keeps a save
    from rewriting every line ending in the file.

    :param file_path: 要寫入的檔案路徑 / the file path to write
    :param content: 要寫入的內容 / the content to write
    :param encoding: 使用的編碼 / the encoding to write with
    :param line_ending: 使用的行尾 / the line ending to write
    :raises JEditorSaveFileException: 寫入或編碼失敗時 / when the write or encode fails
    """
    jeditor_logger.info("save_file.py write_file_with_encoding "
                        f"file_path: {file_path} encoding: {encoding}")
    if not file_path:
        return
    text = apply_line_ending(str(content), line_ending)
    try:
        # 先編碼再開檔：以 "w" 開檔就會清空檔案，編碼失敗時磁碟上只剩空檔
        # Encode before opening: opening with "w" empties the file, so an
        # encoding failure left an empty file where the last good one was
        data = text.encode(encoding)
    except (UnicodeEncodeError, LookupError) as error:
        jeditor_logger.error(f"Failed to encode file {file_path}: {error}")
        raise JEditorSaveFileException from error
    _write_bytes(file_path, data)


def write_file(file_path: str, content: str) -> None:
    """
    功能說明 (Function Description):
    將指定內容寫入檔案，並確保在多執行緒環境下安全操作。
    Write the given content into a file, ensuring thread safety.

    :param file_path: 要寫入的檔案路徑 / the file path to write
    :param content: 要寫入的內容 / the content to write

    流程 (Logic):
    1. 嘗試鎖定執行緒 (避免多執行緒同時存取檔案)
       Try to lock the thread (prevent concurrent file access).
    2. 檢查檔案路徑是否為空字串或 None。
       Check if file path is not empty or None.
    3. 若條件成立，開啟檔案並以 UTF-8 編碼寫入內容。
       If valid, open the file and write content with UTF-8 encoding.
    4. 最後釋放鎖。
       Finally, release the lock.
    """

    content = str(content)  # 確保內容為字串 / Ensure content is a string

    # 只記路徑與長度。內容曾經整份寫進日誌，等於把使用者編輯的每個檔案都抄一份到
    # JEditor.log 裡。
    # The path and a length, nothing more. This used to log the content itself,
    # which copied every file the user edited into JEditor.log.
    jeditor_logger.info("save_file.py write_file "
                        f"file_path: {file_path} "
                        f"length: {len(content)}")

    if file_path == "" or file_path is None:  # 確認路徑有效 / Ensure path is valid
        return
    try:
        # 先編碼再開檔，理由同 write_file_with_encoding（例如孤立的代理字元）
        # Encode before opening, for the same reason as write_file_with_encoding
        # (a lone surrogate, for one, cannot be written as UTF-8)
        data = content.encode("utf-8")
    except UnicodeEncodeError as error:
        jeditor_logger.error(f"Failed to encode file {file_path}: {error}")
        raise JEditorSaveFileException from error
    # 以文字模式寫入時 Windows 會把 \n 轉成 \r\n，這裡照舊
    # Text mode turned \n into \r\n on Windows; keep doing that
    _write_bytes(file_path, data.replace(b"\n", os.linesep.encode("ascii")))


def _write_bytes(file_path: str, data: bytes) -> None:
    """
    在鎖內把已編碼好的內容寫入檔案
    Write already-encoded content to the file, under the module lock.

    :raises JEditorSaveFileException: 寫入失敗時 / when the write fails
    """
    try:
        _file_write_lock.acquire()  # 嘗試鎖定資源 / Acquire the lock
        with open(file_path, "wb") as file_to_write:
            file_to_write.write(data)
    except OSError as error:
        jeditor_logger.error(f"Failed to write file {file_path}: {error}")
        raise JEditorSaveFileException from error
    finally:
        # 確保鎖一定會被釋放 / Ensure the lock is always released
        _file_write_lock.release()
