from __future__ import annotations

from typing import TYPE_CHECKING

from IPython.lib import guisupport
from PySide6.QtWidgets import QWidget, QGridLayout
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


class IpythonWidget(QWidget):

    def __init__(self, main_window: EditorMain):
        jeditor_logger.info(f"Init IpythonWidget main_window: {main_window}")
        super().__init__()
        self.grid_layout = QGridLayout()
        app = guisupport.get_app_qt4()
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()
        self.jupyter_widget = RichJupyterWidget()
        self.jupyter_widget.kernel_manager = self.kernel_manager
        self.jupyter_widget.kernel_client = self.kernel_client
        self.grid_layout.addWidget(self.jupyter_widget, 0, 0, -1, -1)
        guisupport.start_event_loop_qt4(app)

        self.setLayout(self.grid_layout)

    def close(self):
        jeditor_logger.info("IpythonWidget close")
        if self.kernel_client:
            self.kernel_client.stop_channels()
        if self.kernel_manager:
            self.kernel_manager.restart_kernel()
            self.kernel_manager.shutdown_kernel()
        super().close()
