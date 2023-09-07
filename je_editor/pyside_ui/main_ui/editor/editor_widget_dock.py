from pathlib import Path

from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.file.save.save_file import write_file


class FullEditorWidget(QWidget):

    def __init__(self, current_file: str):
        super().__init__()
        # Init variable
        self.auto_save_thread = None
        self.current_file = current_file
        # UI
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle("JEditor")
        # code edit and code result plaintext
        self.code_edit = CodeEditor()
        self.code_edit_scroll_area = QScrollArea()
        self.code_edit_scroll_area.setWidgetResizable(True)
        self.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_edit_scroll_area.setWidget(self.code_edit)
        self.grid_layout.addWidget(self.code_edit_scroll_area, 0, 0)
        # Font
        self.code_edit.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )

    def closeEvent(self, event) -> None:
        path = Path(self.current_file)
        if path.exists() and path.is_file():
            write_file(self.current_file, self.code_edit.toPlainText())
        super().closeEvent(event)
