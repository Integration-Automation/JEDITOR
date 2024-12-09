from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget

from je_editor.utils.logging.loggin_instance import jeditor_logger


class DestroyDock(QDockWidget):

    def __init__(self):
        jeditor_logger.info("Init DestroyDock")
        super().__init__()
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        # Attr
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def closeEvent(self, event) -> None:
        jeditor_logger.info(f"DestroyDock closeEvent event: {event}")
        self.widget().close()
        super().close()
