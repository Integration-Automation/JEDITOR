from pathlib import Path
from threading import Lock

# 匯入自訂例外與日誌工具
# Import custom exception and logging utility
from je_editor.utils.exception.exceptions import JEditorOpenFileException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 模組層級的鎖，確保多執行緒安全
# Module-level lock for thread safety
_file_read_lock = Lock()


def read_file(file_path: str) -> list[Path | str] | None:
    """
    功能說明 (Function Description):
    用來檢查檔案是否存在並嘗試開啟，讀取其內容。
    Used to check if a file exists and open it to read its content.

    :param file_path: 檔案完整路徑 / the full path of the file to read
    :return: [檔案路徑, 檔案內容] / [file path, file content]

    流程 (Logic):
    1. 嘗試鎖定執行緒 (避免多執行緒同時存取)
       Try to lock the thread (prevent concurrent access).
    2. 檢查檔案路徑是否為空，並確認檔案存在且為檔案。
       Check if file path is not empty, exists, and is a file.
    3. 若條件成立，嘗試以 UTF-8 編碼開啟檔案並讀取內容。
       If true, open the file with UTF-8 encoding and read content.
    4. 最後釋放鎖。
       Finally, release the lock.
    """

    # 記錄日誌，方便除錯與追蹤
    # Log the file path for debugging and tracking
    jeditor_logger.info(f"open_file.py read_file file_path: {file_path}")

    try:
        _file_read_lock.acquire()  # 嘗試鎖定資源 / Acquire the lock
        if file_path != "" and file_path is not None:  # 確認路徑不為空 / Ensure path is not empty
            file_path = Path(file_path)  # 轉換為 Path 物件 / Convert to Path object
            if file_path.exists() and file_path.is_file():  # 檢查檔案存在且為檔案 / Check file existence
                # 以唯讀模式開啟檔案 (UTF-8 編碼)
                # Open file in read-only mode with UTF-8 encoding
                with open(file_path, "r", encoding="utf-8") as open_read_file:
                    return [file_path, open_read_file.read()]  # 回傳檔案路徑與內容 / Return file path and content
    except (OSError, UnicodeDecodeError) as e:
        # 捕捉檔案 IO 與編碼例外
        # Catch file IO and encoding exceptions
        jeditor_logger.error(f"Failed to read file {file_path}: {e}")
        raise JEditorOpenFileException
    finally:
        # 確保鎖一定會被釋放
        # Ensure the lock is always released
        _file_read_lock.release()
