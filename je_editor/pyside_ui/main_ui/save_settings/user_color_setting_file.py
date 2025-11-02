from os import getcwd
from pathlib import Path
from typing import Dict

from PySide6.QtGui import QColor

from je_editor.pyside_ui.main_ui.save_settings.setting_utils import write_setting
from je_editor.utils.json.json_file import read_json
from je_editor.utils.logging.loggin_instance import jeditor_logger


def update_actually_color_dict():
    """
    更新實際使用的顏色字典 (actually_color_dict)，
    將 user_setting_color_dict 中的 RGB 值轉換成 QColor 物件。
    Update the actual color dictionary (actually_color_dict),
    converting RGB values from user_setting_color_dict into QColor objects.
    """
    jeditor_logger.info(f"user_color_setting_file.py update_actually_color_dict")

    actually_color_dict.update(
        {
            # 行號顏色 / Line number color
            "line_number_color": QColor(
                user_setting_color_dict.get("line_number_color")[0],
                user_setting_color_dict.get("line_number_color")[1],
                user_setting_color_dict.get("line_number_color")[2],
            ),
            # 行號背景顏色 / Line number background color
            "line_number_background_color": QColor(
                user_setting_color_dict.get("line_number_background_color")[0],
                user_setting_color_dict.get("line_number_background_color")[1],
                user_setting_color_dict.get("line_number_background_color")[2],
            ),
            # 當前行顏色 / Current line highlight color
            "current_line_color": QColor(
                user_setting_color_dict.get("current_line_color")[0],
                user_setting_color_dict.get("current_line_color")[1],
                user_setting_color_dict.get("current_line_color")[2],
            ),
            # 一般輸出顏色 / Normal output color
            "normal_output_color": QColor(
                user_setting_color_dict.get("normal_output_color")[0],
                user_setting_color_dict.get("normal_output_color")[1],
                user_setting_color_dict.get("normal_output_color")[2],
            ),
            # 錯誤輸出顏色 / Error output color
            "error_output_color": QColor(
                user_setting_color_dict.get("error_output_color")[0],
                user_setting_color_dict.get("error_output_color")[1],
                user_setting_color_dict.get("error_output_color")[2],
            ),
            # 警告輸出顏色 / Warning output color
            "warning_output_color": QColor(
                user_setting_color_dict.get("warning_output_color")[0],
                user_setting_color_dict.get("warning_output_color")[1],
                user_setting_color_dict.get("warning_output_color")[2],
            )
        }
    )


# 使用者設定的顏色字典 (以 RGB list 表示)
# User-defined color dictionary (stored as RGB lists)
user_setting_color_dict: Dict[str, list] = {
    "line_number_color": [255, 255, 255],
    "line_number_background_color": [179, 179, 179],
    "current_line_color": [148, 148, 184],
    "normal_output_color": [255, 255, 255],
    "error_output_color": [255, 0, 0],
    "warning_output_color": [204, 204, 0]
}

# 實際使用的顏色字典 (以 QColor 表示)
# Actual color dictionary (stored as QColor objects)
actually_color_dict: Dict[str, QColor] = {}

# 初始化時先更新一次
# Update once at initialization
update_actually_color_dict()


def write_user_color_setting() -> None:
    """
    將使用者顏色設定寫入 JSON 檔案
    Write user color settings into a JSON file
    """
    jeditor_logger.info("user_color_setting_file.py write_user_color_setting")
    write_setting(user_setting_color_dict, "user_color_setting.json")


def read_user_color_setting() -> None:
    """
    從 JSON 檔案讀取使用者顏色設定，並更新 user_setting_color_dict
    Read user color settings from JSON file and update user_setting_color_dict
    """
    jeditor_logger.info("user_color_setting_file.py read_user_color_setting")
    user_color_setting_file = Path(getcwd() + "/.jeditor/user_color_setting.json")

    # 如果檔案存在，就讀取並更新設定
    # If the file exists, read and update the settings
    if user_color_setting_file.exists() and user_color_setting_file.is_file():
        user_setting_color_dict.update(read_json(str(user_color_setting_file)))
