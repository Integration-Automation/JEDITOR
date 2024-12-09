import tokenize

import pycodestyle

from je_editor.utils.logging.loggin_instance import jeditor_logger


class PEP8FormatChecker(pycodestyle.Checker):

    def __init__(self, filename: str, **kwargs):
        jeditor_logger.info(f"Init PEP8FormatChecker "
                            f"filename: {filename} "
                            f"kwargs: {kwargs}")
        super().__init__(filename, **kwargs)
        # Init variable
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
        self.new_line = frozenset([tokenize.NL, tokenize.NEWLINE])
        self.report_error = self.replace_report_error
        self.current_file: str = filename
        self.error_list: list = list()

    def replace_report_error(self, line_number, offset, text, check):
        jeditor_logger.info(f"PEP8FormatChecker replace_report_error "
                            f"line_number: {line_number} "
                            f"offset: {offset} "
                            f"text: {text}")
        if not text.startswith("W191"):
            self.error_list.append(f"{text} on line: {line_number}, offset: {offset}")

    def check_all_format(self, expected=None, line_offset=0) -> int:
        """Run all checks on the input file."""
        jeditor_logger.info(f"PEP8FormatChecker check_all_format "
                            f"expected: {expected} "
                            f"line_offset: {line_offset}")
        self.report.init_file(self.filename, self.lines, expected, line_offset)
        self.total_lines = len(self.lines)
        if self._ast_checks:
            self.check_ast()
        self.line_number = 0
        self.indent_char = None
        self.indent_level = self.previous_indent_level = 0
        self.previous_logical = ''
        self.previous_unindented_logical_line = ''
        self.tokens = []
        self.blank_lines = self.blank_before = 0
        parens = 0
        for token in self.generate_tokens():
            self.tokens.append(token)
            token_type, text = token[0:2]
            if self.verbose >= 3:
                if token[2][0] == token[3][0]:
                    pos = '[{}:{}]'.format(token[2][1] or '', token[3][1])
                else:
                    pos = 'l.%s' % token[3][0]
                self.replace_report_error(token[2][0], pos, tokenize.tok_name[token[0]], text)
            if token_type == tokenize.OP:
                if text in '([{':
                    parens += 1
                elif text in '}])':
                    parens -= 1
            elif not parens:
                if token_type in self.new_line:
                    if token_type == tokenize.NEWLINE:
                        self.check_logical()
                        self.blank_before = 0
                    elif len(self.tokens) == 1:
                        # The physical line contains only this token.
                        self.blank_lines += 1
                        del self.tokens[0]
                    else:
                        self.check_logical()
        if self.tokens:
            self.check_physical(self.lines[-1])
            self.check_logical()
        return self.report.get_file_results()
