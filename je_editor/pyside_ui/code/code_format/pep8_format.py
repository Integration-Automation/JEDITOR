import tokenize
import pycodestyle

from je_editor.utils.logging.loggin_instance import jeditor_logger


class PEP8FormatChecker(pycodestyle.Checker):
    def __init__(self, filename: str, **kwargs):
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
        self.error_list: list = list()

    def replace_report_error(self, line_number, offset, text, check):
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

    def check_all_format(self, expected=None, line_offset=0) -> int:
        """
        執行所有格式檢查。
        Run all checks on the input file.
        """
        jeditor_logger.info(f"PEP8FormatChecker check_all_format "
                            f"expected: {expected} "
                            f"line_offset: {line_offset}")

        # 初始化檔案檢查 / Initialize file check
        self.report.init_file(self.filename, self.lines, expected, line_offset)
        self.total_lines = len(self.lines)

        # 如果有 AST 檢查，先執行 / Run AST checks if available
        if self._ast_checks:
            self.check_ast()

        # 重設狀態變數 / Reset state variables
        self.line_number = 0
        self.indent_char = None
        self.indent_level = self.previous_indent_level = 0
        self.previous_logical = ''
        self.previous_unindented_logical_line = ''
        self.tokens = []
        self.blank_lines = self.blank_before = 0
        parens = 0  # 括號層級計數器 / Parentheses nesting counter

        # 逐一處理 Token / Process tokens one by one
        for token in self.generate_tokens():
            self.tokens.append(token)
            token_type, text = token[0:2]

            # 如果 verbose >= 3，輸出詳細 Token 資訊
            # If verbose >= 3, log detailed token info
            if self.verbose >= 3:
                if token[2][0] == token[3][0]:
                    pos = '[{}:{}]'.format(token[2][1] or '', token[3][1])
                else:
                    pos = 'l.%s' % token[3][0]
                self.replace_report_error(token[2][0], pos, tokenize.tok_name[token[0]], text)

            # 檢查括號層級 / Track parentheses nesting
            if token_type == tokenize.OP:
                if text in '([{':
                    parens += 1
                elif text in '}])':
                    parens -= 1
            # 當不在括號內時，檢查換行 / When not inside parentheses, check newlines
            elif not parens:
                if token_type in self.new_line:
                    if token_type == tokenize.NEWLINE:
                        # 完整邏輯行結束，檢查邏輯行
                        # End of logical line, check it
                        self.check_logical()
                        self.blank_before = 0
                    elif len(self.tokens) == 1:
                        # 只有換行符號，代表空行
                        # Line contains only newline, count as blank line
                        self.blank_lines += 1
                        del self.tokens[0]
                    else:
                        # 其他情況也檢查邏輯行
                        # Otherwise, check logical line
                        self.check_logical()

        # 如果還有剩餘 Token，檢查最後一行
        # If tokens remain, check the last line
        if self.tokens:
            self.check_physical(self.lines[-1])  # 檢查物理行 / Check physical line
            self.check_logical()                 # 檢查邏輯行 / Check logical line

        # 回傳檔案檢查結果 / Return file check results
        return self.report.get_file_results()