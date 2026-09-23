"""存檔失敗時要說出來、不能弄壞任何東西 / A save that fails is reported and breaks nothing."""
from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QPlainTextEdit  # noqa: E402

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def warnings(monkeypatch):
    shown: list = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: shown.append(a[2])))
    return shown


def _tab(path, text="new content\n", encoding="utf-8"):
    tab = MagicMock(spec=EditorWidget)
    tab.code_edit = QPlainTextEdit()
    tab.code_edit.setPlainText(text)
    tab.current_file = str(path) if path else None
    tab.file_encoding = encoding
    tab.line_ending = "\n"
    return tab


class _Tabs:
    def __init__(self, widgets):
        self._widgets = list(widgets)

    def count(self):
        return len(self._widgets)

    def widget(self, index):
        return self._widgets[index]


class TestSaveAs:
    def test_a_failed_write_is_reported_and_the_tab_keeps_its_file(
            self, app, tmp_path, monkeypatch, warnings):
        from je_editor.pyside_ui.dialog.file_dialog import save_file_dialog

        # 以前例外從選單丟出去，而且分頁已經改指向沒寫成的新路徑
        # It used to raise out of the menu, with the tab already pointing at the
        # path that was never written
        original = tmp_path / "original.txt"
        tab = _tab(original, "€ is not in Big5\n", encoding="big5")
        window = MagicMock()
        window.tab_widget.currentWidget.return_value = tab
        target = tmp_path / "copy.txt"
        monkeypatch.setattr(
            save_file_dialog, "QFileDialog",
            lambda: MagicMock(getSaveFileName=lambda **_k: (str(target), "")))

        assert save_file_dialog.choose_file_get_save_file_path(window) is False
        assert tab.current_file == str(original)
        assert warnings and "copy.txt" in warnings[0]
        tab.mark_saved.assert_not_called()


class TestSaveAll:
    def test_one_tab_that_fails_does_not_stop_the_rest(self, app, tmp_path):
        from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import save_all_tabs

        bad = _tab(tmp_path / "bad.txt", "€\n", encoding="big5")
        good_path = tmp_path / "good.txt"
        good = _tab(good_path)
        window = MagicMock()
        window.tab_widget = _Tabs([bad, good])
        failures: list = []

        assert save_all_tabs(window, failures) == 1
        assert good_path.read_text(encoding="utf-8") == "new content\n"
        assert [file for file, _error in failures] == [str(tmp_path / "bad.txt")]

    def test_the_menu_reports_every_tab_it_could_not_save(self, app, tmp_path, warnings):
        from je_editor.pyside_ui.main_ui.menu.file_menu.build_file_menu import _save_all_and_report

        window = MagicMock()
        window.tab_widget = _Tabs([_tab(tmp_path / "bad.txt", "€\n", encoding="big5")])

        _save_all_and_report(window)

        assert len(warnings) == 1 and "bad.txt" in warnings[0]


class TestAutoSave:
    def test_a_failed_write_does_not_end_the_thread(self, app, tmp_path):
        from je_editor.pyside_ui.code.auto_save.auto_save_thread import CodeEditSaveThread

        # 以前 JEditorSaveFileException 沒被接住，執行緒結束，之後再也不自動儲存
        # The exception used to escape and end the thread for good
        thread = CodeEditSaveThread(file_to_save=str(tmp_path / "big5.txt"))
        thread.encoding = "big5"
        thread._get_editor_text = lambda: "€\n"

        thread._attempt_save()  # must not raise


class TestTheEditorDock:
    @staticmethod
    def _dock(path, encoding, line_ending, text):
        from je_editor.pyside_ui.main_ui.editor.editor_widget_dock import FullEditorWidget

        widget = FullEditorWidget(current_file=str(path), encoding=encoding, line_ending=line_ending)
        widget.code_edit.setPlainText(text)
        widget.code_edit.document().setModified(False)
        return widget

    def test_closing_it_unedited_leaves_the_file_alone(self, app, tmp_path):
        # 以前沒改也以 UTF-8 與系統行尾寫回，LF 檔被改成 CRLF
        # Unedited, it used to be written back as UTF-8 with the platform's endings
        path = tmp_path / "unix.txt"
        path.write_bytes(b"a\nb\n")
        widget = self._dock(path, "utf-8", "\n", "a\nb\n")

        widget.close()

        assert path.read_bytes() == b"a\nb\n"

    def test_an_edit_is_saved_in_the_files_encoding_and_line_ending(self, app, tmp_path):
        path = tmp_path / "big5.txt"
        path.write_bytes("舊\r\n".encode("big5"))
        widget = self._dock(path, "big5", "\r\n", "舊\n")
        widget.code_edit.textCursor().insertText("新")

        widget.close()

        assert path.read_bytes() == "新舊\r\n".encode("big5")

    def test_a_save_on_close_that_fails_is_reported(self, app, tmp_path, warnings):
        path = tmp_path / "big5.txt"
        path.write_bytes("舊\n".encode("big5"))
        widget = self._dock(path, "big5", "\n", "舊\n")
        widget.code_edit.textCursor().insertText("€")

        widget.close()

        assert path.read_bytes() == "舊\n".encode("big5")
        assert warnings and "big5.txt" in warnings[0]

    def test_the_menu_opens_the_file_with_its_encoding(self, app, tmp_path, monkeypatch):
        from je_editor.pyside_ui.main_ui.menu.dock_menu import build_dock_menu

        path = tmp_path / "windows.txt"
        path.write_bytes(b"a\r\nb\r\n")
        monkeypatch.setattr(
            build_dock_menu, "QFileDialog",
            lambda: MagicMock(getOpenFileName=lambda **_k: (str(path), "")))
        dock = MagicMock()

        assert build_dock_menu._make_editor_dock(MagicMock(), dock) is True
        widget = dock.setWidget.call_args[0][0]
        assert widget.line_ending == "\r\n"
        assert widget.code_edit.toPlainText() == "a\nb\n"
        assert not widget.code_edit.document().isModified()
        widget.close()
        assert path.read_bytes() == b"a\r\nb\r\n"
