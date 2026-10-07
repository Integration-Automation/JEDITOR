"""Tests for the conversation a chat panel keeps."""
from __future__ import annotations

import pytest

from je_editor.core.ai.ai_provider import ChatResponse, ChatRole
from je_editor.core.ai.chat_session import ChatSession


class TestAsking:
    def test_the_first_request_holds_only_the_prompt(self):
        request = ChatSession().ask("hello")
        assert [(message.role, message.content) for message in request.messages] == [
            (ChatRole.USER, "hello")]

    def test_the_model_and_the_system_prompt_go_into_the_request(self):
        request = ChatSession().ask("hello", "claude-opus-5-5", "Be brief.")
        assert (request.model_id, request.system_prompt) == ("claude-opus-5-5", "Be brief.")

    def test_surrounding_space_is_trimmed(self):
        assert ChatSession().ask("  hello \n").messages[-1].content == "hello"

    @pytest.mark.parametrize("prompt", ["", "   ", "\n\t"])
    def test_an_empty_prompt_builds_no_request(self, prompt):
        session = ChatSession()
        assert session.ask(prompt) is None
        assert not session.is_waiting

    def test_a_second_prompt_waits_for_the_first_reply(self):
        session = ChatSession()
        session.ask("first")
        assert session.is_waiting
        assert session.ask("second") is None


class TestTheReply:
    def test_an_answered_exchange_joins_the_conversation(self):
        session = ChatSession()
        session.ask("hello")
        assert session.answered(ChatResponse("hi there")) is True
        assert [(message.role, message.content) for message in session.messages] == [
            (ChatRole.USER, "hello"), (ChatRole.ASSISTANT, "hi there")]

    def test_the_next_request_carries_the_conversation(self):
        session = ChatSession()
        session.ask("hello")
        session.answered(ChatResponse("hi there"))
        request = session.ask("and then?")
        assert [message.content for message in request.messages] == [
            "hello", "hi there", "and then?"]

    def test_the_prompt_is_not_part_of_the_conversation_until_it_is_answered(self):
        session = ChatSession()
        session.ask("hello")
        assert session.messages == ()

    @pytest.mark.parametrize("response", [
        ChatResponse("partial", cancelled=True), ChatResponse(""),
    ])
    def test_a_cancelled_or_empty_reply_drops_the_exchange(self, response):
        session = ChatSession()
        session.ask("hello")
        assert session.answered(response) is False
        assert session.messages == () and not session.is_waiting

    def test_a_reply_nobody_asked_for_is_ignored(self):
        session = ChatSession()
        assert session.answered(ChatResponse("unsolicited")) is False
        assert session.messages == ()

    def test_a_failure_drops_the_prompt_and_frees_the_session(self):
        session = ChatSession()
        session.ask("hello")
        session.failed()
        assert not session.is_waiting
        assert len(session.ask("again").messages) == 1

    def test_clearing_starts_over(self):
        session = ChatSession()
        session.ask("hello")
        session.answered(ChatResponse("hi there"))
        session.ask("pending")
        session.clear()
        assert session.messages == () and not session.is_waiting
