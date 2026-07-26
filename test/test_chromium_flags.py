"""Tests that the embedded browser's startup noise is quieted."""
from __future__ import annotations

from je_editor.utils.browser.chromium_flags import (
    FLAGS_VARIABLE, QUIET_FLAG, flags_with_quiet_logging, quiet_chromium_logging
)


class TestQuietingChromium:
    """
    QtWebEngine embeds a whole Chromium that writes its own messages to standard
    error, and this editor pipes standard error into its output pane -- so a
    hardware video encoder it probed and rejected ends up in front of the user.
    """

    def test_the_flag_is_added_when_there_is_nothing(self):
        assert flags_with_quiet_logging(None) == QUIET_FLAG

    def test_the_flag_is_added_when_there_is_nothing_but_space(self):
        assert flags_with_quiet_logging("   ") == QUIET_FLAG

    def test_existing_flags_are_kept(self):
        result = flags_with_quiet_logging("--disable-gpu")
        assert "--disable-gpu" in result and QUIET_FLAG in result

    def test_a_log_level_the_user_chose_is_left_alone(self):
        # Someone who set a level evidently wants to see those messages.
        assert flags_with_quiet_logging("--log-level=0") == "--log-level=0"

    def test_a_log_level_among_other_flags_is_left_alone(self):
        flags = "--disable-gpu --log-level=1"
        assert flags_with_quiet_logging(flags) == flags

    def test_the_environment_is_set(self):
        environment: dict = {}
        quiet_chromium_logging(environment)
        assert environment[FLAGS_VARIABLE] == QUIET_FLAG

    def test_setting_it_twice_does_not_repeat_the_flag(self):
        environment: dict = {}
        quiet_chromium_logging(environment)
        quiet_chromium_logging(environment)
        assert environment[FLAGS_VARIABLE].count("--log-level") == 1

    def test_what_was_already_there_survives(self):
        environment = {FLAGS_VARIABLE: "--single-process"}
        quiet_chromium_logging(environment)
        assert "--single-process" in environment[FLAGS_VARIABLE]
