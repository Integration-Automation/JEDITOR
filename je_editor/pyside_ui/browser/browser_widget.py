from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QInputDialog

from je_editor.pyside_ui.browser.browser_serach_lineedit import BrowserLineSearch
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

from je_editor.pyside_ui.browser.browser_view import BrowserView


class BrowserWidget(QWidget):
    def __init__(self, start_url: str = "https://www.google.com/",
                 search_prefix: str = "https://www.google.com.tw/search?q=",
                 main_widget: MainBrowserWidget = None, browser_view: BrowserView = None):
        # --- Browser setting / 瀏覽器設定 ---
        super().__init__()
        self.main_widget = main_widget
        if browser_view:
            self.browser = browser_view
        else:
            self.browser = BrowserView(start_url, main_widget=main_widget)  # 內嵌的瀏覽器視圖
        self.search_prefix = search_prefix  # 搜尋引擎前綴字串
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # --- Top bar buttons / 上方工具列按鈕 ---
        self.back_button = QPushButton(language_wrapper.language_word_dict.get("browser_back_button"))
        self.back_button.clicked.connect(self.browser.back)  # 返回上一頁

        self.forward_button = QPushButton(language_wrapper.language_word_dict.get("browser_forward_button"))
        self.forward_button.clicked.connect(self.browser.forward)  # 前往下一頁

        self.reload_button = QPushButton(language_wrapper.language_word_dict.get("browser_reload_button"))
        self.reload_button.clicked.connect(self.browser.reload)  # 重新整理

        self.search_button = QPushButton(language_wrapper.language_word_dict.get("browser_search_button"))
        self.search_button.clicked.connect(self.search)  # 搜尋按鈕

        # URL / Search input line (custom QLineEdit)
        self.url_input = BrowserLineSearch(self)

        # --- Action: Ctrl+F to find text / 快捷鍵 Ctrl+F 搜尋文字 ---
        self.find_action = QAction()
        self.find_action.setShortcut("Ctrl+f")
        self.find_action.triggered.connect(self.find_text)
        self.addAction(self.find_action)

        # --- Layout / 版面配置 ---
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.back_button, 0, 0)
        self.grid_layout.addWidget(self.forward_button, 0, 1)
        self.grid_layout.addWidget(self.reload_button, 0, 2)
        self.grid_layout.addWidget(self.url_input, 0, 3)
        self.grid_layout.addWidget(self.search_button, 0, 4)
        self.grid_layout.addWidget(self.browser, 1, 0, -1, -1)  # 瀏覽器視圖佔滿下方
        self.setLayout(self.grid_layout)

    def search(self):
        """
        Perform a search using the text in the input line.
        使用輸入框的文字進行搜尋，將字串附加到 search_prefix 後送出。
        """
        jeditor_logger.info("BrowserWidget Search")
        self.browser.setUrl(f"{self.search_prefix}{self.url_input.text()}")

    def find_text(self):
        """
        Open a dialog to find text in the current page.
        開啟輸入對話框，在當前頁面中搜尋文字。
        - 如果按下 OK，搜尋輸入的文字
        - 如果取消，清除搜尋
        """
        jeditor_logger.info("BrowserWidget Find Text")
        search_box = QInputDialog(self)
        search_text, press_ok = search_box.getText(
            self,
            language_wrapper.language_word_dict.get("browser_find_text"),
            language_wrapper.language_word_dict.get("browser_find_text_input")
        )
        if press_ok:
            self.browser.findText(search_text)
        else:
            self.browser.findText("")