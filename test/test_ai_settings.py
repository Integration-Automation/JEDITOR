"""Tests for the provider-scoped AI settings and the file that holds them."""
from __future__ import annotations

import json
import logging

import pytest

from je_editor.adapters.ai.settings_file import (
    ai_settings_path, load_ai_settings, save_ai_settings
)
from je_editor.core.ai.ai_settings import AISettings, ProviderSettings
from je_editor.utils.exception.exceptions import JEditorServiceException

# A made-up value that only has to be long enough to be masked; it opens nothing.
PLACEHOLDER_KEY = "placeholder-0123456789-abcdefghij"
# What the settings file looked like before settings were grouped by provider
OLDER_FILE = {"AI_model": {
    "ai_base_url": "https://example.invalid/v1",
    "ai_api_key": PLACEHOLDER_KEY,
    "chat_model": "gpt-4o-mini",
    "prompt_template": "You are a careful reviewer.",
}}


class TestProviderSettings:
    def test_a_new_set_is_empty(self):
        assert ProviderSettings() == ProviderSettings("", "", "", "")

    def test_a_long_key_is_masked_to_its_ends(self):
        masked = ProviderSettings(api_key=PLACEHOLDER_KEY).masked_api_key
        assert masked == "plac...ghij"
        assert PLACEHOLDER_KEY[4:-4] not in masked

    @pytest.mark.parametrize("key", ["a", "abcd", "abcdefgh"])
    def test_a_short_key_is_hidden_entirely(self, key):
        assert ProviderSettings(api_key=key).masked_api_key == "*" * len(key)

    def test_no_key_masks_to_nothing(self):
        assert ProviderSettings().masked_api_key == ""


class TestAISettings:
    def test_an_unknown_provider_has_empty_settings(self):
        assert AISettings().settings_for("anthropic") == ProviderSettings()

    def test_updating_one_provider_leaves_the_other_alone(self):
        settings = AISettings()
        settings.update("openai", api_key="openai-key", model="gpt-4o-mini")
        settings.update("anthropic", api_key="anthropic-key")
        assert settings.settings_for("openai").api_key == "openai-key"
        assert settings.settings_for("anthropic").api_key == "anthropic-key"

    def test_an_update_keeps_the_fields_it_does_not_name(self):
        settings = AISettings()
        settings.update("openai", api_key="key", model="first")
        settings.update("openai", model="second")
        assert settings.settings_for("openai") == ProviderSettings(api_key="key", model="second")

    def test_a_round_trip_through_a_dictionary_loses_nothing(self):
        settings = AISettings(active_provider="anthropic")
        settings.update("anthropic", api_key="key", model="claude-opus-5-5", system_prompt="Be brief.")
        settings.update("openai", base_url="https://example.invalid/v1", model="gpt-4o-mini")
        assert AISettings.from_dict(settings.to_dict()) == settings

    @pytest.mark.parametrize("data", [None, [], "text", 7, {"providers": "not a mapping"}])
    def test_unusable_content_gives_empty_settings(self, data):
        assert AISettings.from_dict(data) == AISettings()

    def test_entries_of_the_wrong_type_are_skipped(self):
        loaded = AISettings.from_dict({"providers": {
            "openai": {"api_key": 42, "model": "gpt-4o-mini", "unknown_field": "ignored"},
            "broken": "not a mapping",
            "": {"model": "nameless"},
        }})
        assert loaded.providers == {"openai": ProviderSettings(model="gpt-4o-mini")}


class TestTheOlderFileFormat:
    def test_the_single_group_becomes_the_openai_provider(self):
        loaded = AISettings.from_dict(OLDER_FILE)
        assert loaded.settings_for("openai") == ProviderSettings(
            api_key=PLACEHOLDER_KEY, base_url="https://example.invalid/v1", model="gpt-4o-mini",
            system_prompt="You are a careful reviewer.")

    def test_the_openai_provider_becomes_the_one_in_use(self):
        assert AISettings.from_dict(OLDER_FILE).active_provider == "openai"

    def test_an_empty_older_group_adds_nothing(self):
        loaded = AISettings.from_dict({"AI_model": {"ai_base_url": "", "chat_model": ""}})
        assert loaded.providers == {}

    def test_newer_settings_win_over_the_older_group(self):
        data = dict(OLDER_FILE, providers={"openai": {"model": "newer-model"}},
                    active_provider="anthropic")
        loaded = AISettings.from_dict(data)
        assert loaded.settings_for("openai").model == "newer-model"
        assert loaded.active_provider == "anthropic"


class TestTheSettingsFile:
    def test_it_lives_under_the_dot_directory(self, tmp_path):
        assert ai_settings_path(tmp_path) == tmp_path / ".jeditor" / "ai_config.json"

    def test_the_default_place_is_the_working_directory(self, tmp_dir):
        assert ai_settings_path().parent.name == ".jeditor"
        assert ai_settings_path().parent.parent.samefile(tmp_dir)

    def test_a_missing_file_gives_empty_settings(self, tmp_path):
        assert load_ai_settings(tmp_path / "absent.json") == AISettings()

    def test_what_is_saved_is_what_is_loaded(self, tmp_path):
        settings = AISettings(active_provider="anthropic")
        settings.update("anthropic", api_key=PLACEHOLDER_KEY, model="claude-opus-5-5")
        target = save_ai_settings(settings, ai_settings_path(tmp_path))
        assert load_ai_settings(target) == settings

    def test_saving_creates_the_directory(self, tmp_path):
        target = ai_settings_path(tmp_path / "fresh-project")
        save_ai_settings(AISettings(active_provider="openai"), target)
        assert target.is_file()

    def test_text_outside_ascii_is_kept_readable(self, tmp_path):
        settings = AISettings()
        settings.update("openai", system_prompt="請用繁體中文回答")
        target = save_ai_settings(settings, tmp_path / "ai_config.json")
        assert "請用繁體中文回答" in target.read_text(encoding="utf-8")

    def test_an_older_file_on_disk_is_read(self, tmp_path):
        target = tmp_path / "ai_config.json"
        target.write_text(json.dumps(OLDER_FILE), encoding="utf-8")
        assert load_ai_settings(target).settings_for("openai").model == "gpt-4o-mini"

    def test_a_corrupt_file_gives_empty_settings(self, tmp_path):
        target = tmp_path / "ai_config.json"
        target.write_text("{not json", encoding="utf-8")
        assert load_ai_settings(target) == AISettings()

    def test_a_file_that_cannot_be_written_is_reported(self, tmp_path):
        blocked = tmp_path / "a-file"
        blocked.write_text("in the way", encoding="utf-8")
        with pytest.raises(JEditorServiceException, match="could not be saved"):
            save_ai_settings(AISettings(), blocked / "ai_config.json")


class TestTheKeyStaysOutOfTheLog:
    """Saving and loading record where the file is, never what is in it."""

    @pytest.fixture()
    def logged(self, tmp_path, caplog):
        settings = AISettings(active_provider="anthropic")
        settings.update("anthropic", api_key=PLACEHOLDER_KEY)
        with caplog.at_level(logging.DEBUG, logger="JEditor"):
            target = save_ai_settings(settings, tmp_path / "ai_config.json")
            load_ai_settings(target)
        return caplog.text

    def test_the_save_is_recorded_with_its_path(self, logged):
        assert "AI settings saved" in logged
        assert "ai_config.json" in logged

    def test_the_key_is_not_recorded(self, logged):
        assert PLACEHOLDER_KEY not in logged
