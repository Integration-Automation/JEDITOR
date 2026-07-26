"""Tests for signature help, references, quick fixes and document symbols."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from je_editor.utils.lsp.lsp_protocol import (
    code_action_titles, document_symbols, reference_locations, signature_text
)


class TestSignatureText:
    def test_the_label_is_taken(self):
        result = {"signatures": [{"label": "join(sep: str)"}]}
        assert signature_text(result) == "join(sep: str)"

    def test_the_documentation_follows_the_label(self):
        result = {"signatures": [{"label": "f()", "documentation": "Does a thing"}]}
        assert signature_text(result) == "f()\nDoes a thing"

    def test_markup_documentation_is_unwrapped(self):
        result = {"signatures": [{
            "label": "f()", "documentation": {"kind": "markdown", "value": "Docs"}}]}
        assert signature_text(result) == "f()\nDocs"

    def test_the_active_overload_wins(self):
        result = {"signatures": [{"label": "one"}, {"label": "two"}], "activeSignature": 1}
        assert signature_text(result) == "two"

    def test_an_out_of_range_index_falls_back_to_the_first(self):
        result = {"signatures": [{"label": "one"}], "activeSignature": 9}
        assert signature_text(result) == "one"

    def test_no_signatures_gives_nothing(self):
        assert signature_text({"signatures": []}) == ""

    def test_a_null_result_gives_nothing(self):
        assert signature_text(None) == ""


class TestReferenceLocations:
    def test_each_location_is_read(self):
        result = [
            {"uri": "file:///a.ts", "range": {"start": {"line": 3, "character": 2}}},
            {"uri": "file:///b.ts", "range": {"start": {"line": 9, "character": 0}}},
        ]
        assert [item["line"] for item in reference_locations(result)] == [4, 10]

    def test_the_path_comes_out_of_the_uri(self):
        result = [{"uri": "file:///a.ts", "range": {"start": {"line": 0, "character": 0}}}]
        assert reference_locations(result)[0]["path"].endswith("a.ts")

    def test_an_unreadable_entry_is_skipped(self):
        result = [{"no": "uri"}, {"uri": "file:///a.ts", "range": {"start": {"line": 1}}}]
        assert len(reference_locations(result)) == 1

    def test_a_null_result_gives_nothing(self):
        assert reference_locations(None) == []


class TestCodeActionTitles:
    @staticmethod
    def _action(title: str) -> dict:
        return {
            "title": title,
            "edit": {"changes": {"file:///a.ts": [
                {"range": {"start": {"line": 0, "character": 0},
                           "end": {"line": 0, "character": 1}},
                 "newText": "x"}]}},
        }

    def test_an_action_with_edits_is_offered(self):
        assert [item["title"] for item in code_action_titles([self._action("Add import")])] == \
            ["Add import"]

    def test_the_edits_come_along(self):
        assert code_action_titles([self._action("Fix")])[0]["edits"]

    def test_an_action_without_edits_is_dropped(self):
        # A command-only action needs another round trip, so offering it would
        # give the user a fix that does nothing when pressed.
        assert code_action_titles([{"title": "Run command", "command": "do.thing"}]) == []

    def test_an_action_without_a_title_is_dropped(self):
        action = self._action("")
        assert code_action_titles([action]) == []

    def test_a_null_result_gives_nothing(self):
        assert code_action_titles(None) == []


class TestDocumentSymbols:
    def test_a_flat_symbol_is_read(self):
        result = [{"name": "main", "kind": 12,
                   "range": {"start": {"line": 4, "character": 0}}}]
        assert document_symbols(result) == [
            {"name": "main", "kind": 12, "line": 5, "depth": 0}]

    def test_children_are_flattened_with_their_depth(self):
        result = [{
            "name": "Thing", "kind": 5,
            "selectionRange": {"start": {"line": 1, "character": 0}},
            "children": [{"name": "method", "kind": 6,
                          "selectionRange": {"start": {"line": 2, "character": 4}}}],
        }]
        assert [(item["name"], item["depth"]) for item in document_symbols(result)] == \
            [("Thing", 0), ("method", 1)]

    def test_the_older_format_with_a_location_is_read(self):
        result = [{"name": "helper", "kind": 12,
                   "location": {"uri": "file:///a.ts",
                                "range": {"start": {"line": 7, "character": 0}}}}]
        assert document_symbols(result)[0]["line"] == 8

    def test_an_entry_without_a_name_is_skipped(self):
        assert document_symbols([{"kind": 12}]) == []

    def test_a_null_result_gives_nothing(self):
        assert document_symbols(None) == []


@pytest.fixture()
def client(qapp):
    from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
    from je_editor.pyside_ui.code.lsp.lsp_session import LspSession

    class _FakeSession(LspSession):
        def __init__(self):
            super().__init__(["fake"], "/project")
            self.sent: list = []

        @property
        def running(self) -> bool:
            return True

        def send(self, payload: dict) -> bool:
            self.sent.append(payload)
            return True

        def send_request(self, requester, payload: dict) -> bool:
            return self.send(payload)

    instance = LspClient()
    instance._session = _FakeSession()
    instance._file_path = "/project/a.ts"
    return instance


class TestTheClientAsksForThem:
    def test_signature_help_is_requested(self, client):
        assert client.request_signature_help(1, 2) is True
        assert client._session.sent[-1]["method"] == "textDocument/signatureHelp"

    def test_references_ask_to_include_the_declaration(self, client):
        client.request_references(1, 2)
        assert client._session.sent[-1]["params"]["context"]["includeDeclaration"] is True

    def test_code_actions_carry_the_diagnostics(self, client):
        client.request_code_actions(1, 2, [{"message": "unused"}])
        context = client._session.sent[-1]["params"]["context"]
        assert context["diagnostics"] == [{"message": "unused"}]

    def test_document_symbols_are_requested(self, client):
        assert client.request_document_symbols() is True
        assert client._session.sent[-1]["method"] == "textDocument/documentSymbol"

    def test_nothing_is_requested_without_a_file(self, qapp):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        assert LspClient().request_document_symbols() is False


class TestTheClientReportsTheReplies:
    def test_a_signature_reaches_the_editor(self, client):
        client.request_signature_help(0, 0)
        received: list = []
        client.signature_ready.connect(received.append)
        client.handle_message({
            "id": client._pending_signature_id,
            "result": {"signatures": [{"label": "f()"}]},
        })
        assert received == ["f()"]

    def test_references_reach_the_editor(self, client):
        client.request_references(0, 0)
        received: list = []
        client.references_ready.connect(received.append)
        client.handle_message({
            "id": client._pending_references_id,
            "result": [{"uri": "file:///a.ts", "range": {"start": {"line": 2}}}],
        })
        assert received[0][0]["line"] == 3

    def test_a_stale_reply_is_ignored(self, client):
        client.request_references(0, 0)
        received: list = []
        client.references_ready.connect(received.append)
        client.handle_message({"id": 999, "result": [
            {"uri": "file:///a.ts", "range": {"start": {"line": 2}}}]})
        assert received == []

    def test_symbols_reach_the_editor(self, client):
        client.request_document_symbols()
        received: list = []
        client.symbols_ready.connect(received.append)
        client.handle_message({
            "id": client._pending_symbol_id,
            "result": [{"name": "main", "range": {"start": {"line": 0}}}],
        })
        assert received[0][0]["name"] == "main"


@pytest.fixture()
def editor(qapp, qtbot):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    qtbot.addWidget(code_editor)
    return code_editor


class TestReachingSignatureHelp:
    """
    A signature is only useful while the arguments are being typed, so typing is
    what asks for it; nothing called it before, which made the whole feature
    unreachable.
    """

    @staticmethod
    def _with_a_server(editor):
        """Stand a running client in for the real one, for this test only."""
        client = MagicMock()
        client.running = True
        client.request_signature_help.return_value = True
        return patch.object(editor, "lsp_client", client)

    def test_an_opening_bracket_asks_for_one(self, editor):
        with self._with_a_server(editor):
            assert editor._maybe_show_signature("(") is True

    def test_a_comma_asks_for_one(self, editor):
        with self._with_a_server(editor):
            assert editor._maybe_show_signature(",") is True

    def test_an_ordinary_character_does_not(self, editor):
        with self._with_a_server(editor):
            assert editor._maybe_show_signature("x") is False

    def test_nothing_is_asked_without_a_server(self, editor):
        assert editor._maybe_show_signature("(") is False

    def test_typing_a_bracket_reaches_the_server(self, editor):
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        with self._with_a_server(editor):
            QTest.keyClick(editor, Qt.Key.Key_ParenLeft)
            assert editor.lsp_client.request_signature_help.called

    def test_the_context_menu_offers_it(self, editor):
        from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
        with self._with_a_server(editor):
            menu = editor.build_context_menu()
        labels = [action.text() for action in menu.actions()]
        assert language_wrapper.language_word_dict.get("context_menu_signature_help") in labels
        menu.deleteLater()


class TestTheEditorUsesThem:
    def test_a_signature_is_shown(self, editor):
        editor.show_signature_text("join(sep: str)")
        assert editor.toolTip() == "join(sep: str)"

    def test_no_references_means_nothing_to_show(self, editor):
        assert editor.show_references([]) is False

    def test_no_fixes_means_nothing_to_show(self, editor):
        assert editor.show_quick_fixes([]) is False

    def test_the_diagnostics_for_a_line_are_kept_as_the_server_sent_them(self, editor):
        # A fix request has to hand the server its own objects back: the
        # editor's converted form does not even count lines the same way.
        first = {"range": {"start": {"line": 2, "character": 0}}, "message": "unused"}
        second = {"range": {"start": {"line": 5, "character": 0}}, "message": "other"}
        editor.lsp_client.handle_message({
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": "file:///a.ts", "diagnostics": [first, second]},
        })
        assert editor.lsp_client.diagnostics_on_line(2) == [first]

    def test_a_line_without_diagnostics_has_none(self, editor):
        editor.lsp_client.handle_message({
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": "file:///a.ts", "diagnostics": []},
        })
        assert editor.lsp_client.diagnostics_on_line(2) == []
