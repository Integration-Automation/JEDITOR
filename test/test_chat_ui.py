"""Tests for the chat panel, its worker and the AI settings dialog, driven by fake providers."""
from __future__ import annotations

from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QLineEdit

from je_editor.adapters.ai.settings_file import ai_settings_path, load_ai_settings
from je_editor.core.ai.ai_provider import ChatMessage, ChatRequest, ChatResponse, ChatRole, ModelInfo
from je_editor.core.services.editor_services import EditorServices
from je_editor.pyside_ui.dialog.ai_dialog.set_ai_dialog import SetAIDialog
from je_editor.pyside_ui.main_ui.ai_widget import chat_worker
from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI, services_for
from je_editor.pyside_ui.main_ui.ai_widget.chat_worker import (
    ChatWorker, cancel_chat_workers, wait_for_chat_workers
)
from je_editor.utils.exception.exceptions import JEditorServiceException
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.multi_language.traditional_chinese import traditional_chinese_word_dict

# Long enough that a slow machine still finishes; a hang fails rather than blocks.
TIMEOUT_MS = 10_000
CHAT_UI = "je_editor.pyside_ui.main_ui.ai_widget.chat_ui"
DIALOG = "je_editor.pyside_ui.dialog.ai_dialog.set_ai_dialog"


class EchoProvider:
    """Answers with the last message in upper case, one word at a time."""

    name = "echo"

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []

    def models(self) -> list[ModelInfo]:
        return [ModelInfo("echo-large"), ModelInfo("echo-small")]

    def complete(self, request, on_text=None, cancel=None) -> ChatResponse:
        self.requests.append(request)
        words = request.messages[-1].content.upper().split()
        for index, word in enumerate(words):
            on_text(word if index == 0 else f" {word}")
        return ChatResponse(" ".join(words), request.model_id, len(request.messages), len(words))


class FailingProvider:
    """Fails every request with the error it was built with."""

    name = "failing"

    def __init__(self, error: Exception) -> None:
        self._error = error

    def models(self) -> list[ModelInfo]:
        return []

    def complete(self, request, on_text=None, cancel=None) -> ChatResponse:
        raise self._error


class SlowProvider:
    """Sends one piece, then waits until it is cancelled or released."""

    name = "slow"

    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()

    def models(self) -> list[ModelInfo]:
        return []

    def complete(self, request, on_text=None, cancel=None) -> ChatResponse:
        on_text("partial")
        self.started.set()
        while not self.release.wait(0.01):
            if cancel.cancelled:
                return ChatResponse("partial", cancelled=True)
        return ChatResponse("partial and the rest")


def ask(text: str) -> ChatRequest:
    return ChatRequest((ChatMessage(ChatRole.USER, text),))


@pytest.fixture(autouse=True)
def _no_chat_requests_left_running():
    """A request left in flight would deliver its signals into the next test."""
    yield
    cancel_chat_workers()
    assert wait_for_chat_workers(TIMEOUT_MS)
    QApplication.processEvents()


@pytest.fixture()
def services():
    built = EditorServices()
    built.ai_providers.register("echo", EchoProvider())
    built.ai_settings.active_provider = "echo"
    return built


@pytest.fixture()
def panel(qapp, qtbot, services):
    widget = ChatUI(SimpleNamespace(services=services))
    qtbot.addWidget(widget)
    return widget


def send(panel: ChatUI, qtbot, text: str) -> None:
    """Send a prompt and wait until its reply, or its failure, has been handled."""
    panel.prompt_input.setText(text)
    assert panel.call_ai_model() is True
    qtbot.waitUntil(lambda: panel._worker is None, timeout=TIMEOUT_MS)


class TestTheWorker:
    def test_pieces_then_the_reply_then_the_end_are_signalled(self, qapp, qtbot):
        worker = ChatWorker(EchoProvider(), ask("hello world"))
        events: list[tuple] = []
        worker.text_ready.connect(lambda piece: events.append(("text", piece)))
        worker.replied.connect(lambda response: events.append(("replied", response.text)))
        worker.finished.connect(lambda: events.append(("finished",)))
        worker.start_request()
        qtbot.waitUntil(lambda: ("finished",) in events, timeout=TIMEOUT_MS)
        assert events == [("text", "HELLO"), ("text", " WORLD"), ("replied", "HELLO WORLD"),
                          ("finished",)]

    @pytest.mark.parametrize("error, expected", [
        (JEditorServiceException("the key was rejected"), "the key was rejected"),
        (RuntimeError("a plugin bug"), "RuntimeError: a plugin bug"),
    ])
    def test_a_failure_is_signalled_in_words(self, qapp, qtbot, error, expected):
        worker = ChatWorker(FailingProvider(error), ask("hi"))
        failures: list[str] = []
        worker.failed.connect(failures.append)
        worker.start_request()
        qtbot.waitUntil(lambda: bool(failures), timeout=TIMEOUT_MS)
        assert failures == [expected]

    def test_a_running_worker_is_kept_alive_and_let_go_when_done(self, qapp, qtbot):
        provider = SlowProvider()
        worker = ChatWorker(provider, ask("hi"))
        worker.start_request()
        assert provider.started.wait(TIMEOUT_MS / 1000)
        assert worker in chat_worker._live_workers
        provider.release.set()
        qtbot.waitUntil(lambda: worker not in chat_worker._live_workers, timeout=TIMEOUT_MS)

    def test_waiting_reports_whether_it_finished(self, qapp):
        provider = SlowProvider()
        worker = ChatWorker(provider, ask("hi"))
        worker.start_request()
        assert provider.started.wait(TIMEOUT_MS / 1000)
        assert worker.wait(20) is False
        worker.cancel()
        assert worker.wait(TIMEOUT_MS) is True

    def test_a_worker_that_never_started_counts_as_finished(self, qapp):
        assert ChatWorker(EchoProvider(), ask("hi")).wait(1) is True


class TestProvidersAndModels:
    def test_the_providers_come_from_the_registry(self, panel, services):
        services.ai_providers.register("failing", FailingProvider(RuntimeError("unused")))
        panel.refresh_providers()
        listed = [panel.provider_combobox.itemText(i) for i in range(panel.provider_combobox.count())]
        assert listed == ["echo", "failing"]

    def test_the_provider_in_use_is_selected(self, panel):
        assert panel.provider_combobox.currentText() == "echo"
        assert panel.current_provider().name == "echo"

    def test_the_models_of_the_provider_are_offered(self, panel):
        offered = [panel.model_combobox.itemText(i) for i in range(panel.model_combobox.count())]
        assert offered == ["echo-large", "echo-small"]
        assert panel.model_combobox.currentText() == "echo-large"

    def test_the_configured_model_is_selected_even_when_not_offered(self, panel, services):
        services.ai_settings.update("echo", model="echo-custom")
        panel.refresh_providers()
        assert panel.model_combobox.currentText() == "echo-custom"

    def test_picking_another_provider_makes_it_the_one_in_use(self, panel, services):
        services.ai_providers.register("failing", FailingProvider(RuntimeError("unused")))
        panel.refresh_providers()
        panel.provider_combobox.setCurrentText("failing")
        assert services.ai_settings.active_provider == "failing"
        assert panel.model_combobox.count() == 0

    def test_a_window_with_services_shares_them(self, services):
        assert services_for(SimpleNamespace(services=services)) is services

    def test_a_window_without_services_gets_the_built_in_providers(self, tmp_dir):
        assert services_for(object()).ai_providers.names() == ["openai", "anthropic"]


class TestSendingAPrompt:
    def test_the_exchange_is_shown_and_the_reply_arrives_in_pieces(self, panel, qtbot):
        send(panel, qtbot, "hello world")
        shown = panel.chat_panel.toPlainText()
        assert "You: hello world" in shown
        assert "Assistant: HELLO WORLD" in shown

    def test_the_input_is_cleared_and_the_buttons_come_back(self, panel, qtbot):
        send(panel, qtbot, "hello")
        assert panel.prompt_input.text() == ""
        assert panel.call_ai_model_button.isEnabled() and not panel.stop_button.isEnabled()

    def test_the_token_usage_is_shown(self, panel, qtbot):
        send(panel, qtbot, "hello world")
        assert panel.status_label.text() == "Reply complete: 1 tokens in, 2 tokens out"

    def test_the_selected_model_and_the_system_prompt_are_sent(self, panel, qtbot, services):
        services.ai_settings.update("echo", system_prompt="Be brief.")
        panel.model_combobox.setCurrentText("echo-small")
        send(panel, qtbot, "hello")
        request = services.ai_providers.require("echo").requests[0]
        assert (request.model_id, request.system_prompt) == ("echo-small", "Be brief.")

    def test_the_second_prompt_carries_the_conversation_so_far(self, panel, qtbot, services):
        send(panel, qtbot, "first")
        send(panel, qtbot, "second")
        sent = services.ai_providers.require("echo").requests[1].messages
        assert [(message.role, message.content) for message in sent] == [
            (ChatRole.USER, "first"), (ChatRole.ASSISTANT, "FIRST"), (ChatRole.USER, "second")]

    @pytest.mark.parametrize("text", ["", "   "])
    def test_an_empty_prompt_sends_nothing(self, panel, services, text):
        panel.prompt_input.setText(text)
        assert panel.call_ai_model() is False
        assert services.ai_providers.require("echo").requests == []

    def test_a_new_chat_forgets_the_conversation(self, panel, qtbot, services):
        send(panel, qtbot, "first")
        panel.new_chat()
        send(panel, qtbot, "second")
        assert panel.chat_panel.toPlainText().count("You:") == 1
        assert len(services.ai_providers.require("echo").requests[1].messages) == 1

    def test_no_provider_is_reported_instead_of_sending(self, qapp, qtbot):
        empty = ChatUI(SimpleNamespace(services=EditorServices()))
        qtbot.addWidget(empty)
        empty.prompt_input.setText("hello")
        with patch(f"{CHAT_UI}.QMessageBox.warning") as warning:
            assert empty.call_ai_model() is False
        assert warning.call_args.args[2] == "No AI provider is available"


class TestFailuresAndCancelling:
    @pytest.fixture()
    def failing_panel(self, qapp, qtbot):
        services = EditorServices()
        services.ai_providers.register(
            "failing", FailingProvider(JEditorServiceException("Anthropic rejected the API key")))
        widget = ChatUI(SimpleNamespace(services=services))
        qtbot.addWidget(widget)
        return widget

    def test_the_reason_is_shown_to_the_user(self, failing_panel, qtbot):
        with patch(f"{CHAT_UI}.QMessageBox.warning") as warning:
            send(failing_panel, qtbot, "hello")
        assert warning.call_args.args[2] == "Anthropic rejected the API key"
        assert failing_panel.status_label.text() == "The request failed"

    def test_the_unanswered_prompt_does_not_stay_in_the_conversation(self, failing_panel, qtbot):
        with patch(f"{CHAT_UI}.QMessageBox.warning"):
            send(failing_panel, qtbot, "hello")
        assert failing_panel._session.messages == ()
        assert failing_panel.call_ai_model_button.isEnabled()

    @pytest.fixture()
    def slow(self, qapp, qtbot):
        provider = SlowProvider()
        services = EditorServices()
        services.ai_providers.register("slow", provider)
        widget = ChatUI(SimpleNamespace(services=services))
        qtbot.addWidget(widget)
        widget.prompt_input.setText("take your time")
        assert widget.call_ai_model() is True
        assert provider.started.wait(TIMEOUT_MS / 1000)
        return widget, provider

    def test_sending_is_off_while_a_reply_is_awaited(self, slow):
        widget, _provider = slow
        assert not widget.call_ai_model_button.isEnabled() and widget.stop_button.isEnabled()
        assert widget.status_label.text() == "Waiting for the reply..."

    def test_stopping_cancels_and_keeps_the_conversation_clean(self, slow, qtbot):
        widget, _provider = slow
        widget.stop()
        qtbot.waitUntil(lambda: widget._worker is None, timeout=TIMEOUT_MS)
        assert widget.status_label.text() == "Cancelled"
        assert widget._session.messages == ()

    def test_closing_the_panel_mid_reply_leaves_nothing_running(self, slow):
        widget, _provider = slow
        widget.close()
        assert wait_for_chat_workers(TIMEOUT_MS)

    def test_a_reply_to_a_dropped_conversation_is_ignored(self, slow, qtbot):
        widget, provider = slow
        widget.new_chat()
        provider.release.set()
        assert wait_for_chat_workers(TIMEOUT_MS)
        QApplication.processEvents()
        assert widget.chat_panel.toPlainText() == ""
        assert widget._session.messages == ()


class TestRelabelling:
    def test_the_panel_moves_language_without_losing_the_conversation(self, panel, qtbot):
        send(panel, qtbot, "hello")
        language_wrapper.reset_language("Traditional_Chinese")
        try:
            panel.retranslate()
            assert panel.stop_button.text() == traditional_chinese_word_dict["chat_ui_stop_button"]
            assert "HELLO" in panel.chat_panel.toPlainText()
        finally:
            language_wrapper.reset_language("English")
            panel.retranslate()


class TestTheSettingsDialog:
    @pytest.fixture()
    def configured(self):
        services = EditorServices()
        services.ai_providers.register("echo", EchoProvider())
        services.ai_providers.register("failing", FailingProvider(RuntimeError("unused")))
        services.ai_settings.update("echo", api_key="echo-key", model="echo-large",
                                    base_url="https://echo.invalid", system_prompt="Be brief.")
        services.ai_settings.update("failing", model="other-model")
        return services

    @pytest.fixture()
    def dialog(self, qapp, qtbot, configured, tmp_dir):
        widget = SetAIDialog(configured, "echo")
        qtbot.addWidget(widget)
        return widget

    def test_it_opens_on_the_given_provider_with_its_settings(self, dialog):
        assert dialog.provider_combobox.currentText() == "echo"
        assert (dialog.base_url_input.text(), dialog.api_key_input.text(),
                dialog.chat_model_input.text(), dialog.system_prompt_input.toPlainText()) == (
            "https://echo.invalid", "echo-key", "echo-large", "Be brief.")

    def test_the_key_is_not_readable_on_screen(self, dialog):
        assert dialog.api_key_input.echoMode() == QLineEdit.EchoMode.Password

    def test_another_provider_shows_its_own_settings(self, dialog):
        dialog.provider_combobox.setCurrentText("failing")
        assert (dialog.chat_model_input.text(), dialog.api_key_input.text()) == ("other-model", "")

    def test_applying_changes_only_the_provider_shown(self, dialog, configured):
        dialog.chat_model_input.setText("echo-small")
        assert dialog.update_ai_config() is True
        assert configured.ai_settings.settings_for("echo").model == "echo-small"
        assert configured.ai_settings.settings_for("failing").model == "other-model"
        assert configured.ai_settings.active_provider == "echo"

    def test_applying_announces_itself(self, dialog, qtbot):
        with qtbot.waitSignal(dialog.settings_applied, timeout=TIMEOUT_MS):
            dialog.update_ai_config()

    def test_nothing_is_written_to_disk_by_default(self, dialog):
        dialog.update_ai_config()
        assert not ai_settings_path().exists()

    def test_ticking_the_box_saves_the_settings(self, dialog):
        dialog.save_to_file_checkbox.setChecked(True)
        dialog.update_ai_config()
        assert load_ai_settings(ai_settings_path()).settings_for("echo").api_key == "echo-key"

    def test_a_save_that_fails_is_reported_and_the_dialog_stays(self, dialog):
        dialog.save_to_file_checkbox.setChecked(True)
        failure = JEditorServiceException("The AI settings could not be saved")
        with patch(f"{DIALOG}.save_ai_settings", side_effect=failure), \
                patch(f"{DIALOG}.QMessageBox.warning") as warning:
            assert dialog.update_ai_config() is False
        assert "could not be saved" in warning.call_args.args[2]

    def test_the_panel_picks_up_what_the_dialog_applied(self, qapp, qtbot, configured, tmp_dir):
        panel = ChatUI(SimpleNamespace(services=configured))
        qtbot.addWidget(panel)
        panel.set_ai_config()
        dialog = panel.set_ai_config_dialog
        dialog.provider_combobox.setCurrentText("failing")
        dialog.chat_model_input.setText("picked-in-the-dialog")
        dialog.update_ai_config()
        assert panel.provider_combobox.currentText() == "failing"
        assert panel.model_combobox.currentText() == "picked-in-the-dialog"
