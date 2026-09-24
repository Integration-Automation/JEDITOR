from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.encodings.text_codec import DEFAULT_ENCODING, LINE_ENDING_LF
from je_editor.utils.exception.exceptions import JEditorSaveFileException
from je_editor.utils.file.save.save_file import write_file_with_encoding
from je_editor.utils.logging.loggin_instance import jeditor_logger


class FullEditorWidget(QWidget):
    """
    FullEditorWidget 提供一個完整的單檔編輯器介面，
    包含程式碼編輯區、捲動支援，以及關閉時自動儲存功能。

    FullEditorWidget provides a full single-file editor interface,
    including code editing area, scroll support, and auto-save on close.
    """

    def __init__(self, current_file: str, encoding: str = DEFAULT_ENCODING,
                 line_ending: str = LINE_ENDING_LF) -> None:
        # 初始化時記錄日誌 / Log initialization
        jeditor_logger.info(f"Init FullEditorWidget current_file: {current_file}")
        super().__init__()

        # ---------------- Init variable 初始化變數 ----------------
        self.current_file = current_file  # 目前編輯的檔案路徑 / Current editing file path
        # 存檔時寫回檔案原本的編碼與行尾 / Saved back in the file's own encoding and line ending
        self.file_encoding = encoding
        self.line_ending = line_ending

        # ---------------- Attributes 屬性設定 ----------------
        # 設定關閉時自動刪除物件，釋放記憶體
        # Delete object on close to free memory
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # ---------------- UI 初始化 ----------------
        self.grid_layout = QGridLayout(self)
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))

        # 建立程式碼編輯器並放入捲動區域
        # Create code editor and put inside scroll area
        self.code_edit = CodeEditor(self)
        self.code_edit_scroll_area = QScrollArea()
        self.code_edit_scroll_area.setWidgetResizable(True)
        self.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.code_edit_scroll_area.setWidget(self.code_edit)

        # 將編輯器加入版面配置
        # Add editor to layout
        self.grid_layout.addWidget(self.code_edit_scroll_area, 0, 0)

        # 設定字體樣式 (從使用者設定檔讀取)
        # Set font style (from user settings)
        self.code_edit.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        覆寫 closeEvent，在關閉視窗時自動儲存檔案內容。
        Override closeEvent to auto-save file content when closing window.
        """
        jeditor_logger.info(f"FullEditorWidget closeEvent event: {event}")
        path = Path(self.current_file)
        # 沒改過就不寫：以前一律以 UTF-8 與系統行尾寫回，沒動過的 LF 檔也被改成 CRLF
        # Unedited, nothing is written: it used to write back in UTF-8 with the
        # platform's line endings every time, turning an untouched LF file CRLF
        if path.is_file() and self.code_edit.document().isModified():
            try:
                write_file_with_encoding(
                    self.current_file, self.code_edit.toPlainText(),
                    self.file_encoding, self.line_ending)
            except JEditorSaveFileException as error:
                from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import report_save_failure
                report_save_failure(self, self.current_file, error)
        # 呼叫父類別的 closeEvent，完成 Qt 預設流程
        # Call parent closeEvent to complete Qt default process
        super().closeEvent(event)
