"""Tests for the language service interface and its registry."""
from __future__ import annotations

import pytest

from je_editor.core.document.document_model import Document, DocumentStore, TextDocument
from je_editor.core.language.language_service import (
    LanguageCapability, LanguageService, LanguageServiceRegistry
)
from je_editor.core.uri.resource_uri import to_uri
from je_editor.utils.exception.exceptions import JEditorServiceException


class RecordingService:
    """A language service that writes down everything it is told."""

    def __init__(self, name: str, language_id: str,
                 capabilities: frozenset[LanguageCapability] = frozenset()) -> None:
        self.name = name
        self._language_id = language_id
        self._capabilities = capabilities
        self.events: list[tuple[str, str]] = []

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
