"""
Tests that pin what other projects import from JEditor.

The editor's internals are being moved behind a service layer. PyBreeze subclasses
the main window and imports a handful of names by their full module path, and
plugins import the registry functions, so those names have to survive every move.
"""
from __future__ import annotations

import importlib
import inspect

import pytest

import je_editor

# What ``je_editor`` exported when the service layer was introduced. Names may be
# added to the package; none of these may leave it.
EXPORTED_NAMES = frozenset({
    "start_editor", "EditorMain", "EDITOR_EXTEND_TAB", "EditorWidget", "FullEditorWidget",
    "MainBrowserWidget", "ExecManager", "ShellManager", "PythonHighlighter",
    "syntax_rule_setting_dict", "syntax_extend_setting_dict",
    "user_setting_dict", "user_setting_color_dict",
    "language_wrapper", "english_word_dict", "traditional_chinese_word_dict", "jeditor_logger",
    "JEditorException", "JEditorExecException", "JEditorRunOnShellException",
    "JEditorSaveFileException", "JEditorOpenFileException", "JEditorContentFileException",
    "JEditorCantFindLanguageException", "JEditorJsonException",
    "register_programming_language", "get_programming_language_plugin",
    "get_all_programming_language_suffixes",
    "register_natural_language", "get_natural_language_plugin", "get_all_natural_languages",
    "register_plugin_run_config", "get_all_plugin_run_configs", "get_plugin_run_config_by_suffix",
    "register_plugin_metadata", "get_all_plugin_metadata", "load_external_plugins",
})

# Names PyBreeze imports by module path rather than from ``je_editor`` itself
DOWNSTREAM_INTERNALS = [
    ("je_editor.pyside_ui.main_ui.plugin_browser.plugin_browser_widget", "PluginBrowserWidget"),
    ("je_editor.pyside_ui.main_ui.dock.destroy_dock", "DestroyDock"),
    ("je_editor.pyside_ui.main_ui.editor.editor_widget_dock", "FullEditorWidget"),
    ("je_editor.pyside_ui.main_ui.save_settings.user_setting_file", "user_setting_dict"),
    ("je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file", "actually_color_dict"),
    ("je_editor.pyside_ui.dialog.file_dialog.save_file_dialog", "choose_file_get_save_file_path"),
    ("je_editor.pyside_ui.code.auto_save.auto_save_manager", "auto_save_manager_dict"),
    ("je_editor.pyside_ui.code.auto_save.auto_save_manager", "file_is_open_manager_dict"),
    ("je_editor.pyside_ui.code.auto_save.auto_save_manager", "init_new_auto_save_thread"),
    ("je_editor.utils.venv_check.check_venv", "check_and_choose_venv"),
    ("je_editor.utils.redirect_manager.redirect_manager_class", "RedirectStdErr"),
    ("je_editor.utils.encodings.text_codec", "DEFAULT_ENCODING"),
    ("je_editor.utils.encodings.text_codec", "LINE_ENDING_LF"),
    ("je_editor.utils.file.save.save_file", "write_file_with_encoding"),
    ("je_editor.utils.file.save.save_file", "write_file"),
]

# The constructor arguments a host application passes, in order
EDITOR_MAIN_ARGUMENTS = ["debug_mode", "show_system_tray_ray", "extend"]


class TestThePackageExports:
    def test_no_exported_name_has_left(self):
        assert EXPORTED_NAMES - set(je_editor.__all__) == set()

    def test_every_exported_name_exists(self):
        missing = [name for name in je_editor.__all__ if not hasattr(je_editor, name)]
        assert missing == []


class TestTheInternalsDownstreamImports:
    @pytest.mark.parametrize("module_name, attribute", DOWNSTREAM_INTERNALS)
    def test_the_name_is_still_at_its_module_path(self, module_name, attribute):
        # Every module name is a literal from the list above; nothing from
        # outside this file reaches the import.
        module = importlib.import_module(module_name)  # nosemgrep
        assert hasattr(module, attribute)


@pytest.fixture(scope="module")
def parameters():
    """The arguments of the main window's constructor, without ``self``."""
    signature = inspect.signature(je_editor.EditorMain.__init__)
    return [parameter for name, parameter in signature.parameters.items() if name != "self"]


class TestTheMainWindowConstructor:
    def test_the_arguments_keep_their_names_and_order(self, parameters):
        assert [parameter.name for parameter in parameters] == EDITOR_MAIN_ARGUMENTS

    def test_every_argument_is_off_by_default(self, parameters):
        assert [parameter.default for parameter in parameters] == [False, False, False]

    def test_the_arguments_can_be_passed_by_position_or_by_name(self, parameters):
        assert {parameter.kind for parameter in parameters} == {
            inspect.Parameter.POSITIONAL_OR_KEYWORD}


class TestTheShapesPyBreezePins:
    """
    PyBreeze keeps contract tests of its own (``test/test_utils/test_jeditor_contract.py``
    there) that pin parameter lists and even fragments of source. These are the
    ones a change here has broken before; the full set has to be run from PyBreeze.
    """

    def test_a_highlight_colour_may_be_a_theme_colour_key(self):
        from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
        assert "actually_color_dict.get(color)" in inspect.getsource(PythonHighlighter._make_format)

    def test_the_editor_methods_pybreeze_calls_after_renaming_a_file(self):
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        for method in ("reset_highlighter", "load_git_baseline", "start_language_server"):
            assert list(inspect.signature(getattr(CodeEditor, method)).parameters) == ["self"]
