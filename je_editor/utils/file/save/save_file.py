from threading import Lock

# 匯入自訂例外與日誌工具
# Import custom exception and logging utility
from je_editor.utils.exception.exceptions import JEditorSaveFileException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 模組層級的鎖，確保多執行緒安全
# Module-level lock for thread safety
_file_write_lock = Lock()


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

    # 記錄日誌，方便除錯與追蹤
    # Log the file path and content for debugging and tracking
    jeditor_logger.info("save_file.py write_file "
                        f"file_path: {file_path} "
                        f"content: {content}")

    content = str(content)  # 確保內容為字串 / Ensure content is a string

    try:
        _file_write_lock.acquire()  # 嘗試鎖定資源 / Acquire the lock
        if file_path != "" and file_path is not None:  # 確認路徑有效 / Ensure path is valid
            # 以寫入模式開啟檔案 (UTF-8 編碼)
            # Open file in write+read mode with UTF-8 encoding
            with open(file_path, "w+", encoding="utf-8") as file_to_write:
                file_to_write.write(content)  # 寫入內容 / Write content
    except OSError as e:
        # 捕捉檔案 IO 例外
        # Catch file IO exceptions
        jeditor_logger.error(f"Failed to write file {file_path}: {e}")
        raise JEditorSaveFileException
    finally:
        # 確保鎖一定會被釋放
        # Ensure the lock is always released
        _file_write_lock.release()
