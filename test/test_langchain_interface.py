"""Tests for how the AI widget reads a reply out of a langchain message."""
from __future__ import annotations

import os
import warnings

import pytest
from langchain_core.messages import AIMessage

from je_editor.pyside_ui.main_ui.ai_widget.langchain_interface import LangChainInterface


class FakeChat:
    """Stand in for ChatOpenAI, returning a real AIMessage without any network."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> AIMessage:
        self.prompts.append(prompt)
        return AIMessage(content=self._content)


@pytest.fixture(autouse=True)
def _restore_openai_environment():
    """The interface writes its settings into os.environ; put them back afterwards."""
    keys = ("OPENAI_BASE_URL", "OPENAI_API_KEY", "CHAT_MODEL")
    saved = {key: os.environ.get(key) for key in keys}
    yield
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def build_interface(content: str) -> LangChainInterface:
    """An interface whose model is replaced by a fake that answers with ``content``."""
    interface = LangChainInterface(
        main_window=None,
        prompt_template="You are a {role}.",
        base_url="https://example.invalid/v1",
        api_key="not-a-real-key",
        chat_model="gpt-4o-mini",
    )
    interface.chat_ai = FakeChat(content)
    return interface


class TestReadingTheReply:
    def test_a_plain_reply_comes_back_unchanged(self):
        assert build_interface("hello there").call_ai_model("hi") == "hello there"

    def test_the_prompt_reaches_the_model(self):
        interface = build_interface("anything")
        interface.call_ai_model("what is 2 + 2?")
        assert interface.chat_ai.prompts == ["what is 2 + 2?"]

    def test_an_empty_reply_stays_empty(self):
        assert build_interface("").call_ai_model("hi") == ""

    def test_reading_the_text_warns_of_nothing_deprecated(self):
        """
        ``text`` is a property; calling it as a method is deprecated upstream and
        will eventually stop working. Nothing else here would notice, because the
        deprecated form still returns the right value.

        The warnings are recorded rather than raised: ``call_ai_model`` catches
        every exception and answers with a message box, so a raised warning would
        be swallowed there instead of failing the test.
        """
        interface = build_interface("hello there")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert interface.call_ai_model("hi") == "hello there"
        deprecated = [
            str(warning.message) for warning in caught
            if issubclass(warning.category, DeprecationWarning)
        ]
        assert not deprecated, deprecated


class TestStrippingTheThinkingBlock:
    def test_content_before_the_closing_tag_is_dropped(self):
        interface = build_interface("<think>internal reasoning</think>\n  the answer  ")
        assert interface.call_ai_model("hi") == "the answer"

    def test_a_reply_without_the_tag_is_left_alone(self):
        assert build_interface("just the answer").call_ai_model("hi") == "just the answer"

    def test_only_the_first_closing_tag_starts_the_answer(self):
        interface = build_interface("<think>a</think>first</think>second")
        assert interface.call_ai_model("hi") == "first</think>second"
