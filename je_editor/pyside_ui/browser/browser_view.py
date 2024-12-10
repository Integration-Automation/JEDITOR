from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWebEngineWidgets import QWebEngineView

from je_editor.pyside_ui.browser.browser_download_window import BrowserDownloadWindow
from je_editor.utils.logging.loggin_instance import jeditor_logger


class BrowserView(QWebEngineView):

    def __init__(self, start_url: str = "https://www.google.com/"):
        super().__init__()
        jeditor_logger.info(f"Init BrowserView "
                            f"start_url: {start_url}")
        self.setUrl(start_url)
        self.download_list: List[QWebEngineDownloadRequest] = list()
        self.download_window_list: List[BrowserDownloadWindow] = list()
        self.page().profile().downloadRequested.connect(self.download_file)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def download_file(self, download_instance: QWebEngineDownloadRequest):
        jeditor_logger.info(f"Download File "
                            f"download_instance: {download_instance}")
        self.download_list.append(download_instance)
        download_detail_window = BrowserDownloadWindow(download_instance)
        self.download_window_list.append(download_detail_window)
        download_detail_window.show()

    def closeEvent(self, event) -> None:
        jeditor_logger.info(f"BrowserView closeEvent event: {event}")
        for download_instance in self.download_list:
            download_instance.cancel()
        for download_window in self.download_window_list:
            download_window.close()
        super().closeEvent(event)
