"""Tests for encoding detection, line-ending handling, and round-tripping files."""
from __future__ import annotations

import codecs

import pytest

from je_editor.utils.encodings.text_codec import (
    LINE_ENDING_CR,
    LINE_ENDING_CRLF,
    LINE_ENDING_LF,
    apply_line_ending,
    decode_bytes,
    detect_line_ending,
    encoding_from_bom,
    line_ending_name,
    normalise_line_endings,
)
from je_editor.utils.file.open.open_file import read_file_with_encoding
from je_editor.utils.file.save.save_file import write_file_with_encoding


class TestDetectLineEnding:
    def test_unix(self):
        assert detect_line_ending("a\nb\n") == LINE_ENDING_LF

    def test_windows(self):
        assert detect_line_ending("a\r\nb\r\n") == LINE_ENDING_CRLF

    def test_classic_mac(self):
        assert detect_line_ending("a\rb\r") == LINE_ENDING_CR

    def test_no_line_break_defaults_to_lf(self):
        assert detect_line_ending("single line") == LINE_ENDING_LF

    def test_mixed_endings_pick_the_most_common(self):
        assert detect_line_ending("a\r\nb\r\nc\n") == LINE_ENDING_CRLF

    def test_crlf_is_not_counted_as_a_lone_cr(self):
        # Two CRLF and one lone LF: CRLF wins, and the CRs are not double-counted.
        assert detect_line_ending("a\r\nb\r\nc\nd") == LINE_ENDING_CRLF

    @pytest.mark.parametrize("ending,name", [
        (LINE_ENDING_LF, "LF"), (LINE_ENDING_CRLF, "CRLF"), (LINE_ENDING_CR, "CR")])
    def test_names(self, ending, name):
        assert line_ending_name(ending) == name

    def test_unknown_ending_name_falls_back(self):
        assert line_ending_name("??") == "LF"


class TestApplyLineEnding:
    def test_to_crlf(self):
        assert apply_line_ending("a\nb\n", LINE_ENDING_CRLF) == "a\r\nb\r\n"

    def test_to_lf(self):
        assert apply_line_ending("a\r\nb\r\n", LINE_ENDING_LF) == "a\nb\n"

    def test_to_cr(self):
        assert apply_line_ending("a\nb\n", LINE_ENDING_CR) == "a\rb\r"

    def test_mixed_input_becomes_consistent(self):
        assert apply_line_ending("a\r\nb\nc\r", LINE_ENDING_LF) == "a\nb\nc\n"

    def test_normalise(self):
        assert normalise_line_endings("a\r\nb\rc\n") == "a\nb\nc\n"


class TestDecodeBytes:
    def test_utf8_without_a_bom(self):
        text, encoding = decode_bytes("héllo".encode("utf-8"))
        assert text == "héllo" and encoding == "utf-8"

    def test_utf8_bom_is_recognised(self):
        text, encoding = decode_bytes(codecs.BOM_UTF8 + "hi".encode("utf-8"))
        assert text == "hi" and encoding == "utf-8-sig"

    def test_utf16_bom_is_recognised(self):
        text, encoding = decode_bytes("hi".encode("utf-16"))
        assert text == "hi" and encoding == "utf-16"

    def test_explicit_encoding_is_honoured(self):
        text, encoding = decode_bytes("中文".encode("big5"), "big5")
        assert text == "中文" and encoding == "big5"

    def test_undecodable_bytes_fall_back_instead_of_failing(self):
        text, encoding = decode_bytes(b"\xff\xfe\x00abc"[1:])
        assert isinstance(text, str) and encoding in {"utf-8", "latin-1"}

    def test_explicit_encoding_that_cannot_decode_raises(self):
        encoded = "中文".encode("big5")
        with pytest.raises(UnicodeDecodeError):
            decode_bytes(encoded, "ascii")

    def test_bom_detection_without_a_bom(self):
        assert encoding_from_bom(b"plain") is None


class TestFileRoundTrip:
    def test_crlf_file_survives_a_save(self, tmp_path):
        path = tmp_path / "windows.txt"
        path.write_bytes(b"a\r\nb\r\n")
        _p, content, encoding, ending = read_file_with_encoding(str(path))
        assert content == "a\nb\n"  # normalised for the editor
        assert ending == LINE_ENDING_CRLF
        write_file_with_encoding(str(path), content, encoding, ending)
        assert path.read_bytes() == b"a\r\nb\r\n"

    def test_lf_file_stays_lf(self, tmp_path):
        path = tmp_path / "unix.txt"
        path.write_bytes(b"a\nb\n")
        _p, content, encoding, ending = read_file_with_encoding(str(path))
        write_file_with_encoding(str(path), content, encoding, ending)
        assert path.read_bytes() == b"a\nb\n"

    def test_big5_file_round_trips(self, tmp_path):
        path = tmp_path / "big5.txt"
        path.write_bytes("中文內容\n".encode("big5"))
        _p, content, _encoding, ending = read_file_with_encoding(str(path), "big5")
        assert content == "中文內容\n"
        write_file_with_encoding(str(path), content, "big5", ending)
        assert path.read_bytes() == "中文內容\n".encode("big5")

    def test_line_ending_can_be_converted_on_save(self, tmp_path):
        path = tmp_path / "convert.txt"
        path.write_bytes(b"a\nb\n")
        _p, content, encoding, _ending = read_file_with_encoding(str(path))
        write_file_with_encoding(str(path), content, encoding, LINE_ENDING_CRLF)
        assert path.read_bytes() == b"a\r\nb\r\n"

    def test_missing_file_returns_none(self, tmp_path):
        assert read_file_with_encoding(str(tmp_path / "gone.txt")) is None

    def test_empty_path_returns_none(self):
        assert read_file_with_encoding("") is None

    def test_writing_an_empty_path_does_nothing(self, tmp_path):
        write_file_with_encoding("", "text")  # must not raise
