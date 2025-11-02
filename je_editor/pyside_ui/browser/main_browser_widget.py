from PySide6.QtWidgets import QWidget, QGridLayout, QTabWidget, QTabBar

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger


class MainBrowserWidget(QWidget):
    """
    瀏覽器元件：包含分頁，並在最右方固定一個「+」分頁。
    Browser component: includes tabs, with a fixed "+" tab at the far right.
    """

    def __init__(self, start_url: str = "https://www.google.com/",
                 search_prefix: str = "https://www.google.com.tw/search?q="):
        super().__init__()
        # 初始化時記錄訊息 (方便除錯)
        # Log initialization info (for debugging)
        jeditor_logger.info("Init BrowserWidget "
                            f"start_url: {start_url} "
                            f"search_prefix: {search_prefix}")

        grid_layout = QGridLayout()  # 建立網格佈局 / Create grid layout

        self.browser_tab = QTabWidget()  # 建立分頁容器 / Create tab widget
        self.browser_tab.setTabsClosable(True)  # 分頁可關閉 / Tabs can be closed
        self.browser_tab.tabCloseRequested.connect(self.close_tab)  # 綁定關閉事件 / Connect close event

        self.search_prefix = search_prefix  # 搜尋前綴字串 / Search prefix string

        # 預設第一個分頁 (Google)
        # Default first tab (Google)
        self.add_browser_tab(
            BrowserWidget(start_url=start_url, search_prefix=search_prefix), "Google"
        )

        # 固定一個「+」分頁
        # Add a fixed "+" tab
        self.add_plus_tab()

        grid_layout.addWidget(self.browser_tab)  # 把分頁加入佈局 / Add tab widget to layout
        self.setLayout(grid_layout)  # 設定主視窗佈局 / Set main layout

    def add_browser_tab(self, browser_widget: BrowserWidget, title: str = "New Tab"):
        # 在「+」分頁前插入新分頁
        # Insert new tab before the "+" tab
        plus_index = self.browser_tab.count() - 1
        index = self.browser_tab.insertTab(plus_index, browser_widget, title)
        self.browser_tab.setCurrentIndex(index)  # 自動切換到新分頁 / Switch to new tab

        # 更新分頁標題 (當網頁標題改變時)
        # Update tab title when browser title changes
        browser_widget.browser.titleChanged.connect(
            lambda t, i=index: self.browser_tab.setTabText(i, t)
        )

    def add_plus_tab(self):
        """新增一個固定的「+」分頁 / Add a fixed "+" tab"""
        add_new_page_widget = QWidget()
        self.browser_tab.addTab(add_new_page_widget, "+")
        # 禁止關閉「+」分頁 / Disable closing of "+" tab
        self.browser_tab.tabBar().setTabButton(self.browser_tab.count() - 1,
                                               QTabBar.ButtonPosition.RightSide, None)
        # 點擊分頁時觸發事件 / Connect tab click event
        self.browser_tab.tabBar().tabBarClicked.connect(self.handle_tab_changed)

    def handle_tab_changed(self, index: int):
        """如果點到「+」分頁，就開新分頁
        If "+" tab is clicked, open a new tab
        """
        if self.browser_tab.tabText(index) == "+":  # 檢查是否為「+」分頁 / Check if "+" tab
            # 建立新分頁（會自動切換到新分頁）
            # Create a new tab (auto switch to it)
            self.add_browser_tab(
                BrowserWidget(start_url="https://www.google.com/",
                              search_prefix=self.search_prefix),
                "Google"
            )

    def close_tab(self, index: int):
        """關閉指定分頁，但保留「+」
        Close the specified tab, but keep the "+"
        """
        widget = self.browser_tab.widget(index)  # 取得要關閉的分頁元件 / Get tab widget
        self.browser_tab.removeTab(index)  # 移除分頁 / Remove tab
        widget.deleteLater()  # 釋放資源 / Free memory
