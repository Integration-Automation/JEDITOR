from os import getcwd
from pathlib import Path

from je_editor.utils.json.json_file import write_json
from je_editor.utils.logging.loggin_instance import jeditor_logger


def write_setting(save_dict: dict, file_name: str) -> None:
    jeditor_logger.info("setting_utils.py write_setting "
                        f"save_dict: {save_dict} "
                        f"file_name: {file_name}")
    save_dir = Path(getcwd() + "/.jeditor")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_file = Path(getcwd() + f"/.jeditor/{file_name}")
    write_json(str(save_file), save_dict)

