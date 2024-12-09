from PySide6.QtGui import QTextDocument, QAction
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.dialog.search_ui.search_error_box import SearchResultBox
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger


class CodeRecord(QTextEdit):
    # Extend QTextEdit
    def __init__(self):
        jeditor_logger.info("Init CodeRecord")
        super().__init__()
        self.setLineWrapMode(self.LineWrapMode.NoWrap)
        self.setReadOnly(True)
        # Search Result
        self.search_result_action = QAction("Search Error")
        self.search_result_action.setShortcut("Ctrl+e")
        self.search_result_action.triggered.connect(
            self.start_search_result_dialog
        )
        self.addAction(self.search_result_action)

    def append(self, text: str) -> None:
        jeditor_logger.info("CodeRecord append")
        max_line: int = user_setting_dict.get("max_line_of_output", 200000)
        if self.document().lineCount() >= max_line > 0:
            self.setPlainText("")
        super().append(text)

    def start_search_result_dialog(self) -> None:
        jeditor_logger.info("CodeRecord start_search_result_dialog")
        # Binding search box
        self.search_result_box = SearchResultBox()
        self.search_result_box.search_back_button.clicked.connect(
            self.find_back_text
        )
        self.search_result_box.search_next_button.clicked.connect(
            self.find_next_text
        )
        self.search_result_box.show()

    def find_next_text(self) -> None:
        jeditor_logger.info("CodeRecord find_next_text")
        if self.search_result_box.isVisible():
            text = self.search_result_box.search_input.text()
            self.find(text)

    def find_back_text(self) -> None:
        jeditor_logger.info("CodeRecord find_back_text")
        if self.search_result_box.isVisible():
            text = self.search_result_box.search_input.text()
            self.find(text, QTextDocument.FindFlag.FindBackward)
