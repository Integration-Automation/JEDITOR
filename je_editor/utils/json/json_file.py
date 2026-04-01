import json
from pathlib import Path
from threading import Lock
from typing import Union, Any

# 匯入自訂錯誤訊息與例外類別
# Import custom error messages and exception class
from je_editor.utils.exception.exception_tags import cant_find_json_error
from je_editor.utils.exception.exception_tags import cant_save_json_error
from je_editor.utils.exception.exceptions import JEditorJsonException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 全域鎖，確保多執行緒存取 JSON 檔案時的安全性
# Global lock to ensure thread safety when accessing JSON files
_lock = Lock()


def read_json(json_file_path: str) -> Any | None:
    """
    功能說明 (Function Description):
    讀取 JSON 檔案並回傳其內容。
    Read a JSON file and return its content.

    :param json_file_path: JSON 檔案路徑 / path to the JSON file
    :return: list 或 dict，取決於 JSON 結構 / list or dict depending on JSON structure
    """
    jeditor_logger.info(f"json_file.py read_json json_file_path: {json_file_path}")
    _lock.acquire()  # 嘗試鎖定資源 / Acquire the lock
    try:
        file_path = Path(json_file_path)
        if file_path.exists() and file_path.is_file():  # 確認檔案存在且為檔案 / Ensure file exists
            with open(json_file_path, encoding="utf-8") as read_file:  # 開啟檔案 (UTF-8)
                content = read_file.read()
                if not content.strip():
                    return None
                return json.loads(content)  # 載入 JSON 並回傳 / Load JSON and return
    except (json.JSONDecodeError, OSError) as e:
        # 捕捉 JSON 解析錯誤或檔案 IO 錯誤
        # Catch JSON decode errors or file IO errors
        jeditor_logger.error(f"Failed to read JSON file {json_file_path}: {e}")
        raise JEditorJsonException(cant_find_json_error)
    finally:
        _lock.release()  # 確保鎖一定會被釋放 / Ensure the lock is always released


def write_json(json_save_path: str, data_to_output: Union[list, dict]) -> None:
    """
    功能說明 (Function Description):
    將資料寫入 JSON 檔案。
    Write data into a JSON file.

    :param json_save_path: JSON 檔案儲存路徑 / path to save the JSON file
    :param data_to_output: 要輸出的資料 (list 或 dict) / data to output (list or dict)
    """
    jeditor_logger.info("json_file.py write_json "
                        f"json_save_path: {json_save_path} "
                        f"data_to_output: {data_to_output}")
    _lock.acquire()  # 嘗試鎖定資源 / Acquire the lock
    try:
        # 以寫入模式開啟檔案，並將資料轉換為 JSON 格式 (縮排 4 格)
        # Open file in write mode and dump data as JSON (indent=4)
        with open(json_save_path, "w+", encoding="utf-8") as file_to_write:
            file_to_write.write(json.dumps(data_to_output, indent=4))
    except (OSError, TypeError, ValueError) as e:
        jeditor_logger.error(f"Failed to write JSON file {json_save_path}: {e}")
        raise JEditorJsonException(cant_save_json_error)
    finally:
        _lock.release()  # 確保鎖一定會被釋放 / Ensure the lock is always released
