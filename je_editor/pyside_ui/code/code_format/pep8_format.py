import tokenize
from typing import Any

import pycodestyle

from je_editor.utils.logging.loggin_instance import jeditor_logger


class PEP8FormatChecker(pycodestyle.Checker):
    def __init__(self, filename: str, **kwargs: Any) -> None:
        """
        自訂的 PEP8 格式檢查器，繼承自 pycodestyle.Checker。
        Custom PEP8 format checker, inherits from pycodestyle.Checker.
        """
        jeditor_logger.info(f"Init PEP8FormatChecker "
                            f"filename: {filename} "
                            f"kwargs: {kwargs}")
        super().__init__(filename, **kwargs)

        # 初始化變數 / Initialize variables
        self.physical_line = None
        self.blank_before = None
        self.blank_lines = None
        self.tokens = None
        self.previous_unindented_logical_line = None
        self.previous_logical = None
        self.indent_level = None
        self.previous_indent_level = None
        self.line_number = None
        self.indent_char = None
        self.total_lines = None

        # 定義換行符號集合 / Define newline token set
        self.new_line = frozenset([tokenize.NL, tokenize.NEWLINE])

        # 將 report_error 替換為自訂方法 / Override report_error with custom method
        self.report_error = self.replace_report_error

        # 當前檔案名稱 / Current file name
        self.current_file: str = filename

        # 儲存錯誤訊息的清單 / List to store error messages
        self.error_list: list = []

    def replace_report_error(self, line_number: int, offset: int, text: str, check: Any) -> None:
        """
        自訂錯誤回報方法，過濾掉特定錯誤 (例如 W191)。
        Custom error reporting method, filters out specific errors (e.g., W191).
        """
        jeditor_logger.info(f"PEP8FormatChecker replace_report_error "
                            f"line_number: {line_number} "
                            f"offset: {offset} "
                            f"text: {text}")
        # 忽略 W191 (縮排使用 Tab 的警告)
        # Ignore W191 (indentation contains tabs)
        if not text.startswith("W191"):
            self.error_list.append(f"{text} on line: {line_number}, offset: {offset}")

    def _reset_token_state(self) -> None:
        """重設 token 掃描狀態 / Reset per-run token scan state."""
        self.line_number = 0
        self.indent_char = None
        self.indent_level = self.previous_indent_level = 0
        self.previous_logical = ''
        self.previous_unindented_logical_line = ''
        self.tokens = []
        self.blank_lines = self.blank_before = 0

    @staticmethod
    def _paren_delta(text: str) -> int:
        """括號文字的層級增減量 / Return +1 for openers, -1 for closers, else 0."""
        if text in '([{':
            return 1
        if text in '}])':
            return -1
        return 0

    def _log_verbose_token(self, token: Any, text: str) -> None:
        """輸出 verbose token 資訊 / Emit verbose token info when requested."""
        if token[2][0] == token[3][0]:
            pos = '[{}:{}]'.format(token[2][1] or '', token[3][1])
        else:
            pos = 'l.%s' % token[3][0]
        self.replace_report_error(token[2][0], pos, tokenize.tok_name[token[0]], text)

    def _handle_newline_token(self, token_type: int) -> None:
        """處理換行類 token (邏輯行結束/空行) / Dispatch newline tokens."""
        if token_type == tokenize.NEWLINE:
            self.check_logical()
            self.blank_before = 0
        elif len(self.tokens) == 1:
            # 只有換行符號，代表空行 / Only a newline → blank line
            self.blank_lines += 1
            del self.tokens[0]
        else:
            self.check_logical()

    def check_all_format(self, expected: Any = None, line_offset: int = 0) -> int:
        """執行所有格式檢查 / Run all checks on the input file."""
        jeditor_logger.info(f"PEP8FormatChecker check_all_format "
                            f"expected: {expected} "
                            f"line_offset: {line_offset}")

        self.report.init_file(self.filename, self.lines, expected, line_offset)
        self.total_lines = len(self.lines)
        if self._ast_checks:
            self.check_ast()

        self._reset_token_state()
        parens = 0  # 括號層級計數器 / Parentheses nesting counter
        for token in self.generate_tokens():
            self.tokens.append(token)
            token_type, text = token[0:2]
            if self.verbose >= 3:
                self._log_verbose_token(token, text)
            if token_type == tokenize.OP:
                parens += self._paren_delta(text)
            elif not parens and token_type in self.new_line:
                self._handle_newline_token(token_type)

        if self.tokens:
            self.check_physical(self.lines[-1])
            self.check_logical()
        return self.report.get_file_results()
