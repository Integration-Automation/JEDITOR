"""Tests for the Qt-free event hook and the named registry built on it."""
from __future__ import annotations

import logging

import pytest

from je_editor.core.events.event_hook import EventHook
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.utils.exception.exceptions import JEditorException, JEditorServiceException


class TestEventHook:
    def test_a_subscriber_receives_the_arguments(self):
        hook = EventHook()
        received = []
        hook.subscribe(lambda *args: received.append(args))
        hook.emit("uri", 3)
        assert received == [("uri", 3)]

    def test_subscribers_are_called_in_subscription_order(self):
        hook = EventHook()
        order = []
        hook.subscribe(lambda: order.append("first"))
        hook.subscribe(lambda: order.append("second"))
        hook.emit()
        assert order == ["first", "second"]

    def test_the_returned_function_unsubscribes(self):
        hook = EventHook()
        received = []
        unsubscribe = hook.subscribe(received.append)
        unsubscribe()
        hook.emit("ignored")
        assert received == []

    def test_unsubscribing_reports_whether_anything_was_removed(self):
        hook = EventHook()
        listener = print
        hook.subscribe(listener)
        assert hook.unsubscribe(listener) is True
        assert hook.unsubscribe(listener) is False

    def test_the_length_is_the_number_of_subscribers(self):
        hook = EventHook()
        hook.subscribe(print)
        hook.subscribe(repr)
        assert len(hook) == 2

    def test_a_subscriber_may_unsubscribe_while_being_called(self):
        hook = EventHook()
        calls = []

        def once() -> None:
            calls.append("once")
            hook.unsubscribe(once)

        hook.subscribe(once)
        hook.emit()
        hook.emit()
        assert calls == ["once"]

    def test_a_failing_subscriber_does_not_stop_the_others(self):
        hook = EventHook("sample")
        received = []

        def broken(_value: str) -> None:
            raise RuntimeError("subscriber bug")

        hook.subscribe(broken)
        hook.subscribe(received.append)
        hook.emit("delivered")
        assert received == ["delivered"]

    def test_a_failing_subscriber_is_logged_with_the_event_name(self, caplog):
        hook = EventHook("sample event")

        def broken() -> None:
            raise RuntimeError("subscriber bug")

        hook.subscribe(broken)
        with caplog.at_level(logging.ERROR, logger="JEditor"):
            hook.emit()
        assert "sample event" in caplog.text
        assert "subscriber bug" in caplog.text


class TestNamedRegistry:
    def test_a_registered_item_is_found_by_name(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        assert registry.get("one") == 1
        assert "one" in registry

    def test_an_unknown_name_gives_none(self):
        assert NamedRegistry("number").get("missing") is None

    def test_names_keep_registration_order(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("zeta", 1)
        registry.register("alpha", 2)
        assert registry.names() == ["zeta", "alpha"]
        assert registry.items() == [("zeta", 1), ("alpha", 2)]

    def test_a_taken_name_is_refused(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        with pytest.raises(JEditorServiceException, match="already registered"):
            registry.register("one", 2)
        assert registry.get("one") == 1

    def test_a_taken_name_can_be_replaced_on_request(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        registry.register("one", 2, replace=True)
        assert registry.get("one") == 2
        assert len(registry) == 1

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_an_empty_name_is_refused(self, name):
        with pytest.raises(JEditorServiceException, match="non-empty name"):
            NamedRegistry("number").register(name, 1)

    def test_require_returns_the_item(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        assert registry.require("one") == 1

    def test_require_names_what_is_registered_when_it_fails(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        with pytest.raises(JEditorServiceException, match="registered: one"):
            registry.require("two")

    def test_unregister_returns_what_was_removed(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        registry.register("one", 1)
        assert registry.unregister("one") == 1
        assert registry.unregister("one") is None
        assert len(registry) == 0

    def test_changes_are_announced_with_the_name(self):
        registry: NamedRegistry[int] = NamedRegistry("number")
        changed = []
        registry.changed.subscribe(changed.append)
        registry.register("one", 1)
        registry.unregister("one")
        registry.unregister("one")
        assert changed == ["one", "one"]

    def test_the_service_exception_belongs_to_the_editor_family(self):
        assert issubclass(JEditorServiceException, JEditorException)
