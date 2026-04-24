from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtGui import QTextCharFormat, QTextDocument

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

    @staticmethod
    def _make_format(color: object) -> QTextCharFormat:
        """建立含前景色的 QTextCharFormat / Build a QTextCharFormat with the given foreground."""
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        return fmt

    def _add_regex_rules(self, rule_setting: dict) -> None:
        """加入一組「正則規則」設定 / Append a group of regex highlight rules."""
        for rule_variable_dict in rule_setting.values():
            fmt = self._make_format(rule_variable_dict.get("color"))
            for rule in rule_variable_dict.get("rules", ()):  # 正則規則 / regex rules
                self.highlight_rules.append((QRegularExpression(rule), fmt))

    def _add_word_rules(self, word_setting: dict) -> None:
        """加入一組「關鍵字」規則 (使用 \\b 包住) / Append whole-word keyword rules."""
        for rule_variable_dict in word_setting.values():
            fmt = self._make_format(rule_variable_dict.get("color"))
            for word in rule_variable_dict.get("words", ()):  # 關鍵字清單 / keyword list
                self.highlight_rules.append((QRegularExpression(rf"\b{word}\b"), fmt))

    def _add_plugin_rules(self, current_file_suffix: str) -> None:
        """依副檔名載入插件或相容設定的語法規則 / Load plugin/legacy syntax rules for the suffix."""
        from je_editor.plugins import get_programming_language_plugin
        plugin = get_programming_language_plugin(current_file_suffix)
        if plugin:
            self._add_regex_rules(plugin.get("syntax_rules", {}))
            self._add_word_rules(plugin.get("syntax_words", {}))
            return
        legacy = syntax_extend_setting_dict.get(current_file_suffix)
        if legacy:
            # 向後相容：使用舊的 syntax_extend_setting_dict
            # Backward compatible: use old syntax_extend_setting_dict
            self._add_word_rules(legacy)

    def __init__(self, parent: QTextDocument | None = None, main_window: CodeEditor = None) -> None:
        jeditor_logger.info(f"Init PythonHighlighter parent: {parent}")
        super().__init__(parent)

        self.highlight_rules = []  # 儲存所有高亮規則 / store all highlight rules

        if main_window is not None and main_window.current_file is not None:
            current_file_suffix = Path(main_window.current_file).suffix
        else:
            current_file_suffix = ".py"

        self._add_regex_rules(syntax_rule_setting_dict)
        if current_file_suffix == ".py":
            self._add_word_rules(syntax_word_setting_dict)
        else:
            self._add_plugin_rules(current_file_suffix)

    def highlightBlock(self, text: str) -> None:
        """
        對每一行文字進行語法高亮
        Apply syntax highlighting to each block of text
        """
        for pattern, pattern_format in self.highlight_rules:
            match_iterator = pattern.globalMatch(text)  # 全域比對 / global regex match
            while match_iterator.hasNext():
                match = match_iterator.next()
                # 設定比對到的文字格式 / apply format to matched text
                self.setFormat(match.capturedStart(), match.capturedLength(), pattern_format)
