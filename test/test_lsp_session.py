"""Tests that one language server is shared rather than started per editor."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from je_editor.pyside_ui.code.lsp.lsp_session import LspSession, LspSessionRegistry


class _FakeSession(LspSession):
    """A session that records what it would have sent, without a process."""

    def __init__(self, command=None, root="/project"):
        super().__init__(command or ["fake-server"], root)
        self.sent: list = []
        self.started = False

    def start(self, root_uri: str) -> bool:
        self.started = True
        return True

    @property
    def running(self) -> bool:
        return self.started

    def send(self, payload: dict) -> bool:
        self.sent.append(payload)
        return True


class TestRoutingMessages:
    """Two files share one process, so each reply has to find its own file."""

    def test_a_reply_goes_to_the_client_that_asked(self):
        session = _FakeSession()
        asker, other = MagicMock(), MagicMock()
        session.send_request(asker, {"id": 1, "method": "textDocument/hover"})
        session.route({"id": 1, "result": {}})
        asker.handle_message.assert_called_once()
        other.handle_message.assert_not_called()

    def test_a_reply_is_only_delivered_once(self):
        session = _FakeSession()
        asker = MagicMock()
        session.send_request(asker, {"id": 1, "method": "textDocument/hover"})
        session.route({"id": 1, "result": {}})
        session.route({"id": 1, "result": {}})
        assert asker.handle_message.call_count == 1

    def test_a_reply_nobody_asked_for_is_dropped(self):
        session = _FakeSession()
        assert session.route({"id": 99, "result": {}}) is None

    def test_diagnostics_go_to_the_file_they_name(self):
        session = _FakeSession()
        first, second = MagicMock(), MagicMock()
        session.register_document("file:///a.ts", first)
        session.register_document("file:///b.ts", second)
        session.route({
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": "file:///b.ts", "diagnostics": []},
        })
        second.handle_message.assert_called_once()
        first.handle_message.assert_not_called()

    def test_diagnostics_for_an_unopened_file_are_dropped(self):
        session = _FakeSession()
        assert session.route({
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": "file:///gone.ts"},
        }) is None

    def test_request_ids_do_not_repeat(self):
        session = _FakeSession()
        assert session.take_id() != session.take_id()


class TestSharingASession:
    @staticmethod
    def _registry():
        registry = LspSessionRegistry()
        return registry

    def test_two_files_of_one_language_share_a_session(self):
        registry = self._registry()
        with patch(
            "je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession
        ):
            first = registry.session_for(["fake-server"], "/project", "file:///project")
            second = registry.session_for(["fake-server"], "/project", "file:///project")
        assert first is second

    def test_a_different_language_gets_its_own(self):
        registry = self._registry()
        with patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession):
            first = registry.session_for(["ts-server"], "/project", "file:///project")
            second = registry.session_for(["rs-server"], "/project", "file:///project")
        assert first is not second

    def test_a_different_project_gets_its_own(self):
        registry = self._registry()
        with patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession):
            first = registry.session_for(["fake-server"], "/one", "file:///one")
            second = registry.session_for(["fake-server"], "/two", "file:///two")
        assert first is not second

    def test_a_server_that_will_not_start_gives_nothing(self):
        registry = self._registry()

        class _Dead(_FakeSession):
            def start(self, root_uri: str) -> bool:
                return False

        with patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _Dead):
            assert registry.session_for(["fake"], "/p", "file:///p") is None

    def test_a_session_still_in_use_is_not_shut_down(self):
        registry = self._registry()
        with patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession):
            session = registry.session_for(["fake-server"], "/project", "file:///project")
        session.register_document("file:///a.ts", MagicMock())
        assert registry.release(session) is False

    def test_the_last_user_shuts_it_down(self):
        registry = self._registry()
        with patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession):
            session = registry.session_for(["fake-server"], "/project", "file:///project")
        session.register_document("file:///a.ts", MagicMock())
        session.forget_document("file:///a.ts")
        assert registry.release(session) is True
        assert registry.sessions() == []


@pytest.fixture()
def attached_clients(qapp):
    """Two clients attached to one fake server, as two open tabs would be."""
    from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
    registry = LspSessionRegistry()
    # server_command only answers for a server installed on this machine, which a
    # fake one is not.
    with patch("je_editor.pyside_ui.code.lsp.lsp_client.session_registry", registry), \
            patch("je_editor.pyside_ui.code.lsp.lsp_client.server_command",
                  return_value=["fake-server"]), \
            patch("je_editor.pyside_ui.code.lsp.lsp_session.LspSession", _FakeSession):
        first, second = LspClient(), LspClient()
        first.start_for("/project/a.ts")
        second.start_for("/project/b.ts")
        yield registry, first, second


class TestTheClientUsesTheSharedSession:
    def test_two_tabs_start_one_server(self, attached_clients):
        registry, _first, _second = attached_clients
        assert len(registry.sessions()) == 1

    def test_both_tabs_report_it_running(self, attached_clients):
        _registry, first, second = attached_clients
        assert first.running and second.running

    def test_closing_one_tab_leaves_the_server_up(self, attached_clients):
        registry, first, second = attached_clients
        with patch("je_editor.pyside_ui.code.lsp.lsp_client.session_registry", registry):
            first.stop()
        assert len(registry.sessions()) == 1
        assert second.running

    def test_closing_the_last_tab_shuts_it_down(self, attached_clients):
        registry, first, second = attached_clients
        with patch("je_editor.pyside_ui.code.lsp.lsp_client.session_registry", registry):
            first.stop()
            second.stop()
        assert registry.sessions() == []

    def test_closing_tells_the_server_the_file_is_closed(self, attached_clients):
        registry, first, _second = attached_clients
        session = registry.sessions()[0]
        with patch("je_editor.pyside_ui.code.lsp.lsp_client.session_registry", registry):
            first.stop()
        methods = [message.get("method") for message in session.sent]
        assert "textDocument/didClose" in methods

    def test_a_reply_reaches_only_the_tab_that_asked(self, attached_clients):
        registry, first, second = attached_clients
        session = registry.sessions()[0]
        received: list = []
        first.completions_ready.connect(received.append)
        second.completions_ready.connect(lambda _labels: received.append("wrong tab"))
        first.request_completion(0, 0)
        session.route({"id": first._pending_completion_id, "result": [{"label": "ok"}]})
        assert received == [["ok"]]

    def test_saving_tells_the_server(self, attached_clients):
        registry, first, _second = attached_clients
        session = registry.sessions()[0]
        assert first.did_save("text") is True
        assert session.sent[-1]["method"] == "textDocument/didSave"

    def test_saving_without_a_file_sends_nothing(self, qapp):
        from je_editor.pyside_ui.code.lsp.lsp_client import LspClient
        assert LspClient().did_save("text") is False
