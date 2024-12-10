from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.browser.browser_widget import BrowserWidget


class BrowserLineSearch(QLineEdit):

    def __init__(self, browser_widget: BrowserWidget):
        super().__init__()
        jeditor_logger.info(f"Init BrowserLineSearch "
                            f"browser_widget: {browser_widget}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.browser = browser_widget

    def keyPressEvent(self, event) -> None:
        if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            jeditor_logger.info("Browser Search")
            self.browser.search()
        super().keyPressEvent(event)
