from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor

from PySide6.QtGui import QSyntaxHighlighter, QTextDocument

from je_editor.pyside_ui.code.syntax.highlight_rules import (
    HighlightRule, apply_rules, make_format, plugin_rules, regex_rules, word_rules
)
# 匯入語法設定，包括關鍵字與規則
# Import syntax settings: keywords and rules
from je_editor.pyside_ui.code.syntax.syntax_setting import (
    syntax_word_setting_dict,
    syntax_rule_setting_dict,
)
from je_editor.utils.logging.loggin_instance import jeditor_logger


class PythonHighlighter(QSyntaxHighlighter):
    """
    Python 語法高亮類別，繼承自 QSyntaxHighlighter
    Python syntax highlighter class, inherits from QSyntaxHighlighter

    以正規表示式一行一行比對。語法引擎認得的檔案改由
    ``TreeSitterHighlighter`` 上色；這個類別留給語法引擎不能用、或使用者選了
    ``classic`` 的時候，以及沒有任何規則可用的副檔名。
    It matches regular expressions line by line. Files the syntax engine knows
    are coloured by ``TreeSitterHighlighter`` instead; this class remains for
    when the engine is unavailable or the user chose ``classic``, and for
    suffixes nothing else has rules for.
    """

    # 留著原本的名稱：PyBreeze 的契約測試從這裡確認「顏色可以是主題顏色的鍵」
    # Kept under its old name: PyBreeze's contract test checks here that a colour
    # may be a theme colour key
    _make_format = staticmethod(make_format)

    def __init__(self, parent: QTextDocument | None = None, main_window: CodeEditor = None,
                 suffix: str | None = None) -> None:
        """
        :param parent: 要上色的文件 / the document to highlight
        :param main_window: 文件所在的編輯器，用它目前的檔名判斷副檔名
            the editor holding the document, whose current file gives the suffix
        :param suffix: 直接指定副檔名（含點）；給了就不看 ``main_window``
            the suffix, dot included, given directly; ``main_window`` is then ignored
        """
        jeditor_logger.info(f"Init PythonHighlighter parent: {parent}")
        super().__init__(parent)

        if suffix is not None:
            current_file_suffix = suffix
        elif main_window is not None and main_window.current_file is not None:
            current_file_suffix = Path(main_window.current_file).suffix
        else:
            current_file_suffix = ".py"

        # 儲存所有高亮規則 / store all highlight rules
        self.highlight_rules: list[HighlightRule] = regex_rules(syntax_rule_setting_dict)
        if current_file_suffix == ".py":
            self.highlight_rules += word_rules(syntax_word_setting_dict)
        else:
            self.highlight_rules += plugin_rules(current_file_suffix)

    def highlightBlock(self, text: str) -> None:
        """
        對每一行文字進行語法高亮
        Apply syntax highlighting to each block of text
        """
        apply_rules(self, text, self.highlight_rules)
