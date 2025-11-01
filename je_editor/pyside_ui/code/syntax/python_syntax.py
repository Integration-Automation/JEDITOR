from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtGui import QTextCharFormat

# 匯入語法設定，包括關鍵字、規則、擴展設定
# Import syntax settings: keywords, rules, and extended settings
from je_editor.pyside_ui.code.syntax.syntax_setting import (
    syntax_word_setting_dict,
    syntax_rule_setting_dict,
    syntax_extend_setting_dict
)
from je_editor.utils.logging.loggin_instance import jeditor_logger


class PythonHighlighter(QSyntaxHighlighter):
    """
    Python 語法高亮類別，繼承自 QSyntaxHighlighter
    Python syntax highlighter class, inherits from QSyntaxHighlighter
    """

    def __init__(self, parent=None, main_window: CodeEditor = None):
        jeditor_logger.info(f"Init PythonHighlighter parent: {parent}")
        super().__init__(parent)

        self.highlight_rules = []  # 儲存所有高亮規則 / store all highlight rules

        # 判斷目前檔案副檔名，若無則預設為 .py
        # Determine current file suffix, default to .py
        if main_window.current_file is not None:
            current_file_suffix = Path(main_window.current_file).suffix
        else:
            current_file_suffix = ".py"

        # -------------------------
        # 基本語法規則 (通用)
        # Basic highlight rules (common)
        # -------------------------
        for rule_variable_dict in syntax_rule_setting_dict.values():
            color = rule_variable_dict.get("color")  # 規則顏色 / rule color
            text_char_format = QTextCharFormat()
            text_char_format.setForeground(color)
            for rule in rule_variable_dict.get("rules"):  # 正則規則 / regex rules
                pattern = QRegularExpression(rule)
                self.highlight_rules.append((pattern, text_char_format))

        # -------------------------
        # Python 語法高亮
        # Python-specific highlight
        # -------------------------
        if current_file_suffix == ".py":
            for rule_variable_dict in syntax_word_setting_dict.values():
                color = rule_variable_dict.get("color")
                text_char_format = QTextCharFormat()
                text_char_format.setForeground(color)
                for word in rule_variable_dict.get("words"):  # 關鍵字清單 / keyword list
                    # 使用 \b 確保完整單字匹配 / use \b for whole word match
                    pattern = QRegularExpression(rf"\b{word}\b")
                    self.highlight_rules.append((pattern, text_char_format))

        # -------------------------
        # 其他語言的擴展高亮
        # Extended highlight for other languages
        # -------------------------
        else:
            if syntax_extend_setting_dict.get(current_file_suffix):
                for rule_variable_dict in syntax_extend_setting_dict.get(current_file_suffix).values():
                    color = rule_variable_dict.get("color")
                    text_char_format = QTextCharFormat()
                    text_char_format.setForeground(color)
                    for word in rule_variable_dict.get("words"):
                        pattern = QRegularExpression(rf"\b{word}\b")
                        self.highlight_rules.append((pattern, text_char_format))
            else:
                # 若無對應規則則略過
                # Skip if no rules found
                pass

    def highlightBlock(self, text) -> None:
        """
        對每一行文字進行語法高亮
        Apply syntax highlighting to each block of text
        """
        jeditor_logger.info(f"PythonHighlighter highlightBlock text: {text}")
        for pattern, pattern_format in self.highlight_rules:
            match_iterator = pattern.globalMatch(text)  # 全域比對 / global regex match
            while match_iterator.hasNext():
                match = match_iterator.next()
                # 設定比對到的文字格式 / apply format to matched text
                self.setFormat(match.capturedStart(), match.capturedLength(), pattern_format)