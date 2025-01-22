from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtGui import QTextCharFormat

from je_editor.pyside_ui.code.syntax.syntax_setting import syntax_word_setting_dict, syntax_rule_setting_dict, \
    syntax_extend_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, main_window: CodeEditor = None):
        jeditor_logger.info(f"Init PythonHighlighter parent: {parent}")
        super().__init__(parent)

        self.highlight_rules = []
        if main_window.current_file is not None:
            current_file_suffix = Path(main_window.current_file).suffix
        else:
            current_file_suffix = ".py"
        if current_file_suffix == ".py":
            # Highlight
            for rule_variable_dict in syntax_word_setting_dict.values():
                color = rule_variable_dict.get("color")
                text_char_format = QTextCharFormat()
                text_char_format.setForeground(color)
                for word in rule_variable_dict.get("words"):
                    pattern = QRegularExpression(rf"\b{word}\b")
                    self.highlight_rules.append((pattern, text_char_format))
            for rule_variable_dict in syntax_rule_setting_dict.values():
                color = rule_variable_dict.get("color")
                text_char_format = QTextCharFormat()
                text_char_format.setForeground(color)
                for rule in rule_variable_dict.get("rules"):
                    pattern = QRegularExpression(rule)
                    self.highlight_rules.append((pattern, text_char_format))
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
                pass

    def highlightBlock(self, text) -> None:
        jeditor_logger.info(f"PythonHighlighter highlightBlock text: {text}")
        for pattern, pattern_format in self.highlight_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), pattern_format)
