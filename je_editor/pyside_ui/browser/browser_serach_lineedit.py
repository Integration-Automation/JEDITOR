from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit

if TYPE_CHECKING:
    from je_editor.pyside_ui.browser.browser_widget import JEBrowser


class BrowserLineSearch(QLineEdit):

    def __init__(self, browser_widget: JEBrowser):
        super().__init__()
        self.browser = browser_widget

    def keyPressEvent(self, event) -> None:
        if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return]:
            self.browser.search()
        super().keyPressEvent(event)
