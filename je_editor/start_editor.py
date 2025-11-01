import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def start_editor(debug_mode: bool = False) -> None:
    """
    功能說明 (Function Description):
    啟動編輯器主程式，建立 QApplication 實例，套用主題，並顯示主視窗。
    Start the main editor application, create QApplication instance, apply theme, and show main window.

    :param debug_mode: 是否啟用除錯模式 / whether to enable debug mode
    """

    # 嘗試取得現有的 QCoreApplication 實例
    # Try to get an existing QCoreApplication instance
    new_editor = QCoreApplication.instance()

    # 如果沒有現有實例，建立新的 QApplication
    # If no instance exists, create a new QApplication
    if new_editor is None:
        new_editor = QApplication(sys.argv)

    # 建立主視窗，傳入 debug_mode
    # Create the main editor window, passing debug_mode
    window = EditorMain(debug_mode)

    # 套用 qt-material 主題 (dark amber)
    # Apply qt-material theme (dark amber)
    apply_stylesheet(new_editor, theme='dark_amber.xml')

    # 最大化顯示主視窗
    # Show the main window maximized
    window.showMaximized()

    # 啟動事件迴圈，並在結束時退出程式
    # Start the event loop and exit the program when it ends
    sys.exit(new_editor.exec())