from IPython.lib import guisupport
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class IpythonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout()
        self.ipython_enable = False
        try:
            from qtconsole.inprocess import QtInProcessKernelManager
            from qtconsole.rich_jupyter_widget import RichIPythonWidget
            app = guisupport.get_app_qt4()
            kernel_manager = QtInProcessKernelManager()
            kernel_manager.start_kernel()
            kernel = kernel_manager.kernel
            kernel.gui = "qt"
            kernel_client = kernel_manager.client()
            kernel_client.start_channels()
            control = RichIPythonWidget()
            control.kernel_manager = kernel_manager
            control.kernel_client = kernel_client

            def stop():
                kernel_client.stop_channels()
                kernel_manager.shutdown_kernel()
                app.exit()

            control.exit_requested.connect(stop)
            self.show_widget = control
            self.ipython_enable = True
            self.grid_layout.addWidget(self.show_widget, 0, 0, -1, -1)
            guisupport.start_event_loop_qt4(app)
        except ImportError:
            self.ipython_enable = False
            self.show_widget = QLabel(language_wrapper.language_word_dict.get("please_install_qtcontsole_label"))
            self.grid_layout.addWidget(self.show_widget)

        self.setLayout(self.grid_layout)

    def close(self):
        super().close()

