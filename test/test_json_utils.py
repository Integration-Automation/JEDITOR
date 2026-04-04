"""Tests for JSON read/write utilities."""
from __future__ import annotations

import json
import pytest

from je_editor.utils.json.json_file import read_json, write_json
from je_editor.utils.exception.exceptions import JEditorJsonException


class TestWriteJson:
    def test_write_and_read_dict(self, tmp_path):
        path = str(tmp_path / "test.json")
        data = {"key": "value", "num": 42}
        write_json(path, data)
        result = read_json(path)
        assert result == data

    def test_write_and_read_list(self, tmp_path):
        path = str(tmp_path / "test.json")
        data = [1, 2, 3, "abc"]
        write_json(path, data)
        result = read_json(path)
        assert result == data

    def test_write_overwrite(self, tmp_path):
        path = str(tmp_path / "test.json")
        write_json(path, {"a": 1})
        write_json(path, {"b": 2})
        result = read_json(path)
        assert result == {"b": 2}


class TestReadJson:
    def test_read_nonexistent_returns_none(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        result = read_json(path)
        assert result is None

    def test_read_empty_file_returns_none(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("", encoding="utf-8")
        result = read_json(str(path))
        assert result is None

    def test_read_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(JEditorJsonException):
            read_json(str(path))
