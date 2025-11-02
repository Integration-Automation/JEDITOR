from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class CreateFileDialog(QWidget):
    """
    建立新檔案的對話框
    Dialog for creating a new file
    """

    def __init__(self):
        jeditor_logger.info("Init CreateFileDialog")
        super().__init__()

        # 垂直佈局 (上到下)
        # Vertical layout (top to bottom)
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # 檔案名稱輸入框 / File name input field
        self.file_name_input = QLineEdit()

        # 建立檔案按鈕 / Create file button
        self.create_file_button = QPushButton()
        self.create_file_button.setText(language_wrapper.language_word_dict.get("create_file_dialog_pushbutton"))
        self.create_file_button.clicked.connect(self.create_file)

        # 水平佈局 (放置按鈕) / Horizontal layout (for button)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.create_file_button)

        # 將元件加入主佈局 / Add widgets to main layout
        self.box_layout.addWidget(self.file_name_input)
        self.box_layout.addLayout(self.box_h_layout)

        # 設定視窗標題 / Set window title
        self.setWindowTitle(language_wrapper.language_word_dict.get("create_file_dialog_pushbutton"))
        self.setLayout(self.box_layout)

    def create_file(self):
        """
        建立檔案的邏輯：
        1. 檢查輸入是否為空
        2. 若為空，顯示警告訊息
        3. 否則建立新檔案並關閉對話框
        File creation logic:
        1. Check if input is empty
        2. If empty, show warning message
        3. Otherwise, create new file and close dialog
        """
        jeditor_logger.info("CreateFileDialog create_file")
        file_name = self.file_name_input.text().strip()

        if file_name == "":
            # 若未輸入檔名，顯示提示訊息
            # Show warning if no file name is entered
            create_file_message_box = QMessageBox(self)
            create_file_message_box.setText(
                language_wrapper.language_word_dict.get("input_file_name_dialog_pushbutton")
            )
            create_file_message_box.show()
        else:
            # 建立新檔案 (若存在則覆蓋)
            # Create new file (overwrite if exists)
            with open(file_name, "w+") as file:
                file.write("")
            self.close()  # 關閉對話框 / close dialog
