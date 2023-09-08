from os import getcwd
from pathlib import Path
from typing import Dict

from PySide6.QtGui import QColor

from je_editor.utils.json.json_file import write_json, read_json

user_setting_color_dict: Dict[str, list] = {
    "line_number_color": [255, 255, 255],
    "line_number_background_color": [179, 179, 179],
    "current_line_color": [194, 194, 214],
    "normal_output_color": [255, 255, 255],
    "error_output_color": [255, 0, 0]
}

actually_color_dict: Dict[str, QColor] = {
    "line_number_color": QColor(
        user_setting_color_dict.get("line_number_color")[0],
        user_setting_color_dict.get("line_number_color")[1],
        user_setting_color_dict.get("line_number_color")[2],
    ),
    "line_number_background_color": QColor(
        user_setting_color_dict.get("line_number_background_color")[0],
        user_setting_color_dict.get("line_number_background_color")[1],
        user_setting_color_dict.get("line_number_background_color")[2],
    ),
    "current_line_color": QColor(
        user_setting_color_dict.get("current_line_color")[0],
        user_setting_color_dict.get("current_line_color")[1],
        user_setting_color_dict.get("current_line_color")[2],
    ),
    "normal_output_color": QColor(
        user_setting_color_dict.get("normal_output_color")[0],
        user_setting_color_dict.get("normal_output_color")[1],
        user_setting_color_dict.get("normal_output_color")[2],
    ),
    "error_output_color": QColor(
        user_setting_color_dict.get("error_output_color")[0],
        user_setting_color_dict.get("error_output_color")[1],
        user_setting_color_dict.get("error_output_color")[2],
    )
}


def write_user_color_setting() -> None:
    user_setting_dir = Path(getcwd() + "/.jeditor")
    user_setting_dir.mkdir(parents=True, exist_ok=True)
    user_color_setting_file = Path(getcwd() + "/.jeditor/user_color_setting.json")
    write_json(str(user_color_setting_file), user_setting_color_dict)


def read_user_color_setting() -> None:
    user_color_setting_file = Path(getcwd() + "/.jeditor/user_color_setting.json")
    if user_color_setting_file.exists() and user_color_setting_file.is_file():
        user_setting_color_dict.update(read_json(str(user_color_setting_file)))