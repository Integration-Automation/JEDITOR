"""Tests for the plugin registry API."""
from __future__ import annotations

from je_editor.plugins import (
    register_programming_language,
    get_programming_language_plugin,
    get_all_programming_language_suffixes,
    register_natural_language,
    get_natural_language_plugin,
    register_plugin_run_config,
    get_all_plugin_run_configs,
    get_plugin_run_config_by_suffix,
    register_plugin_metadata,
    get_all_plugin_metadata,
)


class TestProgrammingLanguagePlugin:
    def test_register_and_get(self):
        syntax = {"keywords": {"words": ("test",), "color": None}}
        register_programming_language(".test_lang", syntax)
        plugin = get_programming_language_plugin(".test_lang")
        assert plugin is not None
        assert plugin["syntax_words"] == syntax

    def test_get_nonexistent_returns_none(self):
        assert get_programming_language_plugin(".nonexistent_xyz") is None

    def test_get_all_suffixes_includes_registered(self):
        register_programming_language(".test_suffix_check", {})
        assert ".test_suffix_check" in get_all_programming_language_suffixes()


class TestNaturalLanguagePlugin:
    def test_register_and_get(self):
        word_dict = {"application_name": "Test"}
        register_natural_language("TestLang", "Test Language", word_dict)
        plugin = get_natural_language_plugin("TestLang")
        assert plugin is not None
        assert plugin["display_name"] == "Test Language"
        assert plugin["word_dict"] is word_dict

    def test_get_nonexistent_returns_none(self):
        assert get_natural_language_plugin("NoSuchLang_xyz") is None


class TestPluginRunConfig:
    def test_register_and_get_by_suffix(self):
        config = {
            "name": "Test Runner",
            "suffixes": (".tst",),
            "compiler": "test_compiler",
        }
        register_plugin_run_config(config)
        result = get_plugin_run_config_by_suffix(".tst")
        assert result is not None
        assert result["name"] == "Test Runner"

    def test_get_by_unknown_suffix_returns_none(self):
        assert get_plugin_run_config_by_suffix(".unknown_xyz") is None

    def test_get_all_returns_list(self):
        assert isinstance(get_all_plugin_run_configs(), list)


class TestPluginMetadata:
    def test_register_and_get_all(self):
        meta = {"name": "TestPlugin", "author": "Test", "version": "1.0"}
        register_plugin_metadata(meta)
        all_meta = get_all_plugin_metadata()
        assert any(m["name"] == "TestPlugin" for m in all_meta)
