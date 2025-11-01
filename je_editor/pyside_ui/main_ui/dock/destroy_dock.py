from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget

from je_editor.utils.logging.loggin_instance import jeditor_logger


class DestroyDock(QDockWidget):
    """
    DestroyDock 繼承自 QDockWidget，主要用於建立一個可停駐的視窗，
    並在關閉時自動釋放資源與記錄日誌。

    DestroyDock inherits from QDockWidget, mainly used to create a dockable window,
    and automatically release resources and log events when closed.
    """

    def __init__(self):
        # 初始化時記錄日誌 / Log initialization
        jeditor_logger.info("Init DestroyDock")
        super().__init__()

        # 設定允許停駐的區域 (可停駐在所有邊)
        # Allow docking in all areas (top, bottom, left, right)
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        # 設定屬性：當視窗關閉時，自動刪除物件以釋放記憶體
        # Set attribute: delete object on close to free memory
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def closeEvent(self, event) -> None:
        """
        覆寫 closeEvent，在關閉時額外處理：
        - 記錄關閉事件
        - 關閉內部 widget
        - 呼叫父類別的 close()

        Override closeEvent to:
        - Log the close event
        - Close the internal widget
        - Call parent close()
        """
        # 記錄關閉事件 / Log close event
        jeditor_logger.info(f"DestroyDock closeEvent event: {event}")

        # 關閉 dock 內部的 widget，確保資源釋放
        # Close the internal widget to ensure resource release
        self.widget().close()

        # 呼叫父類別的 close()，完成 Qt 預設的關閉流程
        # Call parent close() to complete default Qt closing process
        super().close()