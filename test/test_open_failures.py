"""開檔失敗時要說出來，而且之後還開得了 / A failed open is reported, and the file can still be opened later."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QTabWidget  # noqa: E402

from je_editor.pyside_ui.code.auto_save.auto_save_manager import file_is_open_manager_dict  # noqa: E402
from je_editor.utils.exception.exceptions import JEditorOpenFileException  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def warnings(monkeypatch):
    shown: list = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: shown.append(a[2])))
    return shown


@pytest.fixture()
def editor(app):
    main = MagicMock()
    main.working_dir = None
    main.tab_widget = QTabWidget()
    main.python_compiler = None
    with patch("je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check") as venv:
        venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        widget = EditorWidget(main)
        main.tab_widget.addTab(widget, "Test")
    yield widget
    widget.close()
    widget.deleteLater()


def _unreadable(monkeypatch):
    """讓讀檔像檔案被鎖住一樣失敗 / Make reading fail as for a locked file."""
    from je_editor.pyside_ui.main_ui.editor import editor_widget

    def refuse(*_args, **_kwargs):
        raise JEditorOpenFileException from PermissionError(13, "the file is locked")

    monkeypatch.setattr(editor_widget, "read_file_with_encoding", refuse)


class TestOpeningAFileThatCannotBeRead:
    def test_the_user_is_told(self, editor, tmp_path, monkeypatch, warnings):
        target = tmp_path / "locked.py"
        target.write_text("x = 1\n", encoding="utf-8")
        _unreadable(monkeypatch)

        assert editor.open_an_file(target) is False
        assert warnings and "locked.py" in warnings[0]

    def test_it_can_be_opened_once_it_is_readable(self, editor, tmp_path, monkeypatch, warnings):
        target = tmp_path / "later.py"
        target.write_text("x = 1\n", encoding="utf-8")
        _unreadable(monkeypatch)
        editor.open_an_file(target)
        monkeypatch.undo()

        # 以前檔案已經被記成「已開啟」：下一次什麼都不做
        # It used to stay recorded as open, and the next try did nothing
        assert str(target) not in file_is_open_manager_dict
        assert editor.open_an_file(target) is True
        assert editor.code_edit.toPlainText() == "x = 1\n"
        file_is_open_manager_dict.pop(str(target), None)


class TestAStaleOpenRecord:
    def test_a_record_with_no_tab_does_not_stop_the_open(self, editor, tmp_path):
        target = tmp_path / "stale.py"
        target.write_text("y = 2\n", encoding="utf-8")
        file_is_open_manager_dict[str(target)] = str(target)

        # 以前第一次回傳 None：開檔什麼都不做 / It returned None the first time: nothing opened
        assert editor.open_an_file(target) is True
        file_is_open_manager_dict.pop(str(target), None)


class TestFileOpenDialog:
    def test_a_file_in_another_encoding_keeps_it(self, editor, tmp_path, monkeypatch):
        from je_editor.pyside_ui.dialog.file_dialog import open_file_dialog

        # 以前只用 UTF-8 讀：這個檔案從選單丟出例外，而且之後再也開不了
        # It was read as UTF-8 only: this raised out of the menu, and the file
        # could not be opened again
        target = tmp_path / "latin.txt"
        target.write_bytes("café\r\nnaïve\r\n".encode("latin-1"))
        window = MagicMock()
        window.tab_widget.currentWidget.return_value = editor
        monkeypatch.setattr(open_file_dialog, "_prompt_for_file", lambda _window: str(target))
        monkeypatch.setattr(
            "je_editor.pyside_ui.main_ui.menu.file_menu.build_file_menu.add_to_recent_files",
            lambda _path: None)

        open_file_dialog.choose_file_get_open_file_path(window)

        assert editor.code_edit.toPlainText() == "café\nnaïve\n"
        assert editor.file_encoding == "latin-1"
        assert editor.line_ending == "\r\n"
        assert Path(editor.current_file) == target
        file_is_open_manager_dict.pop(str(target), None)


class TestANewTabThatCannotOpen:
    def test_no_empty_tab_is_left(self, app, tmp_path, monkeypatch, warnings):
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain

        target = tmp_path / "locked.py"
        target.write_text("x = 1\n", encoding="utf-8")
        window = MagicMock()
        window.tab_widget = QTabWidget()
        editor = MagicMock()
        editor.open_an_file.return_value = False
        monkeypatch.setattr(
            "je_editor.pyside_ui.main_ui.main_editor.EditorWidget", lambda _main: editor)
        monkeypatch.setattr(QTabWidget, "addTab", lambda self, *_a: 0)
        removed: list = []
        monkeypatch.setattr(QTabWidget, "removeTab", lambda self, index: removed.append(index))
        monkeypatch.setattr(QTabWidget, "indexOf", lambda self, _widget: 0)
        monkeypatch.setattr(QTabWidget, "setCurrentWidget", lambda self, _widget: None)

        EditorMain.go_to_new_tab(window, target)

        assert removed == [0]
        editor.close.assert_called_once()
