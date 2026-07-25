"""Tests for the LSP wire protocol, the server registry, and the client."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.lsp.language_servers import (
    DEFAULT_SERVERS,
    language_id,
    merge_servers,
    server_command,
)
from je_editor.utils.lsp.lsp_protocol import (
    MessageReader,
    completion_labels,
    diagnostic_entries,
    encode_message,
    file_uri,
    notification,
    request,
)


class TestEncoding:
    def test_message_starts_with_a_content_length(self):
        encoded = encode_message({"jsonrpc": "2.0", "method": "ping"})
        assert encoded.startswith(b"Content-Length: ")

    def test_length_matches_the_body(self):
        encoded = encode_message({"method": "ping"})
        header, body = encoded.split(b"\r\n\r\n", 1)
        declared = int(header.split(b":")[1].strip())
        assert declared == len(body)

    def test_body_is_the_json_payload(self):
        encoded = encode_message({"method": "ping", "id": 3})
        body = encoded.split(b"\r\n\r\n", 1)[1]
        assert json.loads(body) == {"method": "ping", "id": 3}

    def test_non_ascii_survives(self):
        encoded = encode_message({"text": "中文"})
        body = encoded.split(b"\r\n\r\n", 1)[1]
        assert json.loads(body)["text"] == "中文"


class TestMessageReader:
    def test_one_whole_message(self):
        reader = MessageReader()
        assert reader.feed(encode_message({"id": 1})) == [{"id": 1}]

    def test_two_messages_in_one_read(self):
        reader = MessageReader()
        data = encode_message({"id": 1}) + encode_message({"id": 2})
        assert [message["id"] for message in reader.feed(data)] == [1, 2]

    def test_a_message_split_across_reads(self):
        reader = MessageReader()
        encoded = encode_message({"id": 7})
        assert reader.feed(encoded[:10]) == []
        assert reader.feed(encoded[10:]) == [{"id": 7}]

    def test_a_body_split_from_its_header(self):
        reader = MessageReader()
        header, body = encode_message({"id": 9}).split(b"\r\n\r\n", 1)
        assert reader.feed(header + b"\r\n\r\n") == []
        assert reader.feed(body) == [{"id": 9}]

    def test_pending_bytes_are_reported(self):
        reader = MessageReader()
        reader.feed(encode_message({"id": 1})[:8])
        assert reader.pending_bytes > 0

    def test_a_body_that_is_not_json_is_dropped(self):
        reader = MessageReader()
        broken = b"Content-Length: 5\r\n\r\nnotjs"
        assert reader.feed(broken) == []

    def test_a_header_without_a_length_is_skipped(self):
        reader = MessageReader()
        data = b"Bad-Header: 1\r\n\r\n" + encode_message({"id": 4})
        assert reader.feed(data) == [{"id": 4}]

    def test_empty_feed(self):
        assert MessageReader().feed(b"") == []


class TestMessageBuilders:
    def test_request_has_an_id(self):
        assert request(5, "textDocument/completion")["id"] == 5

    def test_notification_has_no_id(self):
        assert "id" not in notification("initialized")

    def test_posix_file_uri(self):
        assert file_uri("/home/user/app.ts") == "file:///home/user/app.ts"

    def test_windows_file_uri(self):
        assert file_uri("D:\\project\\app.ts") == "file:///D:/project/app.ts"


class TestResultParsing:
    def test_completion_list_form(self):
        assert completion_labels([{"label": "alpha"}, {"label": "beta"}]) == ["alpha", "beta"]

    def test_completion_items_form(self):
        assert completion_labels({"items": [{"label": "gamma"}]}) == ["gamma"]

    def test_plain_string_items(self):
        assert completion_labels(["delta"]) == ["delta"]

    def test_duplicates_are_dropped(self):
        assert completion_labels([{"label": "same"}, {"label": "same"}]) == ["same"]

    def test_unusable_result(self):
        assert completion_labels(None) == []
        assert completion_labels({"unexpected": 1}) == []

    def test_diagnostics_are_converted_to_one_based_lines(self):
        entries = diagnostic_entries({"diagnostics": [
            {"range": {"start": {"line": 4, "character": 2}}, "message": "boom"}]})
        assert entries == [{"line": 5, "column": 3, "message": "boom"}]

    def test_diagnostics_without_a_message_are_skipped(self):
        assert diagnostic_entries({"diagnostics": [{"range": {}}]}) == []

    def test_unusable_diagnostics_params(self):
        assert diagnostic_entries(None) == []


class TestServerRegistry:
    def test_python_is_not_served_by_lsp(self):
        # Python keeps jedi; two completion sources for one file helps nobody.
        assert ".py" not in DEFAULT_SERVERS

    def test_known_suffixes_have_commands(self):
        assert DEFAULT_SERVERS[".ts"][0] == "typescript-language-server"

    def test_user_servers_override_the_defaults(self):
        merged = merge_servers({".ts": ["my-server", "--stdio"], ".zig": ["zls"]})
        assert merged[".ts"] == ["my-server", "--stdio"]
        assert merged[".zig"] == ["zls"]

    def test_hand_edited_entries_are_skipped(self):
        merged = merge_servers({"ts": ["no-dot"], ".x": "not-a-list", ".y": []})
        assert "ts" not in merged and ".x" not in merged and ".y" not in merged

    def test_non_dict_falls_back(self):
        assert merge_servers("nonsense")[".go"] == ["gopls"]

    def test_an_uninstalled_server_is_not_offered(self):
        with patch("je_editor.utils.lsp.language_servers.shutil.which", return_value=None):
            assert server_command(".ts") is None

    def test_an_installed_server_is_offered(self):
        with patch(
            "je_editor.utils.lsp.language_servers.shutil.which", return_value="/usr/bin/x"
        ):
            assert server_command(".ts")[0] == "typescript-language-server"

    def test_an_unknown_suffix_has_no_server(self):
        assert server_command(".unknownsuffix") is None

    def test_language_ids(self):
        assert language_id(".ts") == "typescript"
        assert language_id(".RS") == "rust"

    def test_unknown_language_id_falls_back_to_the_suffix(self):
        assert language_id(".zig") == "zig"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class TestLspClient:
    def test_starts_stopped(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        assert client.running is False
        client.stop()

    def test_a_missing_server_does_not_start(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        with patch("je_editor.pyside_ui.code.lsp.lsp_client.server_command", return_value=None):
            assert client.start_for("app.ts") is False
        client.stop()

    def test_sending_without_a_server_is_refused(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        assert client.did_open("text") is False
        assert client.request_completion(0, 0) is False
        client.stop()

    def test_completion_results_are_emitted(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        received = []
        client.completions_ready.connect(received.append)
        client._pending_completion_id = 12
        client.handle_message({"id": 12, "result": [{"label": "answer"}]})
        assert received == [["answer"]]
        client.stop()

    def test_a_reply_to_another_request_is_ignored(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        received = []
        client.completions_ready.connect(received.append)
        client._pending_completion_id = 12
        client.handle_message({"id": 99, "result": [{"label": "stale"}]})
        assert received == []
        client.stop()

    def test_diagnostics_are_emitted(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        received = []
        client.diagnostics_ready.connect(received.append)
        client.handle_message({
            "method": "textDocument/publishDiagnostics",
            "params": {"diagnostics": [
                {"range": {"start": {"line": 0, "character": 0}}, "message": "oops"}]},
        })
        assert received[0][0]["message"] == "oops"
        client.stop()

    def test_stopping_twice_is_safe(self, app):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        client = LspClient()
        client.stop()
        client.stop()


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
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.blame_manager.stop()
    code_editor.lsp_client.stop()
    code_editor.close()
    code_editor.deleteLater()


class TestEditorIntegration:
    def test_python_files_start_no_server(self, editor):
        editor.current_file = "module.py"
        assert editor.start_language_server() is False

    def test_a_file_without_a_server_starts_none(self, editor):
        editor.current_file = "notes.unknownsuffix"
        assert editor.start_language_server() is False

    def test_no_file_starts_none(self, editor):
        editor.current_file = None
        assert editor.start_language_server() is False

    def test_completion_falls_back_to_jedi_without_a_server(self, editor):
        assert editor.request_language_server_completion() is False
