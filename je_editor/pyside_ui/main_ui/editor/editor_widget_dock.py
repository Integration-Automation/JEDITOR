from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea
from frontengine.utils.multi_language.language_wrapper import language_wrapper

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.file.save.save_file import write_file
from je_editor.utils.logging.loggin_instance import jeditor_logger


class FullEditorWidget(QWidget):

    def __init__(self, current_file: str):
        jeditor_logger.info(f"Init FullEditorWidget current_file: {current_file}")
        super().__init__()
        # Init variable
        self.current_file = current_file
        # Attr
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # UI
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))
        # code edit and code result plaintext
        self.code_edit = CodeEditor(self)
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
        jeditor_logger.info(f"FullEditorWidget closeEvent event: {event}")
        path = Path(self.current_file)
        if path.exists() and path.is_file():
            write_file(self.current_file, self.code_edit.toPlainText())
        super().closeEvent(event)
