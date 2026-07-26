"""Tests that every language is complete, and that the system's locale is followed."""
from __future__ import annotations

import re

import pytest

from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.locale_match import (
    DEFAULT_LANGUAGE, language_for_locale, normalise_locale
)
from je_editor.utils.multi_language.multi_language_wrapper import (
    LanguageWrapper, resolve_startup_language
)

# The languages that ship with the editor, as the wrapper registers them.
SHIPPED = LanguageWrapper().choose_language_dict


def _placeholders(text: str) -> set:
    """The {name} fields a string expects to be given."""
    return set(re.findall(r"\{(\w+)\}", text))


class TestEveryLanguageIsComplete:
    @pytest.mark.parametrize("language", sorted(SHIPPED))
    def test_it_covers_every_key(self, language):
        missing = sorted(set(english_word_dict) - set(SHIPPED[language]))
        assert missing == [], f"{language} is missing {missing[:5]}"

    @pytest.mark.parametrize("language", sorted(SHIPPED))
    def test_it_invents_no_keys(self, language):
        extra = sorted(set(SHIPPED[language]) - set(english_word_dict))
        assert extra == [], f"{language} has keys English does not: {extra[:5]}"

    @pytest.mark.parametrize("language", sorted(SHIPPED))
    def test_the_placeholders_survive_translation(self, language):
        # A dropped {name} silently swallows whatever it was meant to show.
        for key, english in english_word_dict.items():
            assert _placeholders(SHIPPED[language][key]) == _placeholders(english), key

    @pytest.mark.parametrize("language", sorted(SHIPPED))
    def test_nothing_is_left_blank(self, language):
        blank = [key for key, value in SHIPPED[language].items() if not str(value).strip()]
        assert blank == []


class TestFallingBackToEnglish:
    """
    A key a language has not translated yet shows English rather than a blank,
    which is what makes it possible to add a language before finishing it.
    """

    def test_a_missing_key_comes_from_english(self):
        wrapper = LanguageWrapper()
        wrapper.register_language("Partial", {"file_menu_label": "Datei"}, "Deutsch")
        wrapper.reset_language("Partial")
        assert wrapper.language_word_dict["file_menu_label"] == "Datei"
        assert wrapper.language_word_dict["toolbar_run"] == english_word_dict["toolbar_run"]

    def test_every_key_is_answerable(self):
        wrapper = LanguageWrapper()
        wrapper.register_language("Partial", {})
        wrapper.reset_language("Partial")
        assert set(wrapper.language_word_dict) == set(english_word_dict)

    def test_an_unknown_language_is_refused(self):
        wrapper = LanguageWrapper()
        wrapper.reset_language("Klingon")
        assert wrapper.language == "English"

    def test_english_is_offered_first(self):
        assert LanguageWrapper().available_languages()[0] == "English"

    def test_each_language_names_itself(self):
        wrapper = LanguageWrapper()
        assert wrapper.display_name("Japanese") == "日本語"
        assert wrapper.display_name("Simplified_Chinese") == "简体中文"

    def test_an_unnamed_language_reads_tidily(self):
        assert LanguageWrapper().display_name("Some_Language") == "Some Language"


class TestReadingTheLocale:
    @pytest.mark.parametrize("locale_name,expected", [
        ("zh_TW", "Traditional_Chinese"),
        ("zh-Hant", "Traditional_Chinese"),
        ("zh_HK", "Traditional_Chinese"),
        ("zh_MO", "Traditional_Chinese"),
        ("zh_CN", "Simplified_Chinese"),
        ("zh-Hans-CN", "Simplified_Chinese"),
        ("zh_SG", "Simplified_Chinese"),
        ("zh", "Simplified_Chinese"),
        ("ja_JP", "Japanese"),
        ("en_US", "English"),
    ])
    def test_a_locale_picks_its_language(self, locale_name, expected):
        assert language_for_locale(locale_name) == expected

    def test_an_encoding_suffix_is_ignored(self):
        assert language_for_locale("zh_TW.UTF-8") == "Traditional_Chinese"

    def test_case_does_not_matter(self):
        assert language_for_locale("ZH_tw") == "Traditional_Chinese"

    def test_an_unknown_locale_falls_back(self):
        assert language_for_locale("xx_YY") == DEFAULT_LANGUAGE

    def test_no_locale_falls_back(self):
        assert language_for_locale("") == DEFAULT_LANGUAGE
        assert language_for_locale(None) == DEFAULT_LANGUAGE

    def test_a_language_that_is_not_installed_falls_back(self):
        # Korean is recognised as a locale but has no dictionary yet.
        assert language_for_locale("ko_KR", available={"English"}) == DEFAULT_LANGUAGE

    def test_an_installed_language_is_used(self):
        assert language_for_locale(
            "ja_JP", available={"English", "Japanese"}) == "Japanese"

    def test_the_parts_are_split_apart(self):
        assert normalise_locale("zh-Hant-TW.UTF-8") == ["zh", "hant", "tw"]

    def test_an_empty_locale_has_no_parts(self):
        assert normalise_locale(None) == []


class TestChoosingAtStartup:
    def test_a_chosen_language_is_kept(self):
        settings = {"language": "Japanese"}
        assert resolve_startup_language(settings) == "Japanese"

    def test_a_first_run_follows_the_system(self, monkeypatch):
        monkeypatch.setattr(
            "je_editor.utils.multi_language.multi_language_wrapper.system_locale_name",
            lambda: "zh_CN")
        settings = {}
        assert resolve_startup_language(settings) == "Simplified_Chinese"

    def test_what_was_detected_is_recorded(self, monkeypatch):
        monkeypatch.setattr(
            "je_editor.utils.multi_language.multi_language_wrapper.system_locale_name",
            lambda: "ja_JP")
        settings = {}
        resolve_startup_language(settings)
        assert settings["language"] == "Japanese"

    def test_a_language_that_no_longer_exists_is_redetected(self, monkeypatch):
        monkeypatch.setattr(
            "je_editor.utils.multi_language.multi_language_wrapper.system_locale_name",
            lambda: "zh_TW")
        settings = {"language": "Klingon"}
        assert resolve_startup_language(settings) == "Traditional_Chinese"

    def test_an_unreadable_locale_leaves_english(self, monkeypatch):
        monkeypatch.setattr(
            "je_editor.utils.multi_language.multi_language_wrapper.system_locale_name",
            lambda: "")
        assert resolve_startup_language({}) == "English"


class TestTheLanguageMenu:
    def test_it_lists_every_shipped_language(self, qapp, qtbot):
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtWidgets import QMainWindow, QMenuBar, QTabWidget
        from je_editor.pyside_ui.main_ui.menu.language_menu.build_language_server import (
            set_language_menu
        )
        window = QMainWindow()
        qtbot.addWidget(window)
        window.menu = QMenuBar()
        window.font_database = QFontDatabase()
        window.tab_widget = QTabWidget()
        set_language_menu(window)
        assert set(window.language_menu.language_actions) >= set(SHIPPED)

    def test_each_entry_is_named_in_its_own_language(self, qapp, qtbot):
        from PySide6.QtWidgets import QMainWindow, QMenuBar
        from je_editor.pyside_ui.main_ui.menu.language_menu.build_language_server import (
            set_language_menu
        )
        window = QMainWindow()
        qtbot.addWidget(window)
        window.menu = QMenuBar()
        set_language_menu(window)
        assert window.language_menu.language_actions["Japanese"].text() == "日本語"
