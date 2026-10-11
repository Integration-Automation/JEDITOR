"""Tests for the language service interface and its registry."""
from __future__ import annotations

import pytest

import threading

from je_editor.core.diagnostics.diagnostic_model import Position
from je_editor.core.document.document_model import Document, DocumentStore, TextDocument
from je_editor.core.language.language_request import (
    LanguageReply, LanguageRequest, ReplyOnce, nothing_to_cancel
)
from je_editor.core.language.language_service import (
    LanguageCapability, LanguageService, LanguageServiceRegistry
)
from je_editor.core.uri.resource_uri import to_uri
from je_editor.utils.exception.exceptions import JEditorServiceException


class RecordingService:
    """A language service that writes down everything it is told."""

    def __init__(self, name: str, language_id: str,
                 capabilities: frozenset[LanguageCapability] = frozenset(),
                 answer_at_once: bool = True) -> None:
        self.name = name
        self._language_id = language_id
        self._capabilities = capabilities
        self._answer_at_once = answer_at_once
        self.events: list[tuple[str, str]] = []
        self.pending: list = []
        self.cancelled = 0

    def capabilities(self) -> frozenset[LanguageCapability]:
        return self._capabilities

    def handles(self, document: Document) -> bool:
        return document.language_id == self._language_id

    def document_opened(self, document: Document) -> None:
        self.events.append(("opened", document.uri))

    def document_changed(self, document: Document) -> None:
        self.events.append(("changed", document.uri))

    def document_closed(self, document: Document) -> None:
        self.events.append(("closed", document.uri))

    def request(self, request, on_reply):
        self.events.append(("request", request.capability.value))
        if self._answer_at_once:
            on_reply(LanguageReply(request, self.name, value=f"{self.name} answers"))
            return nothing_to_cancel
        self.pending.append((request, on_reply))
        return self._cancel

    def _cancel(self) -> None:
        self.cancelled += 1

    def answer_pending(self) -> None:
        for request, on_reply in self.pending:
            on_reply(LanguageReply(request, self.name, value=f"{self.name} answers late"))

    def shutdown(self) -> None:
        self.events.append(("shutdown", ""))


@pytest.fixture()
def documents():
    return DocumentStore()


@pytest.fixture()
def registry(documents):
    return LanguageServiceRegistry(documents)


@pytest.fixture()
def python_uri(tmp_path):
    return to_uri(tmp_path / "main.py")


@pytest.fixture()
def rust_uri(tmp_path):
    return to_uri(tmp_path / "main.rs")


class TestTheInterface:
    def test_a_complete_service_satisfies_the_protocol(self):
        assert isinstance(RecordingService("python", "python"), LanguageService)

    def test_an_object_without_the_lifecycle_does_not(self):
        class NameOnly:
            name = "incomplete"

        assert not isinstance(NameOnly(), LanguageService)


class TestRegistration:
    def test_a_registered_service_is_listed(self, registry):
        service = RecordingService("python", "python")
        registry.register(service)
        assert registry.services() == [service]

    def test_two_services_cannot_share_a_name(self, registry):
        registry.register(RecordingService("python", "python"))
        with pytest.raises(JEditorServiceException, match="already registered"):
            registry.register(RecordingService("python", "rust"))

    def test_a_late_service_is_told_about_documents_already_open(
            self, registry, documents, python_uri, rust_uri):
        documents.open(TextDocument(python_uri, language_id="python"))
        documents.open(TextDocument(rust_uri, language_id="rust"))
        service = RecordingService("python", "python")
        registry.register(service)
        assert service.events == [("opened", python_uri)]

    def test_unregistering_shuts_the_service_down(self, registry):
        service = RecordingService("python", "python")
        registry.register(service)
        assert registry.unregister("python") is True
        assert service.events == [("shutdown", "")]
        assert registry.services() == []

    def test_unregistering_an_unknown_name_does_nothing(self, registry):
        assert registry.unregister("missing") is False


class TestLifecycleForwarding:
    def test_a_service_hears_the_whole_life_of_its_documents(
            self, registry, documents, python_uri):
        service = RecordingService("python", "python")
        registry.register(service)
        documents.open(TextDocument(python_uri, "a", "python"))
        documents.replace_text(python_uri, "b")
        documents.close(python_uri)
        assert service.events == [
            ("opened", python_uri), ("changed", python_uri), ("closed", python_uri)]

    def test_a_service_hears_nothing_about_other_languages(
            self, registry, documents, rust_uri):
        service = RecordingService("python", "python")
        registry.register(service)
        documents.open(TextDocument(rust_uri, "fn main() {}", "rust"))
        documents.replace_text(rust_uri, "fn main() { }")
        documents.close(rust_uri)
        assert service.events == []

    def test_every_service_for_a_language_is_told(self, registry, documents, python_uri):
        linter = RecordingService("linter", "python")
        parser = RecordingService("parser", "python")
        registry.register(linter)
        registry.register(parser)
        documents.open(TextDocument(python_uri, language_id="python"))
        assert linter.events == parser.events == [("opened", python_uri)]


class TestLookup:
    @pytest.fixture()
    def populated(self, registry):
        registry.register(RecordingService(
            "server", "python", frozenset({LanguageCapability.COMPLETION, LanguageCapability.HOVER})))
        registry.register(RecordingService(
            "parser", "python", frozenset({LanguageCapability.SYNTAX_TREE})))
        registry.register(RecordingService(
            "rust", "rust", frozenset({LanguageCapability.COMPLETION})))
        return registry

    def test_services_are_found_by_the_document_they_handle(self, populated, python_uri):
        document = TextDocument(python_uri, language_id="python")
        assert [service.name for service in populated.services_for(document)] == [
            "server", "parser"]

    def test_a_capability_narrows_the_answer(self, populated, python_uri):
        document = TextDocument(python_uri, language_id="python")
        found = populated.services_for(document, LanguageCapability.SYNTAX_TREE)
        assert [service.name for service in found] == ["parser"]

    def test_no_service_offers_what_nobody_registered(self, populated, python_uri):
        document = TextDocument(python_uri, language_id="python")
        assert populated.services_for(document, LanguageCapability.RENAME) == []

    def test_an_unknown_language_has_no_service(self, populated, tmp_path):
        document = TextDocument(to_uri(tmp_path / "notes.txt"), language_id="plaintext")
        assert populated.services_for(document) == []


class TestShutdown:
    def test_every_service_is_shut_down_and_removed(self, registry):
        first = RecordingService("first", "python")
        second = RecordingService("second", "rust")
        registry.register(first)
        registry.register(second)
        registry.shutdown()
        assert first.events == second.events == [("shutdown", "")]
        assert registry.services() == []

    def test_document_events_are_no_longer_listened_to(self, registry, documents):
        listening_before = (len(documents.opened), len(documents.changed), len(documents.closed))
        registry.shutdown()
        assert listening_before == (1, 1, 1)
        assert (len(documents.opened), len(documents.changed), len(documents.closed)) == (0, 0, 0)



class TestAskingAQuestion:
    """
    A question goes to the first service that can answer it, and the reply comes
    back through one function whether the service answers at once or later.
    """

    @pytest.fixture()
    def document(self, documents, python_uri):
        opened = TextDocument(python_uri, "x = 1\n", "python")
        documents.open(opened)
        return opened

    @staticmethod
    def _hover(document) -> LanguageRequest:
        return LanguageRequest(LanguageCapability.HOVER, document, Position(1, 1))

    def test_a_service_that_answers_at_once_replies_before_the_call_returns(
            self, registry, document):
        registry.register(RecordingService("jedi", "python", frozenset({LanguageCapability.HOVER})))
        replies: list[LanguageReply] = []
        registry.request(self._hover(document), replies.append)
        assert [(reply.ok, reply.service, reply.value) for reply in replies] == [
            (True, "jedi", "jedi answers")]

    def test_the_reply_names_the_question_it_answers(self, registry, document):
        registry.register(RecordingService("jedi", "python", frozenset({LanguageCapability.HOVER})))
        replies: list[LanguageReply] = []
        question = self._hover(document)
        registry.request(question, replies.append)
        assert replies[0].request is question

    def test_the_first_registered_service_that_can_answer_is_asked(self, registry, document):
        first = RecordingService("first", "python", frozenset({LanguageCapability.HOVER}))
        second = RecordingService("second", "python", frozenset({LanguageCapability.HOVER}))
        registry.register(first)
        registry.register(second)
        replies: list[LanguageReply] = []
        registry.request(self._hover(document), replies.append)
        assert replies[0].service == "first"
        assert ("request", "hover") not in second.events

    def test_a_service_without_the_capability_is_passed_over(self, registry, document):
        registry.register(RecordingService("lint", "python",
                                           frozenset({LanguageCapability.DIAGNOSTICS})))
        registry.register(RecordingService("jedi", "python", frozenset({LanguageCapability.HOVER})))
        replies: list[LanguageReply] = []
        registry.request(self._hover(document), replies.append)
        assert replies[0].service == "jedi"

    def test_nobody_to_ask_is_an_error_reply_not_an_exception(self, registry, document):
        replies: list[LanguageReply] = []
        cancel = registry.request(self._hover(document), replies.append)
        assert (replies[0].ok, replies[0].service, replies[0].value) == (False, "", None)
        assert "hover" in replies[0].error
        cancel()

    def test_a_service_that_waits_replies_later(self, registry, document):
        slow = RecordingService("server", "python", frozenset({LanguageCapability.HOVER}),
                                answer_at_once=False)
        registry.register(slow)
        replies: list[LanguageReply] = []
        registry.request(self._hover(document), replies.append)
        assert replies == []
        slow.answer_pending()
        assert [reply.value for reply in replies] == ["server answers late"]

    def test_a_cancelled_question_is_never_answered(self, registry, document):
        slow = RecordingService("server", "python", frozenset({LanguageCapability.HOVER}),
                                answer_at_once=False)
        registry.register(slow)
        replies: list[LanguageReply] = []
        cancel = registry.request(self._hover(document), replies.append)
        cancel()
        slow.answer_pending()
        assert (replies, slow.cancelled) == ([], 1)

    def test_cancelling_twice_tells_the_service_once(self, registry, document):
        slow = RecordingService("server", "python", frozenset({LanguageCapability.HOVER}),
                                answer_at_once=False)
        registry.register(slow)
        cancel = registry.request(self._hover(document), lambda _reply: None)
        cancel()
        cancel()
        assert slow.cancelled == 1

    def test_cancelling_after_the_reply_does_not_reach_the_service(self, registry, document):
        slow = RecordingService("server", "python", frozenset({LanguageCapability.HOVER}),
                                answer_at_once=False)
        registry.register(slow)
        cancel = registry.request(self._hover(document), lambda _reply: None)
        slow.answer_pending()
        cancel()
        assert slow.cancelled == 0

    def test_a_service_that_replies_twice_is_heard_once(self, registry, document):
        slow = RecordingService("server", "python", frozenset({LanguageCapability.HOVER}),
                                answer_at_once=False)
        registry.register(slow)
        replies: list[LanguageReply] = []
        registry.request(self._hover(document), replies.append)
        slow.answer_pending()
        slow.answer_pending()
        assert len(replies) == 1

    def test_a_question_without_a_position_and_with_options(self, document):
        question = LanguageRequest(LanguageCapability.FORMATTING, document,
                                   options={"tab_size": 4})
        assert (question.position, question.options["tab_size"]) == (None, 4)


class TestReplyOnce:
    def test_replies_racing_from_many_threads_deliver_one(self, documents, python_uri):
        document = TextDocument(python_uri, "", "python")
        question = LanguageRequest(LanguageCapability.HOVER, document)
        delivered: list[LanguageReply] = []
        reply_once = ReplyOnce(delivered.append)
        start = threading.Event()

        def reply() -> None:
            start.wait()
            reply_once(LanguageReply(question, "racer"))

        threads = [threading.Thread(target=reply) for _ in range(8)]
        for thread in threads:
            thread.start()
        start.set()
        for thread in threads:
            thread.join()
        assert (len(delivered), reply_once.settled) == (1, True)

    def test_an_error_reply_is_not_ok(self, python_uri):
        question = LanguageRequest(LanguageCapability.HOVER, TextDocument(python_uri, ""))
        assert LanguageReply(question, error="not available").ok is False
        assert LanguageReply(question, "jedi", value=None).ok is True
