"""Tests for the OpenAI-compatible and Anthropic providers, against fakes of their SDK clients."""
from __future__ import annotations

import warnings
from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from langchain_core.messages import AIMessage

from je_editor.adapters.ai.anthropic_provider import (
    DEFAULT_MODEL, MAX_OUTPUT_TOKENS, AnthropicProvider
)
from je_editor.adapters.ai.builtin_providers import register_builtin_ai_providers
from je_editor.adapters.ai.openai_provider import OpenAIProvider, answer_after_reasoning
from je_editor.core.ai.ai_provider import (
    AIProvider, CancelToken, ChatMessage, ChatRequest, ChatRole
)
from je_editor.core.ai.ai_settings import AISettings, ProviderSettings
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.utils.exception.exceptions import JEditorServiceException

FALLBACK_BETA = "server-side-fallback-2026-07-01"


def ask(text: str, **fields) -> ChatRequest:
    return ChatRequest((ChatMessage(ChatRole.USER, text),), **fields)


# --- OpenAI-compatible ------------------------------------------------------

class FakeChat:
    """Stands in for ChatOpenAI, returning a real AIMessage without any network."""

    def __init__(self, content: str, usage: dict | None = None) -> None:
        self._content = content
        self._usage = usage
        self.calls: list[list[tuple[str, str]]] = []

    def invoke(self, messages: list[tuple[str, str]]) -> AIMessage:
        self.calls.append(messages)
        return AIMessage(content=self._content, usage_metadata=self._usage)


def openai_provider(content: str, settings: ProviderSettings | None = None, usage=None):
    """A provider whose model is a fake answering with ``content``, plus that fake and the build log."""
    chat = FakeChat(content, usage)
    built: list[tuple[ProviderSettings, str]] = []

    def factory(current: ProviderSettings, model: str) -> FakeChat:
        built.append((current, model))
        return chat

    current = settings or ProviderSettings(model="gpt-4o-mini")
    return OpenAIProvider(lambda: current, factory), chat, built


class TestOpenAIReadingTheReply:
    def test_a_plain_reply_comes_back_unchanged(self):
        provider, _chat, _built = openai_provider("hello there")
        assert provider.complete(ask("hi")).text == "hello there"

    def test_the_prompt_reaches_the_model(self):
        provider, chat, _built = openai_provider("anything")
        provider.complete(ask("what is 2 + 2?"))
        assert chat.calls == [[("human", "what is 2 + 2?")]]

    def test_an_empty_reply_stays_empty(self):
        provider, _chat, _built = openai_provider("")
        assert provider.complete(ask("hi")).text == ""

    def test_reading_the_text_warns_of_nothing_deprecated(self):
        # ``text`` is a property upstream; calling it as a method still returns
        # the right value but is deprecated, so only a recorded warning shows it.
        provider, _chat, _built = openai_provider("hello there")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert provider.complete(ask("hi")).text == "hello there"
        deprecated = [str(item.message) for item in caught
                      if issubclass(item.category, DeprecationWarning)]
        assert not deprecated, deprecated


class TestStrippingTheThinkingBlock:
    def test_content_before_the_closing_tag_is_dropped(self):
        provider, _chat, _built = openai_provider("<think>internal reasoning</think>\n  the answer  ")
        assert provider.complete(ask("hi")).text == "the answer"

    def test_a_reply_without_the_tag_is_left_alone(self):
        assert answer_after_reasoning("just the answer") == "just the answer"

    def test_only_the_first_closing_tag_starts_the_answer(self):
        assert answer_after_reasoning("<think>a</think>first</think>second") == "first</think>second"

    def test_the_listener_never_sees_the_thinking(self):
        provider, _chat, _built = openai_provider("<think>secret plan</think>the answer")
        heard: list[str] = []
        provider.complete(ask("hi"), on_text=heard.append)
        assert heard == ["the answer"]


class TestOpenAIRequestShape:
    def test_the_system_prompt_and_the_history_are_sent_in_order(self):
        provider, chat, _built = openai_provider("ok")
        provider.complete(ChatRequest(
            (ChatMessage(ChatRole.USER, "first"), ChatMessage(ChatRole.ASSISTANT, "reply"),
             ChatMessage(ChatRole.USER, "second")),
            system_prompt="Be brief."))
        assert chat.calls == [[("system", "Be brief."), ("human", "first"), ("ai", "reply"),
                               ("human", "second")]]

    def test_the_system_prompt_falls_back_to_the_settings(self):
        provider, chat, _built = openai_provider(
            "ok", ProviderSettings(model="gpt-4o-mini", system_prompt="From the settings."))
        provider.complete(ask("hi"))
        assert chat.calls[0][0] == ("system", "From the settings.")

    def test_the_model_of_the_request_wins_over_the_settings(self):
        provider, _chat, built = openai_provider("ok")
        response = provider.complete(ask("hi", model_id="another-model"))
        assert built[0][1] == "another-model"
        assert response.model_id == "another-model"

    def test_no_model_anywhere_is_refused_before_any_call(self):
        provider, chat, _built = openai_provider("ok", ProviderSettings())
        with pytest.raises(JEditorServiceException, match="No model is set"):
            provider.complete(ask("hi"))
        assert chat.calls == []

    def test_token_usage_is_reported_when_the_service_gives_it(self):
        usage = {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15}
        provider, _chat, _built = openai_provider("ok", usage=usage)
        response = provider.complete(ask("hi"))
        assert (response.input_tokens, response.output_tokens) == (12, 3)

    def test_missing_usage_is_reported_as_unknown(self):
        provider, _chat, _built = openai_provider("ok")
        response = provider.complete(ask("hi"))
        assert (response.input_tokens, response.output_tokens) == (None, None)

    def test_a_reply_that_arrives_after_a_cancel_is_dropped(self):
        provider, _chat, _built = openai_provider("too late")
        cancel = CancelToken()
        cancel.cancel()
        heard: list[str] = []
        response = provider.complete(ask("hi"), heard.append, cancel)
        assert (response.cancelled, response.text, heard) == (True, "", [])

    def test_a_failure_of_the_service_becomes_the_editor_exception(self):
        from openai import OpenAIError

        class Failing:
            def invoke(self, _messages):
                raise OpenAIError("connection refused")

        provider = OpenAIProvider(lambda: ProviderSettings(model="m"), lambda _s, _m: Failing())
        with pytest.raises(JEditorServiceException, match="connection refused") as caught:
            provider.complete(ask("hi"))
        assert isinstance(caught.value.__cause__, OpenAIError)

    def test_the_real_chat_model_is_built_from_the_settings(self):
        from je_editor.adapters.ai.openai_provider import _build_chat_model
        chat = _build_chat_model(
            ProviderSettings(api_key="not-a-real-key", base_url="https://example.invalid/v1"),
            "gpt-4o-mini")
        assert (chat.model_name, str(chat.openai_api_base)) == (
            "gpt-4o-mini", "https://example.invalid/v1")


# --- Anthropic --------------------------------------------------------------

class FakeStream:
    """One open stream: yields the given pieces, then describes the finished message."""

    def __init__(self, pieces, final) -> None:
        self.text_stream = iter(pieces)
        self._final = final
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        self.closed = True

    def get_final_message(self):
        return self._final


class FakeMessages:
    """Records the parameters of each ``stream`` call."""

    def __init__(self, owner, surface: str) -> None:
        self._owner = owner
        self._surface = surface

    def stream(self, **parameters):
        self._owner.calls.append((self._surface, parameters))
        if self._owner.error is not None:
            raise self._owner.error
        self._owner.stream = FakeStream(self._owner.pieces, self._owner.final)
        return self._owner.stream


class FakeAnthropic:
    """Stands in for ``anthropic.Anthropic``: both the plain and the beta message surfaces."""

    def __init__(self, pieces=("Hello", ", ", "world"), stop_reason="end_turn", error=None,
                 stop_details=None, model="claude-opus-5-5") -> None:
        self.pieces = list(pieces)
        self.error = error
        self.final = SimpleNamespace(
            stop_reason=stop_reason, stop_details=stop_details, model=model,
            usage=SimpleNamespace(input_tokens=21, output_tokens=len(self.pieces)))
        self.calls: list[tuple[str, dict]] = []
        self.stream: FakeStream | None = None
        self.messages = FakeMessages(self, "messages")
        self.beta = SimpleNamespace(messages=FakeMessages(self, "beta.messages"))


def anthropic_provider(client: FakeAnthropic, settings: ProviderSettings | None = None):
    current = settings or ProviderSettings()
    return AnthropicProvider(lambda: current, lambda _settings: client)


def status_error(error_type, status: int, message: str):
    """A real SDK status error, built the way the SDK builds one from a response."""
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return error_type(message, response=httpx2.Response(status, request=request), body=None)


class TestAnthropicStreaming:
    def test_the_pieces_arrive_one_by_one_and_add_up_to_the_reply(self):
        heard: list[str] = []
        response = anthropic_provider(FakeAnthropic()).complete(ask("hi"), heard.append)
        assert heard == ["Hello", ", ", "world"]
        assert response.text == "Hello, world"

    def test_token_usage_and_the_answering_model_are_reported(self):
        response = anthropic_provider(FakeAnthropic(model="claude-opus-4-8")).complete(ask("hi"))
        assert (response.input_tokens, response.output_tokens, response.model_id) == (
            21, 3, "claude-opus-4-8")

    def test_the_stream_is_closed_afterwards(self):
        client = FakeAnthropic()
        anthropic_provider(client).complete(ask("hi"))
        assert client.stream.closed is True

    def test_a_cancel_stops_part_way_and_keeps_what_arrived(self):
        client = FakeAnthropic(pieces=("one ", "two ", "three"))
        cancel = CancelToken()
        heard: list[str] = []

        def stop_after_the_first(piece: str) -> None:
            heard.append(piece)
            cancel.cancel()

        response = anthropic_provider(client).complete(ask("hi"), stop_after_the_first, cancel)
        assert (response.cancelled, response.text, heard) == (True, "one ", ["one "])
        assert client.stream.closed is True

    def test_a_refusal_is_reported_and_not_passed_off_as_an_answer(self):
        client = FakeAnthropic(pieces=("Sure, the first", ), stop_reason="refusal",
                               stop_details=SimpleNamespace(category="cyber"))
        with pytest.raises(JEditorServiceException, match="declined.*cyber"):
            anthropic_provider(client).complete(ask("hi"))

    def test_a_refusal_without_details_still_reads_sensibly(self):
        client = FakeAnthropic(pieces=(), stop_reason="refusal", stop_details=None)
        with pytest.raises(JEditorServiceException, match="category: unspecified"):
            anthropic_provider(client).complete(ask("hi"))


class TestAnthropicRequestShape:
    def _parameters(self, request: ChatRequest, settings: ProviderSettings | None = None):
        client = FakeAnthropic()
        anthropic_provider(client, settings).complete(request)
        return client.calls[0]

    def test_the_default_model_is_used_when_none_is_named(self):
        _surface, parameters = self._parameters(ask("hi"))
        assert parameters["model"] == DEFAULT_MODEL

    def test_the_model_of_the_request_wins_over_the_settings(self):
        _surface, parameters = self._parameters(
            ask("hi", model_id="claude-haiku-4-5"), ProviderSettings(model="claude-sonnet-5-5"))
        assert parameters["model"] == "claude-haiku-4-5"

    def test_the_history_keeps_its_roles_and_order(self):
        _surface, parameters = self._parameters(ChatRequest((
            ChatMessage(ChatRole.USER, "first"), ChatMessage(ChatRole.ASSISTANT, "reply"),
            ChatMessage(ChatRole.USER, "second"))))
        assert parameters["messages"] == [
            {"role": "user", "content": "first"}, {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"}]

    def test_the_system_prompt_is_a_parameter_of_its_own(self):
        _surface, parameters = self._parameters(ask("hi", system_prompt="Be brief."))
        assert parameters["system"] == "Be brief."

    def test_no_system_prompt_sends_no_system_parameter(self):
        _surface, parameters = self._parameters(ask("hi"))
        assert "system" not in parameters

    def test_the_output_cap_leaves_room_for_a_long_answer(self):
        _surface, parameters = self._parameters(ask("hi"))
        assert parameters["max_tokens"] == MAX_OUTPUT_TOKENS

    def test_nothing_the_newer_models_reject_is_sent(self):
        _surface, parameters = self._parameters(ask("hi"))
        assert not {"temperature", "top_p", "top_k", "thinking"} & set(parameters)

    @pytest.mark.parametrize("model", [
        "claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-opus-5"])
    def test_a_model_that_may_decline_gets_the_server_side_fallback(self, model):
        surface, parameters = self._parameters(ask("hi", model_id=model))
        assert surface == "beta.messages"
        assert (parameters["betas"], parameters["fallbacks"]) == ([FALLBACK_BETA], "default")

    @pytest.mark.parametrize("model", ["claude-haiku-4-5", "some-other-model"])
    def test_other_models_use_the_plain_surface(self, model):
        surface, parameters = self._parameters(ask("hi", model_id=model))
        assert surface == "messages"
        assert "fallbacks" not in parameters and "betas" not in parameters

    def test_another_address_turns_the_fallback_off(self):
        surface, parameters = self._parameters(
            ask("hi"), ProviderSettings(base_url="https://proxy.example.invalid"))
        assert surface == "messages"
        assert "fallbacks" not in parameters


class TestAnthropicErrors:
    @pytest.mark.parametrize("error, expected", [
        (status_error(anthropic.AuthenticationError, 401, "invalid x-api-key"), "rejected the API key"),
        (status_error(anthropic.PermissionDeniedError, 403, "no access"), "may not use that model"),
        (status_error(anthropic.NotFoundError, 404, "model: nope"), "does not know that model"),
        (status_error(anthropic.RateLimitError, 429, "slow down"), "rate limiting"),
        (status_error(anthropic.BadRequestError, 400, "bad field"), "rejected the request"),
        (status_error(anthropic.InternalServerError, 500, "overloaded"), "returned an error"),
        (anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")),
         "Could not reach Anthropic"),
    ])
    def test_each_kind_of_failure_gets_its_own_explanation(self, error, expected):
        with pytest.raises(JEditorServiceException, match=expected) as caught:
            anthropic_provider(FakeAnthropic(error=error)).complete(ask("hi"))
        assert caught.value.__cause__ is error

    def test_missing_credentials_are_explained(self):
        missing = TypeError("Could not resolve authentication method.")
        with pytest.raises(JEditorServiceException, match="No Anthropic credentials"):
            anthropic_provider(FakeAnthropic(error=missing)).complete(ask("hi"))


class TestTheRealAnthropicClient:
    """The provider's calls match the SDK that is installed, checked without any network."""

    @pytest.fixture()
    def client(self):
        from je_editor.adapters.ai.anthropic_provider import _build_client
        return _build_client(ProviderSettings(api_key="not-a-real-key"))

    def test_the_key_and_the_address_reach_the_client(self):
        from je_editor.adapters.ai.anthropic_provider import _build_client
        built = _build_client(ProviderSettings(
            api_key="not-a-real-key", base_url="https://proxy.example.invalid"))
        assert built.api_key == "not-a-real-key"
        assert str(built.base_url).startswith("https://proxy.example.invalid")

    def test_both_stream_methods_take_the_parameters_the_provider_sends(self, client):
        import inspect
        plain = set(inspect.signature(client.messages.stream).parameters)
        beta = set(inspect.signature(client.beta.messages.stream).parameters)
        assert {"model", "max_tokens", "messages", "system"} <= plain
        assert {"model", "max_tokens", "messages", "system", "betas", "fallbacks"} <= beta


class TestTheBuiltInProviders:
    @pytest.fixture()
    def registry(self):
        settings = AISettings()
        registry: NamedRegistry[AIProvider] = NamedRegistry("AI provider")
        register_builtin_ai_providers(registry, lambda: settings)
        return registry, settings

    def test_both_are_registered_under_their_names(self, registry):
        assert registry[0].names() == ["openai", "anthropic"]

    def test_each_satisfies_the_provider_interface(self, registry):
        assert all(isinstance(provider, AIProvider) for _name, provider in registry[0].items())

    def test_only_anthropic_offers_a_fixed_model_list(self, registry):
        assert registry[0].require("openai").models() == []
        assert registry[0].require("anthropic").models()[0].model_id == DEFAULT_MODEL

    def test_a_provider_reads_its_own_group_of_the_latest_settings(self, registry):
        providers, settings = registry
        settings.update("openai", model="set-after-registering")
        settings.update("anthropic", model="claude-haiku-4-5")
        assert providers.require("openai")._settings().model == "set-after-registering"
        assert providers.require("anthropic")._settings().model == "claude-haiku-4-5"
