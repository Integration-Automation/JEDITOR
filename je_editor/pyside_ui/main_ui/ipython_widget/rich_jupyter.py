from __future__ import annotations  # 啟用未來版本的型別註解功能 / Enable postponed evaluation of type annotations

from typing import TYPE_CHECKING  # 僅在型別檢查時使用，避免循環匯入 / Used only for type checking to avoid circular imports

from IPython.lib import guisupport  # 提供與 Qt GUI 整合的支援 / Provides support for integrating IPython with Qt GUI
from PySide6.QtWidgets import QWidget, QGridLayout  # PySide6 視窗元件 / PySide6 widgets
from qtconsole.inprocess import QtInProcessKernelManager  # 管理內嵌的 Jupyter kernel / Manages an in-process Jupyter kernel
from qtconsole.rich_jupyter_widget import RichJupyterWidget  # Jupyter 富文本控制台元件 / Rich Jupyter console widget

from je_editor.utils.logging.loggin_instance import jeditor_logger  # 專案內的日誌紀錄器 / Project logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴 / Import only for type checking to avoid circular dependency


class IpythonWidget(QWidget):
    """
    IpythonWidget 類別
    - 在 PySide6 GUI 中嵌入一個 Jupyter/IPython 控制台
    - 提供互動式 Python 環境，方便在應用程式內直接執行程式碼
    IpythonWidget class
    - Embeds a Jupyter/IPython console inside a PySide6 GUI
    - Provides an interactive Python environment within the application
    """

    def __init__(self, main_window: EditorMain):
        # 初始化時記錄日誌 / Log initialization
        jeditor_logger.info(f"Init IpythonWidget main_window: {main_window}")
        super().__init__()

        # 建立網格佈局 / Create grid layout
        self.grid_layout = QGridLayout()

        # 取得 Qt 應用程式實例 (Qt4 API，但可在 PySide6 中使用) / Get Qt application instance
        app = guisupport.get_app_qt4()

        # === 建立並啟動 Jupyter Kernel / Create and start Jupyter kernel ===
        self.kernel_manager = QtInProcessKernelManager()  # 內嵌 kernel 管理器 / In-process kernel manager
        self.kernel_manager.start_kernel()  # 啟動 kernel / Start kernel
        self.kernel = self.kernel_manager.kernel  # 取得 kernel 實例 / Get kernel instance

        # 建立 kernel client 並啟動通訊管道 / Create kernel client and start communication channels
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        # === 建立 Jupyter 控制台元件 / Create Jupyter console widget ===
        self.jupyter_widget = RichJupyterWidget()
        self.jupyter_widget.kernel_manager = self.kernel_manager
        self.jupyter_widget.kernel_client = self.kernel_client

        # 將控制台加入佈局 (佔滿整個視窗) / Add console widget to layout (fill entire window)
        self.grid_layout.addWidget(self.jupyter_widget, 0, 0, -1, -1)

        # 啟動 Qt 事件迴圈，讓 Jupyter 控制台能正常運作 / Start Qt event loop for Jupyter console
        guisupport.start_event_loop_qt4(app)

        # 設定主佈局 / Apply layout
        self.setLayout(self.grid_layout)

    def close(self):
        """
        覆寫 close 方法，確保關閉時正確釋放資源
        Override close method to properly release resources
        """
        jeditor_logger.info("IpythonWidget close")

        # 停止 kernel client 的通訊管道 / Stop kernel client channels
        if self.kernel_client:
            self.kernel_client.stop_channels()

        # 重啟並關閉 kernel，確保乾淨退出 / Restart and shutdown kernel for clean exit
        if self.kernel_manager:
            self.kernel_manager.restart_kernel()
            self.kernel_manager.shutdown_kernel()

        # 呼叫父類別的 close 方法 / Call parent close method
        super().close()
