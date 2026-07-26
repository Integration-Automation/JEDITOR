"""Tests that the editor's own colours follow the chosen window style."""
from __future__ import annotations

import pytest

from je_editor.utils.theme.theme_colors import (
    DARK_COLORS, LIGHT_COLORS, is_light_style, palette_for, retheme
)


class TestRecognisingALightStyle:
    @pytest.mark.parametrize("name", [
        "light_blue.xml", "light_amber.xml", "LIGHT_RED.XML", " light_teal.xml ",
    ])
    def test_a_light_style_is_recognised(self, name):
        assert is_light_style(name) is True

    @pytest.mark.parametrize("name", ["dark_amber.xml", "dark_teal.xml", "", None])
    def test_anything_else_is_dark(self, name):
        assert is_light_style(name) is False


class TestThePalettes:
    def test_both_sets_cover_the_same_colours(self):
        assert set(DARK_COLORS) == set(LIGHT_COLORS)

    def test_every_colour_is_a_valid_rgb_triple(self):
        for palette in (DARK_COLORS, LIGHT_COLORS):
            for key, value in palette.items():
                assert len(value) == 3, key
                assert all(0 <= channel <= 255 for channel in value), key

    def test_the_light_set_really_is_lighter_behind_the_text(self):
        # The minimap draws a background, so it has to invert with the theme.
        assert sum(LIGHT_COLORS["minimap_background_color"]) > \
            sum(DARK_COLORS["minimap_background_color"])

    def test_a_light_style_gets_the_light_set(self):
        assert palette_for("light_blue.xml") == LIGHT_COLORS

    def test_a_dark_style_gets_the_dark_set(self):
        assert palette_for("dark_amber.xml") == DARK_COLORS

    def test_the_palette_is_a_copy(self):
        palette = palette_for("dark_amber.xml")
        palette["line_number_color"][0] = 1
        assert DARK_COLORS["line_number_color"][0] != 1


class TestRethemeing:
    def test_a_default_moves_to_the_new_theme(self):
        result = retheme(dict(DARK_COLORS), "light_blue.xml")
        assert result["minimap_background_color"] == LIGHT_COLORS["minimap_background_color"]

    def test_switching_back_restores_the_dark_default(self):
        light = retheme(dict(DARK_COLORS), "light_blue.xml")
        assert retheme(light, "dark_amber.xml") == DARK_COLORS

    def test_a_colour_the_user_picked_survives(self):
        current = dict(DARK_COLORS)
        current["line_number_color"] = [10, 20, 30]
        result = retheme(current, "light_blue.xml")
        assert result["line_number_color"] == [10, 20, 30]

    def test_the_other_colours_still_move(self):
        current = dict(DARK_COLORS)
        current["line_number_color"] = [10, 20, 30]
        result = retheme(current, "light_blue.xml")
        assert result["indent_guide_color"] == LIGHT_COLORS["indent_guide_color"]

    def test_a_missing_colour_is_filled_in(self):
        result = retheme({}, "light_blue.xml")
        assert result == LIGHT_COLORS

    def test_the_input_is_not_modified(self):
        current = dict(DARK_COLORS)
        retheme(current, "light_blue.xml")
        assert current["indent_guide_color"] == DARK_COLORS["indent_guide_color"]


class TestApplyingToTheSettings:
    def test_applying_a_light_style_updates_the_live_colours(self):
        from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
            actually_color_dict, apply_theme_colors, user_setting_color_dict
        )
        try:
            apply_theme_colors("light_blue.xml")
            assert user_setting_color_dict["minimap_background_color"] == \
                LIGHT_COLORS["minimap_background_color"]
            # The QColor dictionary the painting reads has to move with it.
            colour = actually_color_dict["minimap_background_color"]
            actual = [colour.red(), colour.green(), colour.blue()]
            assert actual == LIGHT_COLORS["minimap_background_color"]
        finally:
            apply_theme_colors("dark_amber.xml")

    def test_applying_a_dark_style_puts_them_back(self):
        from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
            apply_theme_colors, user_setting_color_dict
        )
        apply_theme_colors("light_blue.xml")
        apply_theme_colors("dark_amber.xml")
        assert user_setting_color_dict["minimap_background_color"] == \
            DARK_COLORS["minimap_background_color"]
