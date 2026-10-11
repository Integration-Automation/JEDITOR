"""Tests for the document model and the store of open documents."""
from __future__ import annotations

import pytest

from je_editor.core.document.document_model import (
    INITIAL_VERSION, Document, DocumentStore, TextDocument
)
from je_editor.core.uri.resource_uri import to_uri


@pytest.fixture()
def uri(tmp_path):
    return to_uri(tmp_path / "sample.py")


class TestTextDocument:
    def test_it_satisfies_the_document_protocol(self, uri):
        assert isinstance(TextDocument(uri), Document)

    def test_an_object_missing_the_text_is_not_a_document(self):
        class Incomplete:
            uri = "file:///x"
            language_id = "python"
            version = INITIAL_VERSION

        assert not isinstance(Incomplete(), Document)

    def test_it_reports_what_it_was_built_with(self, uri):
        document = TextDocument(uri, "print(1)\n", "python")
        assert (document.uri, document.text(), document.language_id) == (uri, "print(1)\n", "python")

    def test_a_new_document_starts_at_the_initial_version(self, uri):
        assert TextDocument(uri).version == INITIAL_VERSION

    def test_changing_the_text_raises_the_version(self, uri):
        document = TextDocument(uri, "a")
        assert document.set_text("b") is True
        assert document.text() == "b"
        assert document.version == INITIAL_VERSION + 1

    def test_setting_the_same_text_keeps_the_version(self, uri):
        document = TextDocument(uri, "a")
        assert document.set_text("a") is False
        assert document.version == INITIAL_VERSION


class TestDocumentStore:
    def test_an_opened_document_is_found_by_its_uri(self, uri):
        store = DocumentStore()
        document = TextDocument(uri)
        assert store.open(document) is True
        assert store.get(uri) is document
        assert len(store) == 1

    def test_the_same_uri_is_not_opened_twice(self, uri):
        store = DocumentStore()
        first = TextDocument(uri, "first")
        assert store.open(first) is True
        assert store.open(TextDocument(uri, "second")) is False
        assert store.get(uri) is first

    def test_another_spelling_of_the_path_finds_the_same_document(self, tmp_path):
        store = DocumentStore()
        document = TextDocument(to_uri(tmp_path / "sample.py"))
        store.open(document)
        assert store.get(to_uri(tmp_path / "pkg" / ".." / "sample.py")) is document

    def test_documents_are_listed_in_the_order_they_were_opened(self, tmp_path):
        store = DocumentStore()
        names = ["zeta.py", "alpha.py", "mid.py"]
        for name in names:
            store.open(TextDocument(to_uri(tmp_path / name)))
        assert [document.uri for document in store.documents()] == [
            to_uri(tmp_path / name) for name in names]

    def test_closing_lets_the_document_go(self, uri):
        store = DocumentStore()
        store.open(TextDocument(uri))
        assert store.close(uri) is True
        assert store.get(uri) is None
        assert store.close(uri) is False

    def test_replacing_the_text_updates_the_document(self, uri):
        store = DocumentStore()
        document = TextDocument(uri, "old")
        store.open(document)
        assert store.replace_text(uri, "new") is True
        assert document.text() == "new"

    def test_replacing_the_text_of_an_unopened_document_does_nothing(self, uri):
        assert DocumentStore().replace_text(uri, "new") is False

    def test_a_document_held_elsewhere_cannot_have_its_text_replaced(self, uri):
        store = DocumentStore()
        store.open(_WidgetBackedDocument(uri))
        assert store.replace_text(uri, "new") is False

    def test_each_lifecycle_step_is_announced_with_the_document(self, uri):
        store = DocumentStore()
        events = []
        store.opened.subscribe(lambda doc: events.append(("opened", doc.version)))
        store.changed.subscribe(lambda doc: events.append(("changed", doc.version)))
        store.closed.subscribe(lambda doc: events.append(("closed", doc.version)))
        store.open(TextDocument(uri, "a"))
        store.replace_text(uri, "b")
        store.close(uri)
        assert events == [
            ("opened", INITIAL_VERSION),
            ("changed", INITIAL_VERSION + 1),
            ("closed", INITIAL_VERSION + 1),
        ]

    def test_nothing_is_announced_when_nothing_happened(self, uri):
        store = DocumentStore()
        store.open(TextDocument(uri, "a"))
        events = []
        for hook in (store.opened, store.changed, store.closed):
            hook.subscribe(events.append)
        store.open(TextDocument(uri, "duplicate"))
        store.replace_text(uri, "a")
        store.close("file:///never/opened.py")
        assert events == []

    def test_an_adapter_announces_its_own_changes(self, uri):
        store = DocumentStore()
        document = _WidgetBackedDocument(uri)
        store.open(document)
        changed = []
        store.changed.subscribe(changed.append)
        assert store.notify_changed(uri) is True
        assert changed == [document]

    def test_a_change_to_an_unopened_document_is_not_announced(self, uri):
        store = DocumentStore()
        changed = []
        store.changed.subscribe(changed.append)
        assert store.notify_changed(uri) is False
        assert changed == []


class _WidgetBackedDocument:
    """Stands in for an adapter whose buffer lives in an editor widget."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.language_id = "python"
        self.version = INITIAL_VERSION

    def text(self) -> str:
        return "held by the widget"
