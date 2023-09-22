from PySide6.QtWidgets import QWidget, QGridLayout, QLabel
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class IpythonWidget(QWidget):
    def __init__(self, kernel_name: str = "python3"):
        super().__init__()
        self.grid_layout = QGridLayout()
        self.ipython_enable = False
        try:
            from qtconsole.manager import QtKernelManager
            from qtconsole.rich_jupyter_widget import RichJupyterWidget
            kernel_manager = QtKernelManager(kernel_name=kernel_name)
            kernel_manager.start_kernel()
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            jupyter_widget = RichJupyterWidget()
            jupyter_widget.kernel_manager = kernel_manager
            jupyter_widget.kernel_client = kernel_client
            self.show_widget = jupyter_widget
            self.ipython_enable = True
            self.grid_layout.addWidget(self.show_widget, 0, 0, -1, -1)
        except ImportError:
            self.ipython_enable = False
            self.show_widget = QLabel(language_wrapper.language_word_dict.get("please_install_qtcontsole_label"))
            self.grid_layout.addWidget(self.show_widget)

        self.setLayout(self.grid_layout)

    def close(self):
        if self.ipython_enable:
            self.show_widget.kernel_client.stop_channels()
            self.show_widget.kernel_manager.shutdown_kernel()
        super().close()
