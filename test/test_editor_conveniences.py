"""Tests for macros, surrounding a selection, and saving every tab."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from je_editor.utils.macro.keystroke_macro import MAX_KEYSTROKES, KeystrokeMacro
from je_editor.utils.selection.surround import closing_for, surround


class TestSurroundText:
    @pytest.mark.parametrize("opening,expected", [
        ("(", "(text)"), ("[", "[text]"), ("{", "{text}"),
        ('"', '"text"'), ("'", "'text'"), ("`", "`text`"),
    ])
    def test_pairs(self, opening, expected):
        assert surround("text", opening) == expected

    def test_an_unpaired_character_is_refused(self):
        assert surround("text", "x") is None
        assert closing_for("x") is None

    def test_empty_selection_still_wraps(self):
        assert surround("", "(") == "()"


class TestKeystrokeMacro:
    def test_starts_empty_and_idle(self):
        macro = KeystrokeMacro()
        assert macro.is_empty and macro.recording is False

    def test_recording_collects_keystrokes(self):
        macro = KeystrokeMacro()
        macro.start()
        macro.record(65, 0, "a")
        assert len(macro.keystrokes) == 1

    def test_nothing_is_recorded_while_idle(self):
        macro = KeystrokeMacro()
        assert macro.record(65, 0, "a") is False
        assert macro.is_empty

    def test_toggling_starts_then_stops(self):
        macro = KeystrokeMacro()
        assert macro.toggle() is True
        assert macro.toggle() is False

    def test_a_new_recording_discards_the_previous(self):
        macro = KeystrokeMacro()
        macro.start()
        macro.record(65, 0, "a")
        macro.start()
        assert macro.is_empty

    def test_recording_is_capped(self):
        macro = KeystrokeMacro()
        macro.start()
        for _ in range(MAX_KEYSTROKES + 10):
            macro.record(65, 0, "a")
        assert len(macro.keystrokes) == MAX_KEYSTROKES


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def editor(app):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.close()
    code_editor.deleteLater()


def _select(editor, start: int, end: int) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, cursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestSurroundInEditor:
    def test_typing_a_bracket_over_a_selection_wraps_it(self, editor):
        editor.setPlainText("wrap me\n")
        _select(editor, 0, 4)
        QTest.keyClicks(editor, "(")
        assert editor.toPlainText() == "(wrap) me\n"

    def test_the_wrapped_text_stays_selected(self, editor):
        editor.setPlainText("wrap me\n")
        _select(editor, 0, 4)
        QTest.keyClicks(editor, "[")
        assert editor.textCursor().selectedText() == "wrap"

    def test_wrapping_twice_nests(self, editor):
        editor.setPlainText("word\n")
        _select(editor, 0, 4)
        QTest.keyClicks(editor, "(")
        QTest.keyClicks(editor, '"')
        assert editor.toPlainText() == '("word")\n'

    def test_typing_without_a_selection_inserts_normally(self, editor):
        editor.setPlainText("")
        QTest.keyClicks(editor, "(")
        assert "(" in editor.toPlainText()

    def test_surround_without_a_selection_is_refused(self, editor):
        editor.setPlainText("text")
        assert editor.surround_selection("(") is False


class TestMacroInEditor:
    def test_recording_then_playing_repeats_the_typing(self, editor):
        editor.setPlainText("")
        editor.toggle_macro_recording()
        QTest.keyClicks(editor, "abc")
        editor.toggle_macro_recording()
        editor.play_macro()
        assert editor.toPlainText() == "abcabc"

    def test_playing_while_recording_is_refused(self, editor):
        editor.toggle_macro_recording()
        assert editor.play_macro() is False
        editor.toggle_macro_recording()

    def test_playing_an_empty_macro_is_refused(self, editor):
        editor.macro.stop()
        editor.macro.keystrokes = []
        assert editor.play_macro() is False

    def test_playback_is_one_undo_step(self, editor):
        editor.setPlainText("")
        editor.toggle_macro_recording()
        QTest.keyClicks(editor, "xy")
        editor.toggle_macro_recording()
        before = editor.toPlainText()
        editor.play_macro()
        editor.undo()
        assert editor.toPlainText() == before


class _FakeTabs:
    """Stands in for QTabWidget, which cannot hold a mocked widget."""

    def __init__(self, widgets):
        self._widgets = list(widgets)

    def count(self):
        return len(self._widgets)

    def widget(self, index):
        return self._widgets[index]


def _editor_tab(app, path, text="new content\n"):
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from PySide6.QtWidgets import QPlainTextEdit
    tab = MagicMock(spec=EditorWidget)
    tab.code_edit = QPlainTextEdit()
    tab.code_edit.setPlainText(text)
    tab.current_file = str(path) if path else None
    tab.file_encoding = "utf-8"
    tab.line_ending = "\n"
    return tab


class TestSaveAll:
    def test_every_named_tab_is_written(self, app, tmp_path):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import save_all_tabs
        paths = []
        tabs = []
        for name in ("one.py", "two.py"):
            path = tmp_path / name
            path.write_text("old\n", encoding="utf-8")
            paths.append(path)
            tabs.append(_editor_tab(app, path))
        window = MagicMock()
        window.tab_widget = _FakeTabs(tabs)
        assert save_all_tabs(window) == 2
        assert all(path.read_text(encoding="utf-8") == "new content\n" for path in paths)

    def test_a_tab_without_a_file_is_skipped(self, app):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import save_all_tabs
        window = MagicMock()
        window.tab_widget = _FakeTabs([_editor_tab(app, None)])
        assert save_all_tabs(window) == 0

    def test_the_tab_encoding_is_used(self, app, tmp_path):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import save_all_tabs
        path = tmp_path / "big5.txt"
        tab = _editor_tab(app, path, "中文\n")
        tab.file_encoding = "big5"
        window = MagicMock()
        window.tab_widget = _FakeTabs([tab])
        save_all_tabs(window)
        assert path.read_bytes() == "中文\n".encode("big5")

    def test_a_window_without_tabs(self):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import save_all_tabs
        window = MagicMock()
        window.tab_widget = None
        assert save_all_tabs(window) == 0
