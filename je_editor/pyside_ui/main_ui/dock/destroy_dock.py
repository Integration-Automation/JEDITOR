from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget


class DestroyDock(QDockWidget):

    def __init__(self):
        super().__init__()
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        # Attr
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def closeEvent(self, event) -> None:
        self.widget().close()
        super().close()
