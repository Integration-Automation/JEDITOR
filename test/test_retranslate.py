"""Tests that changing the language relabels the interface without a restart."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QMainWindow, QMenu, QMenuBar, QTabWidget, QWidget

from je_editor.utils.multi_language.english import english_word_dict
from je_editor.utils.multi_language.japanese import japanese_word_dict
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.multi_language.retranslate_text import (
    TITLE_KEYS, family_of, key_for_text, keys_in_family, menu_candidates,
    translated_again
)
from je_editor.utils.multi_language.simplified_chinese import simplified_chinese_word_dict
from je_editor.utils.multi_language.traditional_chinese import traditional_chinese_word_dict


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


class TestNarrowingTheLookupToMenus:
    """
    One English word is often several keys at once, and they need not agree in
    another language: 'Run' is a menu title, a console button and a toolbar tip.
    """

    def test_a_menu_key_is_a_candidate(self):
        assert "run_menu_label" in menu_candidates(english_word_dict)

    def test_a_column_heading_is_not(self):
        assert "search_replace_col_text" not in menu_candidates(english_word_dict)

    def test_the_menu_title_wins_over_a_button_of_the_same_name(self):
        key = key_for_text("Run", english_word_dict, menu_candidates(english_word_dict))
        assert english_word_dict[key] == "Run"
        assert traditional_chinese_word_dict[key] == \
            traditional_chinese_word_dict["run_menu_label"]

    def test_a_family_keeps_its_own_keys(self):
        keys = keys_in_family(english_word_dict, "tab")
        assert "tab_menu_editor_tab_name" in keys
        assert "dock_editor_menu" not in keys

    def test_no_family_means_every_key(self):
        assert len(keys_in_family(english_word_dict, "")) == len(english_word_dict)

    def test_the_family_is_the_first_segment(self):
        assert family_of("tab_menu_editor_tab_name") == "tab"

    def test_nothing_has_no_family(self):
        assert family_of(None) == ""

    def test_the_tab_menu_editor_is_told_from_the_dock_menu_one(self):
        # Both read "Editor" in English, and only one of them is translated.
        in_tab = key_for_text(
            "Editor", english_word_dict, keys_in_family(english_word_dict, "tab"))
        in_dock = key_for_text(
            "Editor", english_word_dict, keys_in_family(english_word_dict, "dock"))
        assert japanese_word_dict[in_tab] != japanese_word_dict.get(in_dock, "Editor")


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


def build_menus_and_toolbar(main_window) -> None:
    """Give a bare window the menu bar and toolbar a real one has."""
    from je_editor.pyside_ui.main_ui.menu.set_menu_bar import set_menu_bar
    from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import build_toolbar
    set_menu_bar(main_window)
    build_toolbar(main_window)


def menu_tree(menu_bar) -> list:
    """Every label on a menu bar, in order and with its depth."""
    def walk(actions, depth):
        rows = []
        for action in actions:
            rows.append(("  " * depth) + action.text())
            submenu = submenus.get(action)
            if submenu is not None:
                rows.extend(walk(submenu.actions(), depth + 1))
        return rows
    # Asking a QAction for its menu hands that menu to Python to delete, which
    # is the very fault these tests exist for; the children are safe to ask.
    submenus = {menu.menuAction(): menu for menu in menu_bar.findChildren(QMenu)}
    return walk(menu_bar.actions(), 0)


@pytest.fixture()
def full_window(window, english):
    """A window carrying the real menu bar and toolbar, built in English."""
    build_menus_and_toolbar(window)
    return window


@pytest.fixture()
def window_factory(qtbot):
    """Make further bare windows, for comparing against a fresh build."""
    from PySide6.QtGui import QFontDatabase

    def make() -> QMainWindow:
        main_window = QMainWindow()
        qtbot.addWidget(main_window)
        main_window.menu = QMenuBar()
        main_window.font_database = QFontDatabase()
        main_window.tab_widget = QTabWidget()
        main_window.setCentralWidget(main_window.tab_widget)
        main_window.encoding = "utf-8"
        return main_window

    return make


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

    def test_the_menu_bar_moves_to_the_new_language(self, full_window):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Simplified_Chinese")
        retranslate_ui(full_window, previous)
        titles = [action.text() for action in full_window.menu.actions()]
        assert simplified_chinese_word_dict["file_menu_label"] in titles

    def test_the_toolbar_moves_to_the_new_language(self, full_window):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(full_window, previous)
        tips = [action.toolTip() for action in full_window.main_toolbar.actions()]
        assert japanese_word_dict["toolbar_run"] in tips

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


class TestNothingIsDestroyedByALanguageChange:
    """
    Relabelling used to mean rebuilding the menu bar, and ``setMenuBar`` deletes
    the outgoing bar with every menu on it. An application embedding this window
    adds its menus to that same bar: they disappeared, and the references it kept
    became pointers to deleted objects, which crash as soon as one is followed.
    """

    @staticmethod
    def switch_to(window, language: str) -> None:
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language(language)
        retranslate_ui(window, previous)

    def test_the_menu_bar_is_the_same_object_afterwards(self, full_window):
        before = full_window.menuBar()
        self.switch_to(full_window, "Japanese")
        assert full_window.menuBar() is before

    def test_every_menu_is_still_alive(self, full_window):
        menus = full_window.menuBar().findChildren(QMenu)
        assert menus, "the window should have menus to begin with"
        self.switch_to(full_window, "Japanese")
        for menu in menus:
            menu.title()  # raises RuntimeError once the C++ object is gone

    def test_the_windows_own_menu_references_stay_usable(self, full_window):
        self.switch_to(full_window, "Simplified_Chinese")
        assert full_window.file_menu.actions()
        assert full_window.dock_menu.actions()

    def test_a_menu_added_by_an_embedding_application_survives(self, full_window):
        # What PyBreeze does: its own menus go on the same bar as ours.
        extra = full_window.menuBar().addMenu("Automation")
        extra.addAction("Run task")
        self.switch_to(full_window, "Japanese")
        assert extra.title() == "Automation"
        assert extra.menuAction() in full_window.menuBar().actions()

    def test_the_toolbar_is_the_same_object_afterwards(self, full_window):
        before = full_window.main_toolbar
        self.switch_to(full_window, "Japanese")
        assert full_window.main_toolbar is before


class TestRelabellingMatchesABuildInThatLanguage:
    """
    The wording has to end up exactly where a fresh build would put it, or
    relabelling in place would be trading a crash for a half-translated window.
    """

    @pytest.mark.parametrize(
        "language", ["Traditional_Chinese", "Simplified_Chinese", "Japanese"])
    def test_the_menus_read_the_same(self, full_window, window_factory, language):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language(language)
        retranslate_ui(full_window, previous)

        built = window_factory()
        build_menus_and_toolbar(built)
        assert menu_tree(full_window.menuBar()) == menu_tree(built.menuBar())

    def test_the_toolbar_tips_read_the_same(self, full_window, window_factory):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(full_window, previous)

        built = window_factory()
        build_menus_and_toolbar(built)
        assert [action.toolTip() for action in full_window.main_toolbar.actions()] == \
            [action.toolTip() for action in built.main_toolbar.actions()]


class TestNamesAreNotTranslated:
    """
    Some menus list names rather than wording: font families, the languages
    themselves. Translating those would name a font nobody has installed, or
    hide a language from the person looking for it.
    """

    @staticmethod
    def labels(menu) -> list:
        return [action.text() for action in menu.actions()]

    def test_font_families_keep_their_names(self, full_window):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        before = self.labels(full_window.file_menu.font_menu)
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(full_window, previous)
        assert self.labels(full_window.file_menu.font_menu) == before

    def test_each_language_stays_written_the_way_it_writes_itself(self, full_window):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        before = self.labels(full_window.language_menu)
        assert "English" in before
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(full_window, previous)
        assert self.labels(full_window.language_menu) == before

    def test_the_line_shown_when_there_are_no_recent_files_does_move(self, full_window):
        from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
        menu = full_window.file_menu.recent_files_menu
        if self.labels(menu) != [english_word_dict["file_menu_no_recent_files"]]:
            pytest.skip("this run has recent files, which are paths and never move")
        previous = dict(language_wrapper.language_word_dict)
        language_wrapper.reset_language("Japanese")
        retranslate_ui(full_window, previous)
        assert self.labels(menu) == [japanese_word_dict["file_menu_no_recent_files"]]


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
