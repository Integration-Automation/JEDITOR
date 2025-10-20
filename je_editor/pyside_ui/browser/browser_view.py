from __future__ import annotations

from typing import List, TYPE_CHECKING

from PySide6.QtCore import Signal

if TYPE_CHECKING:
    from je_editor.pyside_ui.browser.browser_widget import BrowserWidget

from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWebEngineWidgets import QWebEngineView

from je_editor.pyside_ui.browser.browser_download_window import BrowserDownloadWindow
from je_editor.utils.logging.loggin_instance import jeditor_logger


class BrowserView(QWebEngineView):
    new_tab_requested = Signal(QWebEngineView)
    """
    A custom QWebEngineView that supports file downloads and manages download windows.
    自訂的 QWebEngineView，支援檔案下載並管理下載視窗。
    """

    def __init__(self, start_url: str = "https://www.google.com/",
                 main_widget: BrowserWidget = None, parent=None):
        """
        Initialize the browser view with a start URL.
        使用指定的起始網址初始化瀏覽器視圖。
        """
        super().__init__(parent)
        # 記錄初始化訊息
        jeditor_logger.info("Init BrowserView "
                            f"start_url: {start_url}")

        # 設定初始網址
        self.setUrl(start_url)

        # 儲存下載請求的清單
        self.download_list: List[QWebEngineDownloadRequest] = list()

        # 儲存下載視窗的清單
        self.download_window_list: List[BrowserDownloadWindow] = list()

        # 綁定下載事件：當有下載請求時觸發 download_file
        self.page().profile().downloadRequested.connect(self.download_file)

        self.main_widget = main_widget


    def download_file(self, download_instance: QWebEngineDownloadRequest):
        """
        Handle a new download request.
        當有新的下載請求時觸發：
        - 將下載請求加入清單
        - 建立並顯示下載細節視窗
        """
        jeditor_logger.info("Download File "
                            f"download_instance: {download_instance}")

        # 加入下載請求到清單
        self.download_list.append(download_instance)

        # 建立下載細節視窗
        download_detail_window = BrowserDownloadWindow(download_instance)

        # 加入視窗到清單並顯示
        self.download_window_list.append(download_detail_window)
        download_detail_window.show()

    def closeEvent(self, event) -> None:
        """
        Handle the close event of the browser view.
        當瀏覽器視窗關閉時：
        - 取消所有進行中的下載
        - 關閉所有下載細節視窗
        """
        jeditor_logger.info(f"BrowserView closeEvent event: {event}")

        # 取消所有下載
        for download_instance in self.download_list:
            download_instance.cancel()

        # 關閉所有下載視窗
        for download_window in self.download_window_list:
            download_window.close()

        # 呼叫父類別的 closeEvent，確保正常關閉
        super().closeEvent(event)
