from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    # Forward declaration to avoid circular import at runtime
    # 僅在型別檢查時匯入，避免執行時循環匯入問題
    from je_editor.pyside_ui.browser.browser_widget import BrowserWidget


class BrowserLineSearch(QLineEdit):
    """
    A custom QLineEdit widget for browser search input.
    自訂的 QLineEdit，用於瀏覽器搜尋輸入。
    """

    def __init__(self, browser_widget: BrowserWidget):
        """
        Initialize the search line with a reference to the browser widget.
        初始化搜尋輸入框，並保存瀏覽器元件的參考。
        """
        super().__init__()
        # 記錄初始化訊息到 logger
        jeditor_logger.info("Init BrowserLineSearch "
                            f"browser_widget: {browser_widget}")

        # 設定屬性：當視窗關閉時自動刪除
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # 保存瀏覽器元件的參考，用於觸發搜尋
        self.browser = browser_widget

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events.
        當使用者按下按鍵時觸發：
        - 如果是 Enter 或 Return，則呼叫瀏覽器的 search() 方法。
        - 其他情況則交由父類別處理。
        """
        if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            jeditor_logger.info("Browser Search")
            # 呼叫瀏覽器元件的搜尋方法
            self.browser.search()

        # 呼叫父類別的 keyPressEvent，確保其他按鍵行為正常
        super().keyPressEvent(event)