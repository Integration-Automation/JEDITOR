"""Tests for multi-language wrapper and dictionary completeness."""
from __future__ import annotations

from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.traditional_chinese import traditional_chinese_word_dict
from je_editor.utils.multi_language.multi_language_wrapper import LanguageWrapper


class TestLanguageDictCompleteness:
    """Ensure both language dicts have the same keys."""

    def test_english_keys_in_chinese(self):
        missing = set(english_word_dict) - set(traditional_chinese_word_dict)
        assert not missing, f"Keys in English but missing in Chinese: {missing}"

    def test_chinese_keys_in_english(self):
        missing = set(traditional_chinese_word_dict) - set(english_word_dict)
        assert not missing, f"Keys in Chinese but missing in English: {missing}"

    def test_no_empty_values_english(self):
        empty = [k for k, v in english_word_dict.items() if v is None or (isinstance(v, str) and not v.strip())]
        assert not empty, f"Empty values in English: {empty}"

    def test_no_empty_values_chinese(self):
        empty = [k for k, v in traditional_chinese_word_dict.items() if v is None or (isinstance(v, str) and not v.strip())]
        assert not empty, f"Empty values in Chinese: {empty}"


class TestLanguageWrapper:
    """Test LanguageWrapper switching behavior."""

    def test_default_language_is_english(self):
        lw = LanguageWrapper()
        assert lw.language == "English"
        assert lw.language_word_dict is english_word_dict

    def test_switch_to_traditional_chinese(self):
        lw = LanguageWrapper()
        lw.reset_language("Traditional_Chinese")
        assert lw.language == "Traditional_Chinese"
        assert lw.language_word_dict is traditional_chinese_word_dict

    def test_switch_to_unknown_keeps_current(self):
        lw = LanguageWrapper()
        lw.reset_language("NonExistent")
        assert lw.language == "English"

    def test_switch_back_to_english(self):
        lw = LanguageWrapper()
        lw.reset_language("Traditional_Chinese")
        lw.reset_language("English")
        assert lw.language_word_dict is english_word_dict
