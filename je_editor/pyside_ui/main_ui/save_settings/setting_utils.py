from os import getcwd
from pathlib import Path

from je_editor.utils.json.json_file import write_json
from je_editor.utils.logging.loggin_instance import jeditor_logger


def write_setting(save_dict: dict, file_name: str) -> None:
    """
    將設定資料寫入 JSON 檔案
    Write settings dictionary into a JSON file
    """
    # 紀錄日誌，方便除錯與追蹤
    # Log the action for debugging and tracking
    jeditor_logger.info("setting_utils.py write_setting "
                        f"save_dict: {save_dict} "
                        f"file_name: {file_name}")

    # 建立儲存設定的資料夾路徑：當前工作目錄下的 `.jeditor`
    # Create the save directory path: `.jeditor` under current working directory
    save_dir = Path(getcwd() + "/.jeditor")

    # 如果資料夾不存在就自動建立 (parents=True 表示可遞迴建立多層資料夾)
    # Create the directory if it does not exist (parents=True allows nested dirs)
    save_dir.mkdir(parents=True, exist_ok=True)

    # 建立完整的檔案路徑，例如 `.jeditor/settings.json`
    # Create the full file path, e.g., `.jeditor/settings.json`
    save_file = Path(getcwd() + f"/.jeditor/{file_name}")

    # 將設定字典寫入 JSON 檔案
    # Write the dictionary into the JSON file
    write_json(str(save_file), save_dict)
