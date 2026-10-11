"""Tests for the highlighter that paints a syntax engine's categories, and for choosing a highlighter."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCursor, QTextDocument
from PySide6.QtWidgets import QApplication, QPlainTextDocumentLayout

from je_editor.adapters.syntax.tree_sitter_engine import TreeSitterEngine, shared_syntax_engine
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.syntax.syntax_model import LineSpan, NoSyntaxEngine, SyntaxCategory
from je_editor.plugins import _programming_language_plugins, register_programming_language
from je_editor.pyside_ui.code.syntax.generic_syntax import GenericHighlighter
from je_editor.pyside_ui.code.syntax.highlight_rules import (
    make_format, plugin_rules, regex_rules, word_rules
)
from je_editor.pyside_ui.code.syntax.highlighter_factory import (
    CLASSIC_ENGINE, SYNTAX_ENGINE_SETTING, build_highlighter, dispose_highlighter,
    syntax_engine_for
)
from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
from je_editor.pyside_ui.code.syntax.syntax_setting import syntax_extend_setting_dict
from je_editor.pyside_ui.code.syntax.tree_sitter_highlighter import (
    CATEGORY_COLOURS, SINGLE_REPAINT_LIMIT, TreeSitterHighlighter, _merged, category_formats
)
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

pytestmark = pytest.mark.usefixtures("qapp")
UTF16_UNIT_BYTES = 2


def new_document(text: str) -> QTextDocument:
    document = QTextDocument()
    document.setDocumentLayout(QPlainTextDocumentLayout(document))
    document.setPlainText(text)
    return document


def highlighted(file_name: str | None, text: str, engine=None):
    """A document holding *text*, already coloured by the highlighter chosen for *file_name*."""
    document = new_document(text)
    highlighter = build_highlighter(document, file_name, engine or shared_syntax_engine())
    highlighter.rehighlight()
    return highlighter, document


def coloured(document: QTextDocument, line: int) -> list[tuple[str, str]]:
    """Each coloured run of a 1-based line as (text, theme colour key)."""
    keys = {colour.name(): key for key, colour in actually_color_dict.items()
            if key.startswith("syntax_")}
    block = document.findBlockByNumber(line - 1)
    units = block.text().encode("utf-16-le")
    return [
        (units[run.start * UTF16_UNIT_BYTES:(run.start + run.length) * UTF16_UNIT_BYTES]
         .decode("utf-16-le"),
         keys.get(run.format.foreground().color().name(), run.format.foreground().color().name()))
        for run in block.layout().formats()
    ]


def deliver_deferred_deletes() -> None:
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.processEvents()


def attached_highlighters(document: QTextDocument) -> list[QSyntaxHighlighter]:
    return [child for child in document.children()
            if isinstance(child, QSyntaxHighlighter) and child.document() is document]


class TestColours:
    def test_a_python_definition(self):
        _highlighter, document = highlighted("a.py", "def greet(self): return 1  # done\n")
        assert coloured(document, 1) == [
            ("def", "syntax_keyword_color"), ("greet", "syntax_function_color"),
            ("self", "syntax_self_color"), ("return", "syntax_keyword_color"),
            ("1", "syntax_number_color"), ("# done", "syntax_comment_color")]

    def test_an_interpolation_is_not_painted_as_string(self):
        _highlighter, document = highlighted("a.py", 'x = f"hi {name}!"\n')
        assert coloured(document, 1) == [
            ('f"hi ', "syntax_string_color"), ('!"', "syntax_string_color")]

    def test_builtins_types_and_escapes(self):
        _highlighter, document = highlighted("a.py", 'class Abc: pass\nprint("a\\n", True)\n')
        assert coloured(document, 1) == [
            ("class", "syntax_keyword_color"), ("Abc", "syntax_builtin_color"),
            ("pass", "syntax_keyword_color")]
        assert coloured(document, 2) == [
            ("print", "syntax_builtin_color"), ('"a', "syntax_string_color"),
            ("\\n", "syntax_builtin_color"), ('"', "syntax_string_color"),
            ("True", "syntax_keyword_color")]

    def test_json_keys_and_values(self):
        _highlighter, document = highlighted("a.json", '{"key": ["value", 1, null]}')
        assert coloured(document, 1) == [
            ('"key"', "syntax_keyword_color"), ('"value"', "syntax_string_color"),
            ("1", "syntax_number_color"), ("null", "syntax_keyword_color")]

    def test_javascript(self):
        _highlighter, document = highlighted("a.js", "function run() { return 'x'; }\n")
        assert coloured(document, 1)[:3] == [
            ("function", "syntax_keyword_color"), ("run", "syntax_function_color"),
            ("return", "syntax_keyword_color")]

    def test_columns_after_wide_characters(self):
        _highlighter, document = highlighted("a.py", 'x = "中文😀" + 1  # 註解😀\n')
        assert coloured(document, 1) == [
            ('"中文😀"', "syntax_string_color"), ("1", "syntax_number_color"),
            ("# 註解😀", "syntax_comment_color")]

    def test_a_string_over_several_lines(self):
        _highlighter, document = highlighted("a.py", 'x = """one\ntwo\nthree"""\ny = 1\n')
        assert [coloured(document, line) for line in (1, 2, 3, 4)] == [
            [('"""one', "syntax_string_color")], [("two", "syntax_string_color")],
            [('three"""', "syntax_string_color")], [("1", "syntax_number_color")]]

    def test_every_category_has_a_format(self):
        assert set(category_formats()) == set(SyntaxCategory)

    def test_every_colour_a_category_uses_is_in_the_theme(self):
        assert all(key in actually_color_dict for key in CATEGORY_COLOURS.values())

    def test_a_category_without_a_colour_gets_an_empty_format(self):
        assert category_formats()[SyntaxCategory.VARIABLE].foreground().style().name == "NoBrush"


class TestFollowingEdits:
    """An edit can change the syntax of lines Qt would not repaint by itself."""

    BODY = 'a = 1\nb = 2\nc = 3\n"""\n'

    def test_a_string_opened_above_reaches_the_lines_below_at_once(self):
        _highlighter, document = highlighted("a.py", self.BODY)
        assert coloured(document, 2) == [("2", "syntax_number_color")]
        QTextCursor(document).insertText('"""\n')
        assert [coloured(document, line) for line in (2, 3, 4, 5)] == [
            [("a = 1", "syntax_string_color")], [("b = 2", "syntax_string_color")],
            [("c = 3", "syntax_string_color")], [('"""', "syntax_string_color")]]

    def test_removing_it_puts_the_lines_back(self):
        _highlighter, document = highlighted("a.py", '"""\n' + self.BODY)
        assert coloured(document, 3) == [("b = 2", "syntax_string_color")]
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        assert [coloured(document, line) for line in (1, 2, 3)] == [
            [("1", "syntax_number_color")], [("2", "syntax_number_color")],
            [("3", "syntax_number_color")]]

    def test_a_line_above_the_edit_is_repainted_on_the_next_turn(self, qtbot):
        _highlighter, document = highlighted("a.py", "foo(\n    1,\n")
        assert coloured(document, 1) == []
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(")")
        qtbot.waitUntil(lambda: coloured(document, 1) == [("foo", "syntax_function_color")])

    def test_typing_keeps_the_line_right(self):
        _highlighter, document = highlighted("a.py", "value = 1\n")
        cursor = QTextCursor(document)
        cursor.insertText("# ")
        assert coloured(document, 1) == [("# value = 1", "syntax_comment_color")]
        cursor.deletePreviousChar()
        cursor.deletePreviousChar()
        assert coloured(document, 1) == [("1", "syntax_number_color")]

    def test_undo_and_redo_are_followed(self):
        _highlighter, document = highlighted("a.py", "value = 1\n")
        QTextCursor(document).insertText("# ")
        document.undo()
        assert coloured(document, 1) == [("1", "syntax_number_color")]
        document.redo()
        assert coloured(document, 1) == [("# value = 1", "syntax_comment_color")]

    def test_replacing_the_whole_text(self):
        _highlighter, document = highlighted("a.py", "value = 1\n")
        document.setPlainText("def f(): pass\n")
        assert coloured(document, 1)[:2] == [
            ("def", "syntax_keyword_color"), ("f", "syntax_function_color")]


class ScriptedSession:
    """A session that reports whatever the test tells it to."""

    language_id = "scripted"
    has_errors = False

    def __init__(self) -> None:
        self.next_report: LineSpan | None = None
        self.texts: list[str] = []

    def update(self, text: str) -> LineSpan | None:
        self.texts.append(text)
        report, self.next_report = self.next_report, None
        return report

    def spans(self, line: int) -> tuple:
        del line
        return ()

    def regions(self) -> tuple:
        return ()


class Recording(TreeSitterHighlighter):
    """Writes down every line it is asked to paint."""

    def __init__(self, document: QTextDocument, session: ScriptedSession) -> None:
        self.painted: list[int] = []
        super().__init__(document, session)

    def highlightBlock(self, text: str) -> None:
        self.painted.append(self.currentBlock().blockNumber() + 1)
        super().highlightBlock(text)


@pytest.fixture()
def scripted():
    """A hundred-line document with a scripted session; painting starts from a clean record."""
    session = ScriptedSession()
    document = new_document("\n".join(f"line {number}" for number in range(1, 101)))
    highlighter = Recording(document, session)
    highlighter.rehighlight()
    QApplication.processEvents()
    highlighter.painted.clear()
    yield SimpleNamespace(session=session, document=document, highlighter=highlighter)
    highlighter.detach()


def type_at(document: QTextDocument, line: int) -> None:
    QTextCursor(document.findBlockByNumber(line - 1)).insertText("x")


class TestRepaintingBeyondTheEdit:
    def test_nothing_reported_paints_the_edited_line_only(self, scripted):
        type_at(scripted.document, 3)
        QApplication.processEvents()
        assert scripted.highlighter.painted == [3]

    def test_lines_after_the_edit_are_painted_in_the_same_pass(self, scripted):
        scripted.session.next_report = LineSpan(3, 7)
        type_at(scripted.document, 3)
        assert scripted.highlighter.painted == [3, 4, 5, 6, 7]

    def test_the_pass_stops_where_the_report_ends(self, scripted):
        scripted.session.next_report = LineSpan(3, 5)
        type_at(scripted.document, 3)
        scripted.highlighter.painted.clear()
        type_at(scripted.document, 4)
        assert scripted.highlighter.painted == [4]

    def test_lines_before_the_edit_are_painted_on_the_next_turn(self, scripted, qtbot):
        scripted.session.next_report = LineSpan(2, 5)
        type_at(scripted.document, 5)
        assert scripted.highlighter.painted == [5]
        qtbot.waitUntil(lambda: scripted.highlighter.painted == [5, 2, 3, 4])

    def test_many_lines_before_the_edit_repaint_the_document_once(self, scripted, qtbot):
        scripted.session.next_report = LineSpan(1, SINGLE_REPAINT_LIMIT + 20)
        type_at(scripted.document, SINGLE_REPAINT_LIMIT + 20)
        qtbot.waitUntil(lambda: len(scripted.highlighter.painted) > 1)
        assert scripted.highlighter.painted[1:] == list(range(1, 101))

    def test_the_session_gets_the_text_with_plain_newlines(self, scripted):
        type_at(scripted.document, 1)
        assert scripted.session.texts[-1].startswith("xline 1\nline 2\n")
        assert " " not in scripted.session.texts[-1]

    def test_a_detached_highlighter_does_nothing(self, scripted):
        calls = len(scripted.session.texts)
        scripted.highlighter.detach()
        type_at(scripted.document, 3)
        QApplication.processEvents()
        assert (len(scripted.session.texts), scripted.highlighter.painted) == (calls, [])
        assert scripted.highlighter.document() is None

    def test_detaching_twice_is_harmless(self, scripted):
        scripted.highlighter.detach()
        scripted.highlighter.detach()
        assert scripted.highlighter.document() is None

    @pytest.mark.parametrize("waiting, changed, shift, expected", [
        (None, LineSpan(4, 6), 0, LineSpan(4, 6)),
        (LineSpan(10, 12), LineSpan(4, 6), 0, LineSpan(4, 12)),
        (LineSpan(10, 12), LineSpan(4, 6), 3, LineSpan(4, 15)),
        (LineSpan(10, 12), LineSpan(14, 15), -3, LineSpan(7, 15)),
        (LineSpan(1, 2), LineSpan(1, 1), -5, LineSpan(1, 2)),
        (LineSpan(90, 99), LineSpan(95, 96), 50, LineSpan(90, 100)),
    ])
    def test_waiting_lines_are_widened_the_way_the_edit_moved_them(
            self, waiting, changed, shift, expected):
        assert _merged(waiting, changed, shift, line_count=100) == expected


@pytest.fixture()
def _plugins_untouched():
    """Leave the plugin registry and the legacy table as they were."""
    saved_plugins = dict(_programming_language_plugins)
    saved_legacy = dict(syntax_extend_setting_dict)
    yield
    _programming_language_plugins.clear()
    _programming_language_plugins.update(saved_plugins)
    syntax_extend_setting_dict.clear()
    syntax_extend_setting_dict.update(saved_legacy)


@pytest.mark.usefixtures("_plugins_untouched")
class TestPluginKeywords:
    """Keywords a plugin registers for a suffix are laid over whichever highlighter is used."""

    WORDS = {"automation": {"words": {"AC_click"}, "color": "syntax_self_color"}}

    def test_over_the_syntax_engine(self):
        register_programming_language(".json", self.WORDS)
        _highlighter, document = highlighted("steps.json", '["AC_click", "other"]')
        assert coloured(document, 1) == [
            ('"', "syntax_string_color"), ("AC_click", "syntax_self_color"),
            ('"', "syntax_string_color"), ('"other"', "syntax_string_color")]

    def test_over_the_generic_highlighter(self):
        register_programming_language(".yaml", self.WORDS)
        highlighter, document = highlighted("steps.yaml", "- AC_click: 1\n")
        assert isinstance(highlighter, GenericHighlighter)
        assert ("AC_click", "syntax_self_color") in coloured(document, 1)

    def test_a_comment_wins_over_a_plugin_keyword_in_the_generic_highlighter(self):
        register_programming_language(".yaml", self.WORDS)
        _highlighter, document = highlighted("steps.yaml", "# AC_click here\n")
        assert coloured(document, 1) == [("# AC_click here", "syntax_comment_color")]

    def test_over_the_python_highlighter_for_an_unknown_suffix(self):
        register_programming_language(".robot", self.WORDS)
        highlighter, document = highlighted("steps.robot", "AC_click now\n")
        assert isinstance(highlighter, PythonHighlighter)
        assert coloured(document, 1) == [("AC_click", "syntax_self_color")]

    def test_rules_and_a_direct_colour(self):
        register_programming_language(
            ".json", {}, {"marker": {"rules": (r"@\w+",), "color": QColor(1, 2, 3)}})
        _highlighter, document = highlighted("steps.json", '["@tag"]')
        assert ("@tag", QColor(1, 2, 3).name()) in coloured(document, 1)

    def test_the_legacy_table_still_counts(self):
        syntax_extend_setting_dict[".cfgx"] = self.WORDS
        assert len(plugin_rules(".cfgx")) == 1

    def test_no_plugin_means_no_rules(self):
        assert plugin_rules(".nothing-registered") == []

    def test_rule_builders(self):
        assert len(regex_rules({"a": {"rules": ("x", "y"), "color": "syntax_number_color"}})) == 2
        assert len(word_rules({"a": {"words": ("x",), "color": "syntax_number_color"}})) == 1
        assert regex_rules({"a": {"color": "syntax_number_color"}}) == []

    def test_an_unknown_colour_key_gives_a_format_without_a_colour(self):
        assert make_format("no_such_colour").foreground().style().name == "NoBrush"


@pytest.fixture()
def _engine_setting_untouched():
    saved = user_setting_dict.get(SYNTAX_ENGINE_SETTING)
    yield
    user_setting_dict[SYNTAX_ENGINE_SETTING] = saved


@pytest.mark.usefixtures("_engine_setting_untouched")
class TestChoosingAHighlighter:
    @pytest.mark.parametrize("file_name, language", [
        ("main.py", "python"), ("stubs.pyi", "python"), ("app.js", "javascript"),
        ("data.json", "json"), (None, "python"),
    ])
    def test_a_language_the_engine_knows_uses_it(self, file_name, language):
        highlighter, _document = highlighted(file_name, "")
        assert isinstance(highlighter, TreeSitterHighlighter)
        assert highlighter.session.language_id == language

    @pytest.mark.parametrize("file_name, expected", [
        ("app.ts", GenericHighlighter), ("main.rs", GenericHighlighter),
        ("notes.txt", PythonHighlighter), ("Makefile", PythonHighlighter),
    ])
    def test_other_files_keep_the_older_highlighters(self, file_name, expected):
        highlighter, _document = highlighted(file_name, "")
        assert type(highlighter) is expected

    @pytest.mark.parametrize("file_name, expected", [
        ("main.py", PythonHighlighter), ("data.json", GenericHighlighter),
        (None, PythonHighlighter),
    ])
    def test_the_classic_setting_turns_the_engine_off(self, file_name, expected):
        user_setting_dict[SYNTAX_ENGINE_SETTING] = CLASSIC_ENGINE
        highlighter, _document = highlighted(file_name, "")
        assert type(highlighter) is expected

    def test_the_classic_python_highlighter_still_colours(self):
        user_setting_dict[SYNTAX_ENGINE_SETTING] = CLASSIC_ENGINE
        _highlighter, document = highlighted("main.py", "def f(self): return 1\n")
        assert ("def", "syntax_keyword_color") in coloured(document, 1)
        assert ("self", "syntax_self_color") in coloured(document, 1)

    def test_an_engine_that_knows_nothing_falls_back(self):
        highlighter, _document = highlighted("main.py", "", engine=NoSyntaxEngine())
        assert type(highlighter) is PythonHighlighter

    def test_a_grammar_that_will_not_load_falls_back(self):
        def missing():
            raise ImportError("not installed")

        from je_editor.adapters.syntax.grammar_table import GrammarSpec
        engine = TreeSitterEngine([GrammarSpec("json", (".json",), missing)])
        highlighter, _document = highlighted("data.json", "", engine=engine)
        assert type(highlighter) is GenericHighlighter

    def test_a_window_with_services_uses_their_engine(self):
        services = EditorServices()
        assert syntax_engine_for(SimpleNamespace(services=services)) is services.syntax

    @pytest.mark.parametrize("window", [None, SimpleNamespace(), MagicMock()])
    def test_a_window_without_services_uses_the_shared_engine(self, window):
        assert syntax_engine_for(window) is shared_syntax_engine()


class TestReplacingAHighlighter:
    @pytest.fixture()
    def editor(self):
        with patch(
            "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
        ) as venv:
            venv.return_value = MagicMock(exists=MagicMock(return_value=False))
            parent = MagicMock()
            parent.current_file = None
            from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
            code_editor = CodeEditor(parent)
        yield code_editor
        code_editor.close()
        code_editor.deleteLater()

    def test_only_the_new_one_stays_on_the_document(self, editor):
        for name in ("main.py", "app.ts", "notes.txt", "data.json"):
            editor.current_file = name
            editor.reset_highlighter()
        deliver_deferred_deletes()
        assert attached_highlighters(editor.document()) == [editor.highlighter]
        assert sum(isinstance(child, QSyntaxHighlighter)
                   for child in editor.document().children()) == 1

    def test_the_text_is_recoloured_for_the_new_language(self, editor):
        editor.setPlainText('{"key": 1}')
        editor.current_file = "data.json"
        editor.reset_highlighter()
        editor.highlighter.rehighlight()
        assert coloured(editor.document(), 1) == [
            ('"key"', "syntax_keyword_color"), ("1", "syntax_number_color")]

    def test_disposing_nothing_is_allowed(self):
        dispose_highlighter(None)

    def test_disposing_does_not_look_like_an_edit(self):
        for file_name in ("main.py", "app.ts", "notes.txt"):
            highlighter, document = highlighted(file_name, "x = 1\n")
            edits: list[int] = []
            document.contentsChange.connect(lambda position, *_: edits.append(position))
            dispose_highlighter(highlighter)
            assert (edits, document.signalsBlocked()) == ([], False)

    def test_the_python_highlighter_can_be_told_its_suffix(self):
        document = new_document("")
        assert len(PythonHighlighter(document, suffix=".py").highlight_rules) > len(
            PythonHighlighter(document, suffix=".unknown").highlight_rules)

    def test_disposing_takes_a_highlighter_off_its_document(self):
        for file_name in ("main.py", "app.ts", "notes.txt"):
            highlighter, document = highlighted(file_name, "x = 1\n")
            dispose_highlighter(highlighter)
            assert attached_highlighters(document) == []
