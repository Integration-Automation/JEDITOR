from os import getcwd
from pathlib import Path
from typing import Dict

from PySide6.QtGui import QColor

from je_editor.pyside_ui.main_ui.save_settings.setting_utils import write_setting
from je_editor.utils.json.json_file import read_json
from je_editor.utils.logging.loggin_instance import jeditor_logger


def _to_qcolor(key: str, fallback: list) -> QColor:
    """安全地將 RGB list 轉換為 QColor / Safely convert RGB list to QColor with fallback."""
    rgb = user_setting_color_dict.get(key, fallback)
    if rgb is None or not isinstance(rgb, list) or len(rgb) < 3:
        rgb = fallback
    return QColor(
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2]))
    )


def update_actually_color_dict() -> None:
    """
    更新實際使用的顏色字典 (actually_color_dict)，
    將 user_setting_color_dict 中的 RGB 值轉換成 QColor 物件。
    Update the actual color dictionary (actually_color_dict),
    converting RGB values from user_setting_color_dict into QColor objects.
    """
    actually_color_dict.update(
        {
            "line_number_color": _to_qcolor("line_number_color", [255, 255, 255]),
            "line_number_background_color": _to_qcolor("line_number_background_color", [179, 179, 179]),
            "current_line_color": _to_qcolor("current_line_color", [148, 148, 184]),
            "normal_output_color": _to_qcolor("normal_output_color", [255, 255, 255]),
            "error_output_color": _to_qcolor("error_output_color", [255, 0, 0]),
            "warning_output_color": _to_qcolor("warning_output_color", [204, 204, 0]),
            "bookmark_marker_color": _to_qcolor("bookmark_marker_color", [66, 165, 245]),
            "fold_marker_color": _to_qcolor("fold_marker_color", [120, 120, 120]),
            "occurrence_highlight_color": _to_qcolor("occurrence_highlight_color", [80, 90, 60]),
            "diff_added_marker_color": _to_qcolor("diff_added_marker_color", [76, 175, 80]),
            "diff_modified_marker_color": _to_qcolor("diff_modified_marker_color", [255, 167, 38]),
            "diff_removed_marker_color": _to_qcolor("diff_removed_marker_color", [229, 57, 53]),
            "lint_underline_color": _to_qcolor("lint_underline_color", [255, 138, 101]),
            "blame_annotation_color": _to_qcolor("blame_annotation_color", [130, 130, 130]),
            "indent_guide_color": _to_qcolor("indent_guide_color", [90, 90, 110]),
            "minimap_background_color": _to_qcolor("minimap_background_color", [40, 40, 48]),
            "minimap_line_color": _to_qcolor("minimap_line_color", [130, 130, 150]),
            "minimap_viewport_color": _to_qcolor("minimap_viewport_color", [80, 80, 110]),
            "extra_cursor_color": _to_qcolor("extra_cursor_color", [255, 215, 64]),
            "syntax_keyword_color": _to_qcolor("syntax_keyword_color", [86, 156, 214]),
            "syntax_string_color": _to_qcolor("syntax_string_color", [206, 145, 120]),
            "syntax_comment_color": _to_qcolor("syntax_comment_color", [106, 153, 85]),
            "syntax_number_color": _to_qcolor("syntax_number_color", [181, 206, 168]),
            "trailing_whitespace_color": _to_qcolor("trailing_whitespace_color", [120, 70, 70]),
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
    "warning_output_color": [204, 204, 0],
    "bookmark_marker_color": [66, 165, 245],
    "fold_marker_color": [120, 120, 120],
    "occurrence_highlight_color": [80, 90, 60],
    "diff_added_marker_color": [76, 175, 80],
    "diff_modified_marker_color": [255, 167, 38],
    "diff_removed_marker_color": [229, 57, 53],
    "lint_underline_color": [255, 138, 101],
    "blame_annotation_color": [130, 130, 130],
    "indent_guide_color": [90, 90, 110],
    "minimap_background_color": [40, 40, 48],
    "minimap_line_color": [130, 130, 150],
    "minimap_viewport_color": [80, 80, 110],
    "extra_cursor_color": [255, 215, 64],
    "syntax_keyword_color": [86, 156, 214],
    "syntax_string_color": [206, 145, 120],
    "syntax_comment_color": [106, 153, 85],
    "syntax_number_color": [181, 206, 168],
    "trailing_whitespace_color": [120, 70, 70]
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
    user_color_setting_file = Path(getcwd()) / ".jeditor" / "user_color_setting.json"

    # 如果檔案存在，就讀取並更新設定
    # If the file exists, read and update the settings
    if user_color_setting_file.exists() and user_color_setting_file.is_file():
        data = read_json(str(user_color_setting_file))
        if data is not None:
            user_setting_color_dict.update(data)
