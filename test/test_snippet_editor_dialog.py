"""Tests for the snippet editor dialog."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def dialog(app, tmp_path):
    from je_editor.pyside_ui.dialog.snippet_dialog.snippet_editor_dialog import (
        SnippetEditorDialog
    )
    path = tmp_path / "snippets.json"
    with patch(
        "je_editor.pyside_ui.code.snippets.snippet_manager.snippet_file_path",
        return_value=path,
    ):
        window = MagicMock()
        window.tab_widget = None
        editor = SnippetEditorDialog(window)
        editor._test_path = path
        yield editor
    editor.close()
    editor.deleteLater()


class TestSnippetEditorDialog:
    def test_the_built_in_snippets_are_listed(self, dialog):
        triggers = [
            dialog.trigger_list.item(row).text()
            for row in range(dialog.trigger_list.count())
        ]
        assert "def" in triggers and "for" in triggers

    def test_selecting_a_trigger_shows_its_body(self, dialog):
        row = [
            index for index in range(dialog.trigger_list.count())
            if dialog.trigger_list.item(index).text() == "for"
        ][0]
        dialog.trigger_list.setCurrentRow(row)
        assert "in" in dialog.body_edit.toPlainText()

    def test_adding_creates_a_new_trigger(self, dialog):
        before = dialog.trigger_list.count()
        trigger = dialog.add_snippet()
        assert dialog.trigger_list.count() == before + 1
        assert trigger in dialog.snippets()

    def test_adding_twice_does_not_overwrite(self, dialog):
        first = dialog.add_snippet()
        second = dialog.add_snippet()
        assert first != second

    def test_editing_a_body_is_kept(self, dialog):
        trigger = dialog.add_snippet()
        dialog.body_edit.setPlainText("changed $0")
        dialog.add_snippet()  # moving away keeps the edited body
        assert dialog.snippets()[trigger] == "changed $0"

    def test_removing_takes_it_out_of_the_list(self, dialog):
        trigger = dialog.add_snippet()
        assert dialog.remove_snippet() is True
        assert trigger not in dialog.snippets()

    def test_removing_without_a_selection_is_refused(self, dialog):
        dialog.trigger_list.setCurrentRow(-1)
        assert dialog.remove_snippet() is False

    def test_saving_writes_the_file(self, dialog):
        with patch(
            "je_editor.pyside_ui.code.snippets.snippet_manager.snippet_file_path",
            return_value=dialog._test_path,
        ):
            trigger = dialog.add_snippet()
            dialog.body_edit.setPlainText("saved body $0")
            assert dialog.save() is True
        assert trigger in dialog._test_path.read_text(encoding="utf-8")
