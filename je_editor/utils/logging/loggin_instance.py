import logging
from logging.handlers import RotatingFileHandler

# 設定 root logger 的最低層級為 DEBUG
# Set the root logger level to DEBUG
logging.root.setLevel(logging.DEBUG)

# 建立一個名為 "JEditor" 的 logger
# Create a logger named "JEditor"
jeditor_logger = logging.getLogger("JEditor")

# 設定 JEditor logger 的層級為 WARNING (只會輸出 WARNING 以上的訊息)
# Set the JEditor logger level to WARNING (only WARNING and above will be logged)
jeditor_logger.setLevel(logging.WARNING)

# 定義日誌格式：時間 | logger 名稱 | 等級 | 訊息
# Define log format: time | logger name | level | message
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')


class JEditorLoggingHandler(RotatingFileHandler):
    """
    自訂的 Logging Handler，繼承自 RotatingFileHandler
    Custom Logging Handler, inherits from RotatingFileHandler

    功能：
    - 將日誌輸出到檔案 (支援檔案大小輪替)
    - 預設檔名為 JEditor.log
    """

    # redirect logging stderr output to queue (註解說明，但目前未實作)
    # 註解提到要將 stderr 輸出導向 queue，但目前程式碼僅繼承 RotatingFileHandler

    def __init__(self, filename: str = "JEditor.log", mode="w",
                 maxBytes: int = 1073741824, backupCount: int = 0):
        """
        :param filename: 日誌檔案名稱 / log file name
        :param mode: 檔案開啟模式 (預設 w 覆寫) / file open mode (default "w" overwrite)
        :param maxBytes: 單一檔案最大大小 (預設 1GB) / max file size (default 1GB)
        :param backupCount: 保留的備份檔案數量 / number of backup files to keep
        """
        super().__init__(filename=filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount)
        self.formatter = formatter  # 設定日誌格式 / set log formatter
        self.setLevel(logging.DEBUG)  # 設定 handler 層級為 DEBUG / set handler level to DEBUG

    def emit(self, record: logging.LogRecord) -> None:
        """
        實際輸出日誌的方法，這裡直接呼叫父類別的 emit
        Method to emit log records, here just call parent emit
        """
        super().emit(record)


# 建立檔案處理器並加入到 JEditor logger
# Create file handler and add it to JEditor logger
file_handler = JEditorLoggingHandler()
jeditor_logger.addHandler(file_handler)
