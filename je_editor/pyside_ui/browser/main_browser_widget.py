from PySide6.QtWidgets import QWidget, QGridLayout, QTabWidget, QTabBar

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger


class MainBrowserWidget(QWidget):
    """
    瀏覽器元件：包含分頁，並在最右方固定一個「+」分頁。
    """

    def __init__(self, start_url: str = "https://www.google.com/",
                 search_prefix: str = "https://www.google.com.tw/search?q="):
        super().__init__()
        jeditor_logger.info("Init BrowserWidget "
                            f"start_url: {start_url} "
                            f"search_prefix: {search_prefix}")

        grid_layout = QGridLayout()

        self.browser_tab = QTabWidget()
        self.browser_tab.setTabsClosable(True)
        self.browser_tab.tabCloseRequested.connect(self.close_tab)

        self.search_prefix = search_prefix

        # 預設第一個分頁
        self.add_browser_tab(BrowserWidget(start_url=start_url,
                                           search_prefix=search_prefix),
                             "Google")

        # 固定一個「+」分頁
        self.add_plus_tab()

        grid_layout.addWidget(self.browser_tab)
        self.setLayout(grid_layout)

    def add_browser_tab(self, browser_widget: BrowserWidget, title: str = "New Tab"):
        # 在「+」分頁前插入新分頁
        plus_index = self.browser_tab.count() - 1
        index = self.browser_tab.insertTab(plus_index, browser_widget, title)
        self.browser_tab.setCurrentIndex(index)

        # 更新分頁標題
        browser_widget.browser.titleChanged.connect(
            lambda t, i=index: self.browser_tab.setTabText(i, t)
        )

    def add_plus_tab(self):
        """新增一個固定的「+」分頁"""
        add_new_page_widget = QWidget()
        self.browser_tab.addTab(add_new_page_widget, "+")
        # 禁止關閉「+」分頁
        self.browser_tab.tabBar().setTabButton(self.browser_tab.count() - 1,
                                               QTabBar.ButtonPosition.RightSide, None)
        self.browser_tab.tabBar().tabBarClicked.connect(self.handle_tab_changed)

    def handle_tab_changed(self, index: int):
        """如果點到「+」分頁，就開新分頁"""
        if self.browser_tab.tabText(index) == "+": # 最後一個是「+」
                # 建立新分頁（會自動切換到新分頁）
                self.add_browser_tab(
                    BrowserWidget(start_url="https://www.google.com/",
                                  search_prefix=self.search_prefix),
                    "Google"
                )

    def close_tab(self, index: int):
        """關閉指定分頁，但保留「+」"""
        widget = self.browser_tab.widget(index)
        self.browser_tab.removeTab(index)
        widget.deleteLater()
