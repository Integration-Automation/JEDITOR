"""Tests for user settings read/write and setting_utils backup."""
from __future__ import annotations

import json

from je_editor.pyside_ui.main_ui.save_settings.setting_utils import write_setting
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict


class TestWriteSetting:
    def test_creates_jeditor_dir(self, tmp_dir):
        write_setting({"test": True}, "test_setting.json")
        assert (tmp_dir / ".jeditor" / "test_setting.json").exists()

    def test_creates_backup_on_overwrite(self, tmp_dir):
        write_setting({"version": 1}, "cfg.json")
        write_setting({"version": 2}, "cfg.json")
        bak = tmp_dir / ".jeditor" / "cfg.json.bak"
        assert bak.exists()
        with open(bak, encoding="utf-8") as f:
            data = json.load(f)
        assert data["version"] == 1

    def test_written_file_is_valid_json(self, tmp_dir):
        write_setting({"a": [1, 2, 3]}, "valid.json")
        with open(tmp_dir / ".jeditor" / "valid.json", encoding="utf-8") as f:
            data = json.load(f)
        assert data == {"a": [1, 2, 3]}


class TestUserSettingDict:
    def test_has_required_keys(self):
        required = [
            "ui_font", "ui_font_size", "language", "ui_style",
            "font", "font_size", "encoding", "last_file",
            "python_compiler", "max_line_of_output", "recent_files",
            "indent_size",
        ]
        for key in required:
            assert key in user_setting_dict, f"Missing key: {key}"

    def test_default_encoding(self):
        assert user_setting_dict["encoding"] == "utf-8"

    def test_default_indent_size(self):
        assert user_setting_dict["indent_size"] == 4

    def test_recent_files_is_list(self):
        assert isinstance(user_setting_dict["recent_files"], list)
