from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtGui import QTextCharFormat

from je_editor.pyside_ui.code.syntax.syntax_setting import syntax_word_setting_dict, syntax_rule_setting_dict


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlight_rules = []

        # Highlight
        for rule_variable_dict in syntax_word_setting_dict.values():
            color = rule_variable_dict.get("color")
            text_char_format = QTextCharFormat()
            text_char_format.setForeground(color)
            for word in rule_variable_dict.get("words"):
                pattern = QRegularExpression(rf"{word}")
                self.highlight_rules.append((pattern, text_char_format))

        for rule_variable_dict in syntax_rule_setting_dict.values():
            color = rule_variable_dict.get("color")
            text_char_format = QTextCharFormat()
            text_char_format.setForeground(color)
            for rule in rule_variable_dict.get("rules"):
                pattern = QRegularExpression(rule)
                self.highlight_rules.append((pattern, text_char_format))

    def highlightBlock(self, text) -> None:
        for pattern, pattern_format in self.highlight_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), pattern_format)

