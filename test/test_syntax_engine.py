"""Tests for the syntax model, the Tree-sitter engine and the syntax language service."""
from __future__ import annotations

import gc
import sys
from types import SimpleNamespace

import pytest

from je_editor.adapters.default_services import build_default_services
from je_editor.adapters.syntax.grammar_table import (
    BUILTIN_GRAMMARS, CAPTURE_CATEGORIES, HIGHLIGHTS_QUERY_FILE, QUERY_DIRECTORY,
    REGIONS_QUERY_FILE, GrammarSpec, category_for, own_query
)
from je_editor.adapters.syntax.syntax_language_service import SERVICE_NAME, SyntaxLanguageService
from je_editor.adapters.syntax.tree_sitter_engine import (
    MAX_SOURCE_BYTES, SPAN_CHUNK_LINES, TreeSitterEngine, changed_bytes, load_grammar, point_at,
    shared_syntax_engine, suffix_of
)
from je_editor.core.diagnostics.diagnostic_model import Position, TextRange
from je_editor.core.document.document_model import TextDocument
from je_editor.core.language.language_capability import LanguageCapability
from je_editor.core.language.language_request import LanguageReply, LanguageRequest
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.syntax.syntax_model import (
    LineSpan, NoSyntaxEngine, RegionKind, StructuralRegion, SyntaxCategory, SyntaxEngine,
    SyntaxSession, SyntaxSpan
)
from je_editor.core.uri.resource_uri import to_uri

PYTHON = (
    "import os\n"
    "\n"
    "\n"
    "class Greeter:\n"
    "    def greet(self, name: str) -> str:\n"
    "        # say hello\n"
    '        return f"hi {name}\\n" + str(MAX)\n'
)
LANGUAGES = [spec.language_id for spec in BUILTIN_GRAMMARS]


@pytest.fixture(scope="module")
def engine():
    return TreeSitterEngine()


@pytest.fixture()
def python(engine):
    session = engine.open_session("python")
    session.update(PYTHON)
    return session


def shown(session, line: int) -> list[tuple[str, str]]:
    """Each span of a line as (text, category), in the order the session gives them."""
    text = session._lines[line - 1]
    return [(text[span.column - 1:span.column - 1 + span.length], span.category.value)
            for span in session.spans(line)]


class TestTheModel:
    def test_a_region_on_one_line_cannot_fold(self):
        region = StructuralRegion(RegionKind.FUNCTION, TextRange.from_lines(3, 1, 3, 20), "f")
        assert region.is_multiline is False

    def test_a_region_over_several_lines_can(self):
        region = StructuralRegion(RegionKind.CLASS, TextRange.from_lines(3, 1, 9, 1))
        assert (region.is_multiline, region.name) == (True, "")

    def test_spans_and_line_spans_are_values(self):
        # Equal fields make one value, so a set keeps a single copy of it.
        fields = (1, 3, SyntaxCategory.KEYWORD)
        spans = {SyntaxSpan(*fields), SyntaxSpan(*fields), SyntaxSpan(2, 3, SyntaxCategory.KEYWORD)}
        lines = {LineSpan(2, 5), LineSpan(*(2, 5)), LineSpan(2, 6)}
        assert (len(spans), len(lines)) == (2, 2)

    def test_the_engine_that_knows_nothing(self):
        nothing = NoSyntaxEngine()
        assert (nothing.language_ids(), nothing.language_for("main.py"),
                nothing.open_session("python")) == ((), None, None)

    def test_both_engines_satisfy_the_interface(self, engine):
        assert isinstance(NoSyntaxEngine(), SyntaxEngine)
        assert isinstance(engine, SyntaxEngine)

    def test_a_session_satisfies_the_interface(self, python):
        assert isinstance(python, SyntaxSession)

    def test_services_start_without_a_parser(self):
        assert isinstance(EditorServices().syntax, NoSyntaxEngine)


class TestChoosingALanguage:
    def test_the_built_in_languages_are_available(self, engine):
        assert engine.language_ids() == ("python", "javascript", "json")

    @pytest.mark.parametrize("name, language", [
        ("main.py", "python"), ("stubs.pyi", "python"), ("C:\\src\\Tool.PYW", "python"),
        ("app.js", "javascript"), ("lib/index.mjs", "javascript"), ("view.jsx", "javascript"),
        ("data.json", "json"), ("file:///c:/project/package.json", "json"),
    ])
    def test_a_file_name_path_or_uri_names_its_language(self, engine, name, language):
        assert engine.language_for(name) == language

    @pytest.mark.parametrize("name", ["notes.txt", "app.ts", "Makefile", ".json", "", "dir.py/readme"])
    def test_an_unknown_name_has_no_language(self, engine, name):
        assert engine.language_for(name) is None

    def test_an_unknown_language_opens_no_session(self, engine):
        assert engine.open_session("cobol") is None

    def test_every_session_is_its_own(self, engine):
        first, second = engine.open_session("python"), engine.open_session("python")
        first.update("x = 1\n")
        assert (first is not second, second.spans(1)) == (True, ())

    @pytest.mark.parametrize("name, suffix", [
        ("a.py", ".py"), ("A.PY", ".py"), ("dir/b.tar.gz", ".gz"), ("c:\\x\\y.json", ".json"),
        (".hidden", ""), ("none", ""), ("trailing.", "."),
    ])
    def test_the_suffix_of_a_name(self, name, suffix):
        assert suffix_of(name) == suffix

    def test_the_shared_engine_is_one_object(self):
        assert shared_syntax_engine() is shared_syntax_engine()


class TestCategories:
    def test_keywords_names_and_types(self, python):
        assert shown(python, 4) == [("class", "keyword"), ("Greeter", "type")]

    def test_a_definition_its_receiver_and_its_annotations(self, python):
        assert shown(python, 5) == [
            ("def", "keyword"), ("greet", "function"), ("self", "special_variable"),
            ("name", "variable"), ("str", "type"), ("->", "operator"), ("str", "type")]

    def test_a_comment(self, python):
        assert shown(python, 6) == [("# say hello", "comment")]

    def test_what_is_inside_a_string_comes_after_the_string(self, python):
        assert shown(python, 7) == [
            ("return", "keyword"), ('f"hi {name}\\n"', "string"), ("{name}", "embedded"),
            ("{", "punctuation"), ("name", "variable"), ("}", "punctuation"), ("\\n", "escape"),
            ("+", "operator"), ("str", "builtin"), ("MAX", "constant")]

    def test_an_empty_line_and_a_missing_line_have_nothing(self, python):
        assert (python.spans(2), python.spans(0), python.spans(99)) == ((), (), ())

    def test_a_later_pattern_wins_on_the_same_node(self, python):
        # ``self`` is an identifier (variable) first and the receiver second.
        categories = [span.category for span in python.spans(5) if span.column == 15]
        assert categories == [SyntaxCategory.SPECIAL_VARIABLE]

    def test_javascript(self, engine):
        session = engine.open_session("javascript")
        session.update("class A { run() { return `a ${1} b`; } }\n")
        found = shown(session, 1)
        assert ("class", "keyword") in found and ("run", "function") in found
        assert ("`a ${1} b`", "string") in found and ("1", "number") in found

    def test_a_json_key_is_told_from_a_string_value(self, engine):
        session = engine.open_session("json")
        session.update('{"key": [1, true, null, "v"]}')
        assert shown(session, 1) == [
            ('"key"', "key"), ("1", "number"), ("true", "literal"), ("null", "literal"),
            ('"v"', "string")]

    def test_a_string_over_several_lines_colours_each_of_them(self, engine):
        session = engine.open_session("python")
        session.update('x = """one\ntwo\nthree"""\ny = 1\n')
        assert [shown(session, line)[-1] for line in (1, 2, 3)] == [
            ('"""one', "string"), ("two", "string"), ('three"""', "string")]
        assert ("y", "variable") in shown(session, 4)

    def test_lines_past_the_first_chunk(self, engine):
        session = engine.open_session("python")
        session.update("\n".join(f"value_{index} = {index}" for index in range(SPAN_CHUNK_LINES * 3)))
        line = SPAN_CHUNK_LINES * 2 + 5
        assert shown(session, line) == [
            (f"value_{line - 1}", "variable"), ("=", "operator"), (str(line - 1), "number")]

    @pytest.mark.parametrize("name, category", [
        ("comment", SyntaxCategory.COMMENT), ("function.builtin", SyntaxCategory.BUILTIN),
        ("function.method", SyntaxCategory.FUNCTION), ("string.special.key", SyntaxCategory.KEY),
        ("string.special", SyntaxCategory.STRING), ("punctuation.bracket", SyntaxCategory.PUNCTUATION),
        ("variable.builtin", SyntaxCategory.SPECIAL_VARIABLE), ("no.such.name", None), ("", None),
    ])
    def test_a_capture_name_falls_back_to_its_parent(self, name, category):
        assert category_for(name) is category

    def test_every_category_is_reachable_from_a_capture_name(self):
        assert set(CAPTURE_CATEGORIES.values()) == set(SyntaxCategory)


class TestColumnsCountUtf16Units:
    """Qt and the language server protocol count UTF-16 units, so an emoji is two columns."""

    def test_text_after_wide_characters(self, engine):
        session = engine.open_session("python")
        session.update('x = "中文😀" + y  # 註解😀\n')
        assert [(span.column, span.length, span.category.value) for span in session.spans(1)] == [
            (1, 1, "variable"), (3, 1, "operator"), (5, 6, "string"), (12, 1, "operator"),
            (14, 1, "variable"), (17, 6, "comment")]

    def test_a_region_starting_after_wide_characters(self, engine):
        session = engine.open_session("python")
        session.update('x = "😀"; y = [\n    1,\n]\n')
        collection = session.regions()[0]
        assert (collection.range.start, collection.range.end) == (Position(1, 15), Position(3, 2))

    def test_a_lone_surrogate_does_not_stop_the_analysis(self, engine):
        session = engine.open_session("python")
        session.update('x = "\ud83d" + y\n')
        assert [(span.column, span.category.value) for span in session.spans(1)][-1] == (
            11, "variable")


class TestFollowingAnEdit:
    def test_the_first_text_changes_every_line(self, engine):
        session = engine.open_session("python")
        assert session.update(PYTHON) == LineSpan(1, 8)

    def test_the_same_text_changes_nothing(self, python):
        assert python.update(PYTHON) is None

    def test_typing_in_one_line_changes_that_line(self, python):
        assert python.update(PYTHON.replace("import os", "import oss")) == LineSpan(1, 1)
        assert shown(python, 1) == [("import", "keyword"), ("oss", "variable")]

    # Three statements and a quote left open at the end; a quote added on top closes over them.
    BELOW_AN_OPEN_QUOTE = 'a = 1\nb = 2\nc = 3\n"""\n'

    def test_opening_a_string_reaches_every_line_after_it(self, engine):
        session = engine.open_session("python")
        session.update(self.BELOW_AN_OPEN_QUOTE)
        assert shown(session, 2) == [("b", "variable"), ("=", "operator"), ("2", "number")]
        changed = session.update('"""\n' + self.BELOW_AN_OPEN_QUOTE)
        assert changed.first == 1 and changed.last >= 5
        assert [shown(session, line) for line in (2, 3, 4)] == [
            [("a = 1", "string")], [("b = 2", "string")], [("c = 3", "string")]]
        assert session.has_errors is False

    def test_removing_it_again_puts_the_lines_back(self, engine):
        session = engine.open_session("python")
        session.update('"""\n' + self.BELOW_AN_OPEN_QUOTE)
        changed = session.update(self.BELOW_AN_OPEN_QUOTE)
        assert changed.first == 1 and changed.last >= 4
        assert shown(session, 2) == [("b", "variable"), ("=", "operator"), ("2", "number")]
        assert session.has_errors is True

    def test_an_edit_can_change_a_line_above_it(self, engine):
        session = engine.open_session("python")
        session.update("def f(\n    a,\n")
        changed = session.update("def f(\n    a,\n): pass\n")
        assert changed.first == 1

    def test_adding_and_removing_lines(self, python):
        longer = PYTHON + "\nprint(Greeter())\n"
        assert python.update(longer).last == python.line_count
        assert ("print", "builtin") in shown(python, 9)
        python.update("x = 1\n")
        assert (python.line_count, python.spans(5)) == (2, ())

    def test_emptying_the_text(self, python):
        assert python.update("") == LineSpan(1, 1)
        assert (python.spans(1), python.regions(), python.has_errors) == ((), (), False)

    def test_the_result_matches_a_fresh_analysis(self, engine):
        edited = engine.open_session("python")
        text = PYTHON
        for old, new in (("os", "sys"), ("Greeter", "G"), ("# say hello", "pass  # 中文"),
                         ("        return", "        yield")):
            text = text.replace(old, new, 1)
            edited.update(text)
        fresh = engine.open_session("python")
        fresh.update(text)
        lines = range(1, fresh.line_count + 1)
        assert [edited.spans(line) for line in lines] == [fresh.spans(line) for line in lines]
        assert edited.regions() == fresh.regions()

    @pytest.mark.parametrize("old, new, expected", [
        (b"abc", b"abc", (3, 3, 3)), (b"", b"xyz", (0, 0, 3)), (b"xyz", b"", (0, 3, 0)),
        (b"abcd", b"abXd", (2, 3, 3)), (b"abcabc", b"abc", (3, 6, 3)),
        (b"ab", b"aXXb", (1, 1, 3)),
    ])
    def test_the_smallest_edit_between_two_contents(self, old, new, expected):
        assert changed_bytes(old, new) == expected

    def test_an_edit_never_starts_or_ends_inside_a_character(self):
        old, new = "a中b".encode(), "a丮b".encode()
        # The two characters share their first two bytes; the edit covers them whole.
        assert changed_bytes(old, new) == (1, 4, 4)
        assert changed_bytes("é".encode(), "è".encode()) == (0, 2, 2)

    def test_a_byte_offset_as_row_and_column(self):
        source = "ab\n中c\n".encode()
        assert [point_at(source, offset) for offset in (0, 2, 3, 6, 8)] == [
            (0, 0), (0, 2), (1, 0), (1, 3), (2, 0)]


class TestStructuralRegions:
    def test_classes_functions_and_their_names(self, python):
        assert [(region.kind, region.name, region.range.start.line, region.range.end.line)
                for region in python.regions()] == [
            (RegionKind.CLASS, "Greeter", 4, 7), (RegionKind.FUNCTION, "greet", 5, 7)]

    def test_outer_regions_come_first(self, engine):
        session = engine.open_session("python")
        session.update("def outer():\n    for item in []:\n        data = {\n            1: 2,\n        }\n")
        assert [region.kind for region in session.regions()] == [
            RegionKind.FUNCTION, RegionKind.BLOCK, RegionKind.COLLECTION, RegionKind.COLLECTION]

    def test_a_region_knows_whether_it_spans_lines(self, engine):
        session = engine.open_session("python")
        session.update("def one(): pass\n\n\ndef two():\n    pass\n")
        assert [(region.name, region.is_multiline) for region in session.regions()] == [
            ("one", False), ("two", True)]

    def test_javascript_regions(self, engine):
        session = engine.open_session("javascript")
        session.update("class A {\n  run() {\n    return [1].map((x) => x);\n  }\n}\n")
        assert [(region.kind.value, region.name) for region in session.regions()] == [
            ("class", "A"), ("function", "run"), ("collection", ""), ("function", "")]

    def test_json_regions(self, engine):
        session = engine.open_session("json")
        session.update('{\n  "a": [\n    1\n  ]\n}\n')
        assert [(region.kind, region.range.start.line, region.range.end.line)
                for region in session.regions()] == [
            (RegionKind.COLLECTION, 1, 5), (RegionKind.COLLECTION, 2, 4)]

    def test_regions_follow_an_edit(self, python):
        python.update(PYTHON + "\n\ndef added():\n    pass\n")
        assert [region.name for region in python.regions()] == ["Greeter", "greet", "added"]


class TestQueryFiles:
    @pytest.mark.parametrize("language_id", LANGUAGES)
    def test_every_language_has_a_region_query(self, language_id):
        assert own_query(QUERY_DIRECTORY, language_id, REGIONS_QUERY_FILE).strip()

    @pytest.mark.parametrize("spec", BUILTIN_GRAMMARS, ids=LANGUAGES)
    def test_the_queries_compile_and_name_known_things(self, spec):
        grammar = load_grammar(spec, QUERY_DIRECTORY)
        assert grammar.categories and grammar.regions is not None
        region_names = {grammar.regions.capture_name(index)
                        for index in range(grammar.regions.capture_count)}
        assert region_names <= {f"region.{kind.value}" for kind in RegionKind}

    def test_a_language_without_a_query_file_has_no_text(self, tmp_path):
        assert own_query(tmp_path, "python", HIGHLIGHTS_QUERY_FILE) == ""

    def test_no_suffix_belongs_to_two_languages(self):
        suffixes = [suffix for spec in BUILTIN_GRAMMARS for suffix in spec.suffixes]
        assert len(suffixes) == len(set(suffixes))
        assert all(suffix == suffix.lower() and suffix.startswith(".") for suffix in suffixes)


class TestWhenAGrammarCannotBeUsed:
    """A missing package or a broken query makes a language unsupported; it never raises."""

    @staticmethod
    def _missing():
        raise ImportError("No module named 'tree_sitter_cobol'")

    def test_a_grammar_that_is_not_installed(self, caplog):
        engine = TreeSitterEngine([GrammarSpec("cobol", (".cob",), self._missing)])
        assert (engine.language_ids(), engine.language_for("a.cob"),
                engine.open_session("cobol")) == ((), None, None)
        assert "cobol" in caplog.text

    def test_the_load_is_tried_once(self):
        attempts: list[int] = []

        def load():
            attempts.append(1)
            raise ImportError("not installed")

        engine = TreeSitterEngine([GrammarSpec("cobol", (".cob",), load)])
        for _ in range(3):
            engine.language_for("a.cob")
        assert len(attempts) == 1

    def test_a_broken_query_file(self, tmp_path):
        (tmp_path / "python").mkdir()
        (tmp_path / "python" / REGIONS_QUERY_FILE).write_text("(no_such_node) @region.block",
                                                              encoding="utf-8")
        engine = TreeSitterEngine(BUILTIN_GRAMMARS, tmp_path)
        assert "python" not in engine.language_ids()
        assert "json" in engine.language_ids()

    def test_an_unknown_region_name_is_left_out(self, tmp_path):
        (tmp_path / "json").mkdir()
        (tmp_path / "json" / REGIONS_QUERY_FILE).write_text(
            "(object) @region.collection\n(array) @region.mystery\n(pair) @other",
            encoding="utf-8")
        session = TreeSitterEngine(BUILTIN_GRAMMARS, tmp_path).open_session("json")
        session.update('{"a": [1]}')
        assert [region.kind for region in session.regions()] == [RegionKind.COLLECTION]

    def test_a_grammar_that_ships_no_highlight_query(self):
        import tree_sitter_json
        bare = SimpleNamespace(language=tree_sitter_json.language)
        engine = TreeSitterEngine([GrammarSpec("json", (".json",), lambda: bare)])
        session = engine.open_session("json")
        session.update('{"a": 1}')
        assert [span.category for span in session.spans(1)] == [SyntaxCategory.KEY]

    def test_a_text_too_large_is_left_uncoloured(self, engine, monkeypatch):
        monkeypatch.setattr("je_editor.adapters.syntax.tree_sitter_engine.MAX_SOURCE_BYTES", 40)
        session = engine.open_session("python")
        session.update("x = 1\n")
        assert session.spans(1) != ()
        assert session.update("x = 1\n" * 20) == LineSpan(1, 21)
        assert (session.spans(1), session.regions(), session.has_errors) == ((), (), False)
        # Still too large: nothing had colours, so only the first line is reported.
        assert session.update("y = 2\n" * 20) == LineSpan(1, 1)
        assert session.update("x = 1\n") == LineSpan(1, 2)
        assert session.spans(1) != ()

    def test_the_limit_is_generous(self):
        assert MAX_SOURCE_BYTES >= 1_000_000


class TestTheBindingIsUsedSafely:
    def test_reading_rows_does_not_take_references_away(self, engine):
        """
        ``Point.row`` and ``Point.column`` of tree-sitter 0.26.0 drop a reference
        to the integer on every read, which crashes the interpreter after enough
        of them. The engine reads points by index; this notices if that changes.
        """
        session = engine.open_session("python")
        text = "\n".join(f"def function_{index}(value):\n    return value + {index}"
                         for index in range(400))
        watched = (0, 1, 4)
        # Earlier tests leave cycles holding small integers. Their collection during
        # this loop must not look like the binding dropped references on Python 3.10.
        gc.collect()
        before = [sys.getrefcount(value) for value in watched]
        for round_number in range(3):
            session.update(text + f"\n# round {round_number}\n")
            for line in range(1, session.line_count + 1):
                session.spans(line)
            session.regions()
        drift = [sys.getrefcount(value) - count for value, count in zip(watched, before)]
        # Thousands of reads happened; a leak of one reference each would show as thousands.
        assert min(drift) > -200


class TestTheSyntaxLanguageService:
    @pytest.fixture()
    def services(self, tmp_path):
        built = build_default_services(settings_directory=tmp_path)
        yield built
        built.shutdown()

    @pytest.fixture()
    def document(self, services, tmp_path):
        opened = TextDocument(to_uri(tmp_path / "main.py"), PYTHON)
        services.documents.open(opened)
        return opened

    @staticmethod
    def _ask(services, capability, document) -> LanguageReply:
        replies: list[LanguageReply] = []
        services.languages.request(LanguageRequest(capability, document), replies.append)
        return replies[0]

    def test_the_default_services_have_the_engine_and_the_service(self, services):
        assert services.syntax is shared_syntax_engine()
        assert [service.name for service in services.languages.services()] == [SERVICE_NAME]

    def test_an_open_document_has_a_syntax_tree(self, services, document):
        reply = self._ask(services, LanguageCapability.SYNTAX_TREE, document)
        assert (reply.ok, reply.service) == (True, SERVICE_NAME)
        assert isinstance(reply.value, SyntaxSession)
        assert reply.value.spans(4)[0] == SyntaxSpan(1, 5, SyntaxCategory.KEYWORD)

    def test_the_symbols_are_the_named_regions(self, services, document):
        reply = self._ask(services, LanguageCapability.DOCUMENT_SYMBOLS, document)
        assert [(region.kind, region.name) for region in reply.value] == [
            (RegionKind.CLASS, "Greeter"), (RegionKind.FUNCTION, "greet")]

    def test_the_tree_follows_the_document(self, services, document):
        services.documents.replace_text(document.uri, "def renamed():\n    pass\n")
        reply = self._ask(services, LanguageCapability.DOCUMENT_SYMBOLS, document)
        assert [region.name for region in reply.value] == ["renamed"]

    def test_a_closed_document_has_no_tree(self, services, document):
        services.documents.close(document.uri)
        service = services.languages.services()[0]
        assert service.session_for(document) is None

    def test_the_language_id_counts_before_the_file_name(self, services, tmp_path):
        opened = TextDocument(to_uri(tmp_path / "settings.conf"), '{"a": 1}', "json")
        services.documents.open(opened)
        assert self._ask(services, LanguageCapability.SYNTAX_TREE, opened).value.language_id == "json"

    def test_a_language_the_engine_does_not_know_is_not_handled(self, services, tmp_path):
        opened = TextDocument(to_uri(tmp_path / "main.rs"), "fn main() {}", "rust")
        services.documents.open(opened)
        reply = self._ask(services, LanguageCapability.SYNTAX_TREE, opened)
        assert (reply.ok, reply.service) == (False, "")

    def test_a_capability_it_does_not_offer_is_an_error_reply(self, document):
        service = SyntaxLanguageService(shared_syntax_engine())
        service.document_opened(document)
        replies: list[LanguageReply] = []
        service.request(LanguageRequest(LanguageCapability.HOVER, document), replies.append)
        assert (replies[0].ok, "hover" in replies[0].error) == (False, True)

    def test_a_document_it_was_never_told_about_is_an_error_reply(self, tmp_path):
        service = SyntaxLanguageService(shared_syntax_engine())
        unknown = TextDocument(to_uri(tmp_path / "other.py"), "x = 1\n")
        replies: list[LanguageReply] = []
        service.request(LanguageRequest(LanguageCapability.SYNTAX_TREE, unknown), replies.append)
        assert replies[0].ok is False

    def test_a_change_to_a_document_it_missed_opens_it(self, tmp_path):
        service = SyntaxLanguageService(shared_syntax_engine())
        late = TextDocument(to_uri(tmp_path / "late.py"), "x = 1\n")
        service.document_changed(late)
        assert service.session_for(late) is not None

    def test_shutting_down_lets_go_of_every_tree(self, services, document):
        service = services.languages.services()[0]
        services.shutdown()
        assert service.session_for(document) is None

    def test_with_no_parser_nothing_is_handled(self, document):
        service = SyntaxLanguageService(NoSyntaxEngine())
        service.document_opened(document)
        assert (service.handles(document), service.session_for(document)) == (False, None)
