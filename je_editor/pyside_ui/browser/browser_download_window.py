from PySide6.QtCore import Qt
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWidgets import QWidget, QBoxLayout, QPlainTextEdit

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class BrowserDownloadWindow(QWidget):
    """
    A window widget to display details of a browser download.
    瀏覽器下載視窗，用來顯示下載的詳細資訊。
    """

    def __init__(self, download_instance: QWebEngineDownloadRequest):
        """
        Initialize the download window with a given QWebEngineDownloadRequest.
        使用指定的 QWebEngineDownloadRequest 初始化下載視窗。
        """
        super().__init__()
        # 記錄初始化訊息到 logger
        jeditor_logger.info("Init BrowserDownloadWindow "
                            f"download_instance: {download_instance}")

        # 設定視窗屬性：當視窗關閉時自動刪除
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # 建立垂直方向的 BoxLayout
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # 建立文字框來顯示下載細節，並設為唯讀
        self.show_download_detail_plaintext = QPlainTextEdit()
        self.show_download_detail_plaintext.setReadOnly(True)

        # 設定視窗標題，支援多語言
        self.setWindowTitle(language_wrapper.language_word_dict.get("browser_download_detail"))

        # 儲存下載實例
        self.download_instance = download_instance

        # 綁定下載事件到對應的處理函式
        self.download_instance.isFinishedChanged.connect(self.print_finish)  # 當下載完成時
        self.download_instance.interruptReasonChanged.connect(self.print_interrupt)  # 當下載被中斷時
        self.download_instance.stateChanged.connect(self.print_state)  # 當下載狀態改變時

        # 接受下載請求，開始下載
        self.download_instance.accept()

        # 將文字框加入版面配置
        self.box_layout.addWidget(self.show_download_detail_plaintext)
        self.setLayout(self.box_layout)

    def print_finish(self):
        """
        Slot function triggered when download finishes.
        當下載完成時觸發，將完成狀態輸出到 logger 與文字框。
        """
        jeditor_logger.info("BrowserDownloadWindow Print Download is Finished")
        self.show_download_detail_plaintext.appendPlainText(str(self.download_instance.isFinished()))

    def print_interrupt(self):
        """
        Slot function triggered when download is interrupted.
        當下載被中斷時觸發，將中斷原因輸出到 logger 與文字框。
        """
        jeditor_logger.info("BrowserDownloadWindow Print interruptReason")
        self.show_download_detail_plaintext.appendPlainText(str(self.download_instance.interruptReason()))

    def print_state(self):
        """
        Slot function triggered when download state changes.
        當下載狀態改變時觸發，將狀態輸出到 logger 與文字框。
        """
        jeditor_logger.info("BrowserDownloadWindow Print State")
        self.show_download_detail_plaintext.appendPlainText(str(self.download_instance.state()))
