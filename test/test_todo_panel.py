"""Tests for the TODO comment scanner and the TODO panel widget."""
from __future__ import annotations

import textwrap

import pytest

from je_editor.pyside_ui.main_ui.todo_panel.todo_panel_widget import (
    ALL_TAGS_FILTER,
    TodoPanelWidget,
    jump_to_item_line,
    open_todo_item,
    resolve_todo_root,
)
from je_editor.utils.file_scan.todo_scanner import (
    DEFAULT_TAGS,
    TodoItem,
    build_tag_pattern,
    scan_project_todos,
    scan_text,
)


def _scan(source: str, path: str = "sample.py") -> list[TodoItem]:
    return scan_text(textwrap.dedent(source), path, build_tag_pattern())


class TestBuildTagPattern:
    """Pattern construction, including the degenerate empty case."""

    def test_default_tags_match(self):
        assert build_tag_pattern().search("# TODO: ship it") is not None

    def test_empty_tag_list_never_matches(self):
        assert build_tag_pattern([]).search("# TODO: ship it") is None

    def test_blank_tags_are_ignored(self):
        assert build_tag_pattern(["", "  "]).search("# TODO: ship it") is None

    def test_custom_tag_is_matched(self):
        assert build_tag_pattern(["REVIEW"]).search("# REVIEW: check this") is not None


class TestScanText:
    """Tag detection, message extraction and false-positive avoidance."""

    def test_finds_python_todo(self):
        found = _scan("# TODO: write the docs\n")
        assert (found[0].tag, found[0].message, found[0].line) == ("TODO", "write the docs", 1)

    def test_finds_fixme(self):
        assert _scan("# FIXME broken on Windows\n")[0].tag == "FIXME"

    def test_tag_match_is_case_insensitive_but_reported_upper(self):
        assert _scan("# todo: lowercase tag\n")[0].tag == "TODO"

    def test_c_style_comment_is_matched(self):
        assert _scan("// TODO: port this\n")[0].message == "port this"

    def test_block_comment_trailer_is_stripped(self):
        assert _scan("/* TODO: port this */\n")[0].message == "port this"

    def test_html_comment_is_matched(self):
        assert _scan("<!-- TODO: add alt text -->\n")[0].message == "add alt text"

    def test_plain_string_is_not_a_todo(self):
        # Without a comment marker this is ordinary code, not a task.
        assert _scan('message = "TODO items are tracked elsewhere"\n') == []

    def test_word_inside_identifier_is_not_matched(self):
        assert _scan("# TODOLIST = []\n") == []

    def test_reports_every_line(self):
        found = _scan("""
            # TODO: first
            code = 1
            # FIXME: second
            """)
        assert [item.tag for item in found] == ["TODO", "FIXME"]

    def test_line_numbers_are_one_based(self):
        found = _scan("code = 1\n# TODO: second line\n")
        assert found[0].line == 2

    def test_relative_path_is_kept(self):
        assert _scan("# TODO: x\n", "pkg/mod.py")[0].path == "pkg/mod.py"

    def test_empty_message_is_allowed(self):
        assert _scan("# TODO\n")[0].message == ""

    def test_every_default_tag_is_detected(self):
        for tag in DEFAULT_TAGS:
            assert _scan(f"# {tag}: something\n")[0].tag == tag


class TestScanProjectTodos:
    """Project-wide scanning, pruning and cancellation."""

    @staticmethod
    def _project(tmp_path):
        (tmp_path / "main.py").write_text("# TODO: main work\n", encoding="utf-8")
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "helper.py").write_text("# FIXME: helper bug\n", encoding="utf-8")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cached.py").write_text("# TODO: ignored\n", encoding="utf-8")
        (tmp_path / "blob.bin").write_bytes(b"# TODO: binary\x00")
        return tmp_path

    def test_finds_todos_across_files(self, tmp_path):
        found = scan_project_todos(self._project(tmp_path))
        assert {item.tag for item in found} == {"TODO", "FIXME"}

    def test_ignored_directories_are_skipped(self, tmp_path):
        found = scan_project_todos(self._project(tmp_path))
        assert not any("__pycache__" in item.path for item in found)

    def test_binary_files_are_skipped(self, tmp_path):
        found = scan_project_todos(self._project(tmp_path))
        assert not any(item.path.endswith(".bin") for item in found)

    def test_missing_root_returns_empty(self, tmp_path):
        assert scan_project_todos(tmp_path / "nope") == []

    def test_should_stop_aborts_the_scan(self, tmp_path):
        assert scan_project_todos(self._project(tmp_path), should_stop=lambda: True) == []

    def test_limit_caps_the_result(self, tmp_path):
        target = tmp_path / "many.py"
        target.write_text("\n".join(f"# TODO: item {i}" for i in range(20)), encoding="utf-8")
        assert len(scan_project_todos(tmp_path, limit=5)) == 5

    def test_custom_tags_only(self, tmp_path):
        (tmp_path / "main.py").write_text("# TODO: a\n# FIXME: b\n", encoding="utf-8")
        found = scan_project_todos(tmp_path, tags=("FIXME",))
        assert [item.tag for item in found] == ["FIXME"]


class _FakeCodeEdit:
    def __init__(self):
        self.jumped: list[int] = []

    def jump_to_line(self, line: int) -> bool:
        self.jumped.append(line)
        return True


class _FakeMainWindow:
    def __init__(self, working_dir=None):
        self.working_dir = working_dir
        self.opened: list = []

    def go_to_new_tab(self, file_path) -> None:
        self.opened.append(file_path)


class TestResolveTodoRoot:
    """Root resolution mirrors quick open's behaviour."""

    def test_uses_working_dir_when_valid(self, tmp_path):
        assert resolve_todo_root(_FakeMainWindow(str(tmp_path))) == str(tmp_path)

    def test_falls_back_without_working_dir(self):
        import os
        assert resolve_todo_root(_FakeMainWindow(None)) == os.getcwd()

    def test_falls_back_without_a_window(self):
        import os
        assert resolve_todo_root(None) == os.getcwd()


class TestOpenTodoItem:
    """Opening an item must degrade gracefully without a real window."""

    @staticmethod
    def _item() -> TodoItem:
        return TodoItem(tag="TODO", message="x", path="pkg/mod.py", line=9)

    def test_no_window_returns_false(self, tmp_path):
        assert open_todo_item(None, str(tmp_path), self._item()) is False

    def test_window_without_tab_api_returns_false(self, tmp_path):
        assert open_todo_item(object(), str(tmp_path), self._item()) is False

    def test_opens_the_expected_path(self, tmp_path):
        window = _FakeMainWindow()
        assert open_todo_item(window, str(tmp_path), self._item()) is True
        assert window.opened[0].name == "mod.py"

    def test_jump_without_tab_widget_returns_false(self):
        assert jump_to_item_line(_FakeMainWindow(), 5) is False


@pytest.mark.usefixtures("qapp")
class TestTodoPanelWidget:
    """Scanning, filtering and teardown in the panel."""

    @staticmethod
    def _project(tmp_path):
        (tmp_path / "main.py").write_text("# TODO: main work\n", encoding="utf-8")
        (tmp_path / "other.py").write_text("# FIXME: other bug\n", encoding="utf-8")
        return tmp_path

    def _panel(self, qtbot, tmp_path) -> TodoPanelWidget:
        panel = TodoPanelWidget(main_window=None, root=str(self._project(tmp_path)))
        qtbot.addWidget(panel)
        qtbot.waitUntil(lambda: panel.result_tree.topLevelItemCount() > 0, timeout=10000)
        return panel

    def test_scan_populates_the_tree(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        assert panel.result_tree.topLevelItemCount() == 2
        panel.close()

    def test_all_tags_filter_shows_everything(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        assert panel.tag_filter.currentData() == ALL_TAGS_FILTER
        assert len(panel.visible_items()) == 2
        panel.close()

    def test_tag_filter_narrows_the_list(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        panel.tag_filter.setCurrentIndex(panel.tag_filter.findData("FIXME"))
        assert [item.tag for item in panel.visible_items()] == ["FIXME"]
        panel.close()

    def test_tag_filter_updates_the_tree(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        panel.tag_filter.setCurrentIndex(panel.tag_filter.findData("FIXME"))
        assert panel.result_tree.topLevelItemCount() == 1
        panel.close()

    def test_rescan_while_running_is_ignored(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        panel.start_scan()
        first_thread = panel._scan_thread
        panel.start_scan()
        assert panel._scan_thread is first_thread
        qtbot.waitUntil(lambda: not first_thread.isRunning(), timeout=10000)
        panel.close()

    def test_closing_stops_the_scan_thread(self, qtbot, tmp_path):
        panel = self._panel(qtbot, tmp_path)
        panel.close()
        assert not panel._scan_thread.isRunning()

    def test_closing_immediately_is_safe(self, tmp_path):
        panel = TodoPanelWidget(main_window=None, root=str(self._project(tmp_path)))
        panel.close()
        assert not panel._scan_thread.isRunning()

    def test_empty_project_reports_no_items(self, qtbot, tmp_path):
        panel = TodoPanelWidget(main_window=None, root=str(tmp_path))
        qtbot.addWidget(panel)
        qtbot.waitUntil(lambda: not panel._scan_thread.isRunning(), timeout=10000)
        assert panel.visible_items() == []
        panel.close()
