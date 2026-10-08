"""
為一份文件挑選並建立高亮器
Choose and build the highlighter for a document.

語法引擎會的語言用它來上色；其餘的照原本的規則：有關鍵字表的語言用通用高亮器，
都不符合的用 Python 的。插件為副檔名登記的關鍵字疊在任何一種之上。
A language the syntax engine knows is coloured by it. Everything else follows the
older rules: a language with a keyword table gets the generic highlighter, and
whatever is left gets Python's. Keywords a plugin registered for the suffix are
laid over whichever one is used.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QSyntaxHighlighter, QTextDocument

from je_editor.adapters.syntax.tree_sitter_engine import shared_syntax_engine
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.syntax.syntax_model import SyntaxEngine, SyntaxSession
from je_editor.pyside_ui.code.syntax.generic_syntax import highlighter_for
from je_editor.pyside_ui.code.syntax.highlight_rules import plugin_rules, release_document
from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
from je_editor.pyside_ui.code.syntax.tree_sitter_highlighter import TreeSitterHighlighter
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

# 使用者設定裡選擇語法引擎的鍵與它的兩個值
# The user setting that selects the syntax engine, and its two values
SYNTAX_ENGINE_SETTING = "syntax_engine"
TREE_SITTER_ENGINE = "tree_sitter"
CLASSIC_ENGINE = "classic"
# 還沒有檔名的新分頁當成這個語言 / A new tab that has no file name yet counts as this language
UNNAMED_LANGUAGE = "python"
UNNAMED_SUFFIX = ".py"


def syntax_engine_for(main_window: object) -> SyntaxEngine:
    """
    取得視窗的語法引擎
    The syntax engine of a window.

    :param main_window: 主視窗 / the main window
    :return: 視窗核心服務裡的引擎；視窗沒有核心服務（宿主程式自己的視窗、測試替身）
        時用整個程序共用的那一個
        the engine in the window's core services, or the one the whole process
        shares when the window has none, as a host's own window or a test double
    """
    services = getattr(main_window, "services", None)
    return services.syntax if isinstance(services, EditorServices) else shared_syntax_engine()


def _session_for(engine: SyntaxEngine, file_path: str | None) -> SyntaxSession | None:
    """照設定與檔名開一個語法 session，不該用語法引擎時為 ``None`` / A session by setting and file name, or ``None``."""
    if user_setting_dict.get(SYNTAX_ENGINE_SETTING, TREE_SITTER_ENGINE) != TREE_SITTER_ENGINE:
        return None
    language_id = engine.language_for(file_path) if file_path else UNNAMED_LANGUAGE
    return None if language_id is None else engine.open_session(language_id)


def build_highlighter(document: QTextDocument, file_path: str | None,
                      engine: SyntaxEngine) -> QSyntaxHighlighter:
    """
    為文件建立適合它的高亮器
    Build the highlighter that suits a document.

    :param document: 要上色的文件 / the document to highlight
    :param file_path: 文件的檔案路徑，還沒有檔名時為 ``None``
        the document's file path, or ``None`` when it has no name yet
    :param engine: 語法引擎 / the syntax engine
    :return: 已經接上文件的高亮器 / a highlighter already attached to the document
    """
    suffix = Path(file_path).suffix if file_path else ""
    extra_rules = plugin_rules(suffix) if suffix else []
    session = _session_for(engine, file_path)
    if session is not None:
        return TreeSitterHighlighter(document, session, extra_rules)
    generic = highlighter_for(document, suffix, extra_rules) if suffix else None
    if generic is not None:
        return generic
    # Python 的高亮器自己會加上插件的規則 / Python's highlighter adds the plugin rules itself
    return PythonHighlighter(document, suffix=suffix if file_path else UNNAMED_SUFFIX)


def dispose_highlighter(highlighter: QSyntaxHighlighter | None) -> None:
    """
    把不再使用的高亮器從文件上拿掉並刪除
    Take a highlighter that is no longer used off its document and delete it.

    高亮器是文件的子物件；只把 Python 這邊的參照換掉的話，舊的那一個還連在文件上，
    每次編輯都繼續上色。
    A highlighter is a child of its document: replacing only the Python reference
    leaves the old one connected, colouring on every edit.

    :param highlighter: 要丟掉的高亮器，``None`` 時什麼都不做
        the highlighter to drop; ``None`` does nothing
    """
    if highlighter is None:
        return
    if isinstance(highlighter, TreeSitterHighlighter):
        highlighter.detach()
    else:
        release_document(highlighter)
    highlighter.deleteLater()
