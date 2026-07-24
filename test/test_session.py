"""Tests for open-file session serialisation and restore filtering."""
from __future__ import annotations

from je_editor.utils.session.open_files_session import (
    MAX_SESSION_FILES,
    SESSION_SETTING_KEY,
    collect_open_files,
    restorable_files,
)


class TestCollectOpenFiles:
    """Turning the live tab list into something storable."""

    def test_keeps_tab_order(self):
        assert collect_open_files(["b.py", "a.py"]) == ["b.py", "a.py"]

    def test_drops_unsaved_tabs(self):
        # A tab that was never saved has current_file None.
        assert collect_open_files(["a.py", None, "b.py"]) == ["a.py", "b.py"]

    def test_drops_empty_strings(self):
        assert collect_open_files(["", "a.py"]) == ["a.py"]

    def test_drops_duplicates_keeping_first(self):
        assert collect_open_files(["a.py", "b.py", "a.py"]) == ["a.py", "b.py"]

    def test_empty_input_yields_empty_list(self):
        assert collect_open_files([]) == []

    def test_result_is_capped(self):
        many = [f"file_{index}.py" for index in range(MAX_SESSION_FILES + 10)]
        assert len(collect_open_files(many)) == MAX_SESSION_FILES


class TestRestorableFiles:
    """A stored session must never be trusted blindly."""

    @staticmethod
    def _files(tmp_path, count=2):
        paths = []
        for index in range(count):
            target = tmp_path / f"file_{index}.py"
            target.write_text("x = 1\n", encoding="utf-8")
            paths.append(str(target))
        return paths

    def test_existing_files_are_restorable(self, tmp_path):
        paths = self._files(tmp_path)
        assert restorable_files(paths) == paths

    def test_missing_files_are_skipped(self, tmp_path):
        paths = self._files(tmp_path, 1)
        assert restorable_files(paths + [str(tmp_path / "gone.py")]) == paths

    def test_directories_are_skipped(self, tmp_path):
        assert restorable_files([str(tmp_path)]) == []

    def test_already_open_files_are_skipped(self, tmp_path):
        first, second = self._files(tmp_path)
        assert restorable_files([first, second], already_open=[first]) == [second]

    def test_duplicates_are_collapsed(self, tmp_path):
        first, _second = self._files(tmp_path)
        assert restorable_files([first, first]) == [first]

    def test_non_list_setting_is_ignored(self):
        # An old settings file may hold a bare string instead of a list.
        assert restorable_files("not-a-list") == []

    def test_none_setting_is_ignored(self):
        assert restorable_files(None) == []

    def test_non_string_entries_are_ignored(self, tmp_path):
        paths = self._files(tmp_path, 1)
        assert restorable_files([42, None, {"a": 1}] + paths) == paths

    def test_empty_string_entries_are_ignored(self, tmp_path):
        paths = self._files(tmp_path, 1)
        assert restorable_files(["", *paths]) == paths

    def test_result_is_capped(self, tmp_path):
        paths = self._files(tmp_path, MAX_SESSION_FILES + 5)
        assert len(restorable_files(paths)) == MAX_SESSION_FILES

    def test_overlong_path_does_not_raise(self):
        assert restorable_files(["\0bad" + "x" * 5000]) == []


class TestSessionSettingKey:
    """The key must match the one shipped in the default settings dict."""

    def test_key_is_registered_in_defaults(self):
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        assert SESSION_SETTING_KEY in user_setting_dict

    def test_restore_flag_is_registered_in_defaults(self):
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        assert user_setting_dict["restore_session"] is True


class TestEditorMainSessionGuard:
    """The restore step must be one-shot and must never raise."""

    @staticmethod
    def _window():
        # A bare instance is enough: the helpers only touch class-level state.
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        return EditorMain.__new__(EditorMain)

    def test_restore_flag_defaults_to_false(self):
        assert self._window()._session_restored is False

    def test_restore_runs_only_once(self):
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        window = self._window()
        calls = []
        window._open_file_paths = lambda: calls.append("read") or []
        window.go_to_new_tab = lambda path: None
        EditorMain._restore_open_files_session(window)
        EditorMain._restore_open_files_session(window)
        assert calls == ["read"]

    def test_restore_survives_a_broken_tab_list(self):
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        window = self._window()

        def explode():
            raise RuntimeError("tab widget is gone")

        window._open_file_paths = explode
        # A failure here must be logged and swallowed, never block startup.
        EditorMain._restore_open_files_session(window)

    def test_save_survives_a_broken_tab_list(self):
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        window = self._window()

        def explode():
            raise RuntimeError("tab widget is gone")

        window._open_file_paths = explode
        EditorMain._save_open_files_session(window)
