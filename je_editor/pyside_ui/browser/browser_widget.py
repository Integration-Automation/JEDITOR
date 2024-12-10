from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton, QInputDialog

from je_editor.pyside_ui.browser.browser_serach_lineedit import BrowserLineSearch
from je_editor.pyside_ui.browser.browser_view import BrowserView
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class BrowserWidget(QWidget):

    def __init__(self, start_url: str = "https://www.google.com/",
                 search_prefix: str = "https://www.google.com.tw/search?q="):
        super().__init__()
        jeditor_logger.info("Init BrowserWidget "
                            f"start_url: {start_url} "
                            f"search_prefix: {search_prefix}")
        # Browser setting
        self.browser = BrowserView(start_url)
        self.search_prefix = search_prefix
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # Top bar
        self.back_button = QPushButton(language_wrapper.language_word_dict.get("browser_back_button"))
        self.back_button.clicked.connect(self.browser.back)
        self.forward_button = QPushButton(language_wrapper.language_word_dict.get("browser_forward_button"))
        self.forward_button.clicked.connect(self.browser.forward)
        self.reload_button = QPushButton(language_wrapper.language_word_dict.get("browser_reload_button"))
        self.reload_button.clicked.connect(self.browser.reload)
        self.search_button = QPushButton(language_wrapper.language_word_dict.get("browser_search_button"))
        self.search_button.clicked.connect(self.search)
        self.url_input = BrowserLineSearch(self)
        # Action
        self.find_action = QAction()
        self.find_action.setShortcut("Ctrl+f")
        self.find_action.triggered.connect(self.find_text)
        self.addAction(self.find_action)
        # Layout
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.back_button, 0, 0)
        self.grid_layout.addWidget(self.forward_button, 0, 1)
        self.grid_layout.addWidget(self.reload_button, 0, 2)
        self.grid_layout.addWidget(self.url_input, 0, 3)
        self.grid_layout.addWidget(self.search_button, 0, 4)
        self.grid_layout.addWidget(self.browser, 1, 0, -1, -1)
        self.setLayout(self.grid_layout)

    def search(self):
        jeditor_logger.info("BrowserWidget Search")
        self.browser.setUrl(f"{self.search_prefix}{self.url_input.text()}")

    def find_text(self):
        jeditor_logger.info("BrowserWidget Find Text")
        search_box = QInputDialog(self)
        search_text, press_ok = search_box.getText(
            self, language_wrapper.language_word_dict.get("browser_find_text"),
            language_wrapper.language_word_dict.get("browser_find_text_input"))
        if press_ok:
            self.browser.findText(search_text)
        else:
            self.browser.findText("")
