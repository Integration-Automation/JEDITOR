"""Tests that changing the language relabels the interface without a restart."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QMainWindow, QMenuBar, QTabWidget, QWidget

from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.multi_language.retranslate_text import (
    TITLE_KEYS, key_for_text, translated_again
)
from je_editor.utils.multi_language.simplified_chinese import simplified_chinese_word_dict


class TestLookingUpTranslatedText:
    """
    Some words on screen came from a translation and some are file names.
    Replacing everything would overwrite the file names.
    """

    def test_a_translated_word_is_found(self):
        assert key_for_text("Editor", {"tab_name_editor": "Editor"}) == "tab_name_editor"

    def test_a_file_name_is_not_found(self):
        assert key_for_text("main.py", {"tab_name_editor": "Editor"}) is None

    def test_nothing_is_found_for_nothing(self):
        assert key_for_text("", {"tab_name_editor": "Editor"}) is None

    def test_a_shared_translation_answers_predictably(self):
        words = {"b_key": "Same", "a_key": "Same"}
        assert key_for_text("Same", words) == "a_key"

    def test_only_the_offered_keys_are_considered(self):
        # "Editor" is a tab name, a dock title and an untranslated menu
        # identifier all at once; without narrowing, the untranslated one wins
        # and the language change looks like it did nothing.
        assert key_for_text(
            "Editor", english_word_dict, ["tab_name_editor"]) == "tab_name_editor"

    def test_a_key_outside_the_offered_set_is_not_matched(self):
        assert key_for_text("Editor", english_word_dict, ["toolbar_run"]) is None

    def test_the_title_keys_all_exist(self):
        missing = [key for key in TITLE_KEYS if key not in english_word_dict]
        assert missing == []

    def test_a_translated_word_moves_language(self):
        assert translated_again(
            "Editor", {"tab_name_editor": "Editor"},
            {"tab_name_editor": "编辑器"}) == "编辑器"

    def test_a_file_name_is_left_alone(self):
        assert translated_again(
            "main.py", {"tab_name_editor": "Editor"},
            {"tab_name_editor": "编辑器"}) == "main.py"

    def test_a_key_the_new_language_lacks_stays_put(self):
        assert translated_again("Editor", {"tab_name_editor": "Editor"}, {}) == "Editor"

    def test_the_real_dictionaries_move_a_tab_title(self):
        assert translated_again(
            english_word_dict["tab_name_editor"],
            english_word_dict, simplified_chinese_word_dict, TITLE_KEYS
        ) == simplified_chinese_word_dict["tab_name_editor"]


@pytest.fixture()
def window(qapp, qtbot):
    """A window with the pieces retranslating touches."""
    from PySide6.QtGui import QFontDatabase
    main_window = QMainWindow()
    qtbot.addWidget(main_window)
    main_window.menu = QMenuBar()
    main_window.font_database = QFontDatabase()
    main_window.tab_widget = QTabWidget()
    main_window.setCentralWidget(main_window.tab_widget)
    main_window.encoding = "utf-8"
    yield main_window
    # Building a toolbar starts a git scan that fills its combo box. The real
    # window waits for those when it closes; a bare one has to do it here, or Qt
    # aborts the process when the widget goes away underneath a running scan.
    from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import stop_background_threads
    stop_background_threads()


@pytest.fixture()
def english(qapp):
    """Start each test in English, and leave the wrapper as it was found."""
    before = language_wrapper.language
    language_wrapper.reset_language("English")
    yield
    language_wrapper.reset_language(before)


class TestRetranslatingTheWindow:
    def test_a_translated_tab_title_changes(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        window.tab_widget.addTab(QWidget(), english_word_dict["tab_name_editor"])
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Simplified_Chinese")
        retranslate_ui(window, previous)
        assert window.tab_widget.tabText(0) == \
            simplified_chinese_word_dict["tab_name_editor"]

    def test_a_file_name_tab_is_left_alone(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        window.tab_widget.addTab(QWidget(), "main.py")
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(window, previous)
        assert window.tab_widget.tabText(0) == "main.py"

    def test_the_window_title_changes(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Simplified_Chinese")
        retranslate_ui(window, previous)
        assert window.windowTitle() == \
            simplified_chinese_word_dict["application_name"]

    def test_the_menu_bar_is_rebuilt_in_the_new_language(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Simplified_Chinese")
        retranslate_ui(window, previous)
        titles = [action.text() for action in window.menu.actions()]
        assert simplified_chinese_word_dict["file_menu_label"] in titles

    def test_the_toolbar_is_rebuilt(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(window, previous)
        assert window.main_toolbar is not None

    def test_a_panel_is_asked_to_relabel_itself(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        panel = MagicMock(spec=["retranslate"])
        holder = QWidget()
        holder.retranslate = panel.retranslate
        window.tab_widget.addTab(holder, "Panel")
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(window, previous)
        panel.retranslate.assert_called_once()

    def test_a_widget_without_one_is_tolerated(self, window, english):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        window.tab_widget.addTab(QWidget(), "Plain")
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(window, previous)
        assert window.tab_widget.count() == 1


class TestChangingLanguageNeedsNoRestart:
    def test_choosing_a_language_relabels_at_once(self, window, english):
        from je_editor.pyside_ui.main_ui.menu.language_menu.build_language_server import (
            set_language
        )
        window.tab_widget.addTab(QWidget(), english_word_dict["tab_name_editor"])
        with patch.dict(
            "je_editor.pyside_ui.main_ui.save_settings.user_setting_file.user_setting_dict",
            {}, clear=False
        ):
            set_language("Simplified_Chinese", window)
        assert window.tab_widget.tabText(0) == \
            simplified_chinese_word_dict["tab_name_editor"]

    def test_the_choice_is_remembered(self, window, english):
        from je_editor.pyside_ui.main_ui.menu.language_menu.build_language_server import (
            set_language
        )
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import (
            user_setting_dict
        )
        saved = user_setting_dict.get("language")
        try:
            set_language("Japanese", window)
            assert user_setting_dict["language"] == "Japanese"
        finally:
            user_setting_dict["language"] = saved


class TestPanelsRelabelThemselves:
    @pytest.mark.parametrize("panel_import,builder", [
        ("je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget:"
         "ProblemsPanelWidget", "problems"),
        ("je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget:"
         "OutlinePanelWidget", "outline"),
    ])
    def test_the_panel_moves_language(self, qapp, qtbot, english, panel_import, builder):
        module_name, class_name = panel_import.split(":")
        module = __import__(module_name, fromlist=[class_name])
        panel = getattr(module, class_name)(main_window=None)
        qtbot.addWidget(panel)
        english_label = panel.refresh_button.text()
        language_wrapper.reset_language("Simplified_Chinese")
        panel.retranslate()
        assert panel.refresh_button.text() != english_label
        panel.close()
