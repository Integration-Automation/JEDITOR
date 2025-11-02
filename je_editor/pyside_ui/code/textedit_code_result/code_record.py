from PySide6.QtGui import QTextDocument, QAction
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.dialog.search_ui.search_error_box import SearchResultBox
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger


class CodeRecord(QTextEdit):
    # 繼承自 QTextEdit，作為程式碼輸出紀錄區
    # Extend QTextEdit, used as a code output record area
    def __init__(self):
        jeditor_logger.info("Init CodeRecord")
        super().__init__()
        self.setLineWrapMode(self.LineWrapMode.NoWrap)  # 禁止自動換行 / disable line wrapping
        self.setReadOnly(True)  # 設為唯讀 / set as read-only

        # 建立搜尋錯誤的快捷動作
        # Create search error action with shortcut
        self.search_result_action = QAction("Search Error")
        self.search_result_action.setShortcut("Ctrl+e")
        self.search_result_action.triggered.connect(
            self.start_search_result_dialog  # 綁定觸發事件 / bind trigger event
        )
        self.addAction(self.search_result_action)

    def append(self, text: str) -> None:
        """
        新增文字到輸出區，若超過最大行數則清空
        Append text to output area, clear if exceeding max lines
        """
        jeditor_logger.info("CodeRecord append")
        max_line: int = user_setting_dict.get("max_line_of_output", 200000)
        if self.document().lineCount() >= max_line > 0:
            # 若行數超過設定，清空內容
            # Clear content if line count exceeds limit
            self.setPlainText("")
        super().append(text)

    def start_search_result_dialog(self) -> None:
        """
        開啟搜尋對話框，並綁定搜尋按鈕事件
        Open search dialog and bind search button events
        """
        jeditor_logger.info("CodeRecord start_search_result_dialog")
        self.search_result_box = SearchResultBox()  # 建立搜尋框 / create search box
        self.search_result_box.search_back_button.clicked.connect(
            self.find_back_text  # 綁定「上一個」搜尋 / bind "find previous"
        )
        self.search_result_box.search_next_button.clicked.connect(
            self.find_next_text  # 綁定「下一個」搜尋 / bind "find next"
        )
        self.search_result_box.show()  # 顯示搜尋框 / show search box

    def find_next_text(self) -> None:
        """
        搜尋下一個符合的文字
        Find next matching text
        """
        jeditor_logger.info("CodeRecord find_next_text")
        if self.search_result_box.isVisible():
            text = self.search_result_box.search_input.text()
            self.find(text)  # 使用 QTextEdit 內建 find 方法 / use QTextEdit built-in find

    def find_back_text(self) -> None:
        """
        搜尋上一個符合的文字
        Find previous matching text
        """
        jeditor_logger.info("CodeRecord find_back_text")
        if self.search_result_box.isVisible():
            text = self.search_result_box.search_input.text()
            # 使用 FindBackward 旗標往回搜尋
            # Use FindBackward flag to search backwards
            self.find(text, QTextDocument.FindFlag.FindBackward)
