from os import getcwd
from pathlib import Path

from je_editor.pyside_ui.main_ui.save_settings.setting_utils import write_setting
from je_editor.utils.json.json_file import read_json
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 匯入通用的設定寫入工具
# Import utility function to write settings
# 匯入 JSON 讀取工具
# Import JSON reader utility

# 匯入日誌工具
# Import logger


# 使用者設定字典，包含 UI 與編輯器的偏好
# User settings dictionary, storing UI and editor preferences
user_setting_dict = {
    "ui_font": "Lato",  # UI 字型 / UI font
    "ui_font_size": 12,  # UI 字體大小 / UI font size
    "language": "English",  # 語言設定 / Language setting
    "ui_style": "dark_amber.xml",  # UI 樣式檔 / UI style file
    "font": "Lato",  # 編輯器字型 / Editor font
    "font_size": 12,  # 編輯器字體大小 / Editor font size
    "encoding": "utf-8",  # 檔案編碼 / File encoding
    "last_file": None,  # 上次開啟的檔案 / Last opened file
    "python_compiler": None,  # Python 編譯器路徑 / Python compiler path
    "max_line_of_output": 200000,  # 最大輸出行數限制 / Max lines of output
}


def write_user_setting() -> None:
    """
    將使用者設定寫入 JSON 檔案
    Write user settings into a JSON file
    """
    jeditor_logger.info("user_setting_file.py write_user_setting")
    # 呼叫通用工具，將 user_setting_dict 寫入 `.jeditor/user_setting.json`
    # Use utility to write user_setting_dict into `.jeditor/user_setting.json`
    write_setting(user_setting_dict, "user_setting.json")


def read_user_setting() -> None:
    """
    從 JSON 檔案讀取使用者設定，並更新 user_setting_dict
    Read user settings from JSON file and update user_setting_dict
    """
    jeditor_logger.info("user_setting_file.py read_user_setting")

    # 設定檔路徑：當前工作目錄下的 `.jeditor/user_setting.json`
    # File path: `.jeditor/user_setting.json` under current working directory
    user_setting_file = Path(getcwd() + "/.jeditor/user_setting.json")

    # 如果檔案存在，就讀取並更新設定字典
    # If the file exists, read and update the settings dictionary
    if user_setting_file.exists() and user_setting_file.is_file():
        user_setting_dict.update(read_json(str(user_setting_file)))
