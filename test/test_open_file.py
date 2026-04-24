"""Tests for file open/read utility."""
from __future__ import annotations

from je_editor.utils.file.open.open_file import read_file


class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "hello.py"
        f.write_text("print('hello')\n", encoding="utf-8")
        result = read_file(str(f))
        assert result is not None
        assert result[1] == "print('hello')\n"

    def test_read_empty_path_returns_none(self):
        result = read_file("")
        assert result is None

    def test_read_none_path_returns_none(self):
        result = read_file(None)
        assert result is None

    def test_read_nonexistent_file_returns_none(self, tmp_path):
        result = read_file(str(tmp_path / "no_such_file.txt"))
        assert result is None

    def test_read_directory_returns_none(self, tmp_path):
        result = read_file(str(tmp_path))
        assert result is None

    def test_read_utf8_content(self, tmp_path):
        f = tmp_path / "unicode.txt"
        f.write_text("你好世界\n", encoding="utf-8")
        result = read_file(str(f))
        assert result is not None
        assert "你好" in result[1]
