from os import getcwd
from pathlib import Path

from je_editor.pyside_ui.main_ui.save_settings.setting_utils import write_setting
from je_editor.utils.json.json_file import read_json
from je_editor.utils.logging.loggin_instance import jeditor_logger

user_setting_dict = {
    "ui_font": "Lato",
    "ui_font_size": 12,
    "language": "English",
    "ui_style": "dark_amber.xml",
    "font": "Lato",
    "font_size": 12,
    "encoding": "utf-8",
    "last_file": None,
    "python_compiler": None,
    "max_line_of_output": 200000,
}


def write_user_setting() -> None:
    jeditor_logger.info(f"user_setting_file.py write_user_setting")
    write_setting(user_setting_dict, "user_setting.json")


def read_user_setting() -> None:
    jeditor_logger.info(f"user_setting_file.py read_user_setting")
    user_setting_file = Path(getcwd() + "/.jeditor/user_setting.json")
    if user_setting_file.exists() and user_setting_file.is_file():
        user_setting_dict.update(read_json(str(user_setting_file)))
