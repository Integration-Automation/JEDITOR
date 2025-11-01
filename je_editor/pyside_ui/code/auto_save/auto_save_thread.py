import time
from pathlib import Path
from threading import Thread
from typing import Union

from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
from je_editor.utils.file.save.save_file import write_file
from je_editor.utils.logging.loggin_instance import jeditor_logger


class CodeEditSaveThread(Thread):

    def __init__(
            self, file_to_save: Union[str, None] = None, editor: Union[None, CodeEditor] = None):
        """
        This thread is used to auto save current file.
        這個執行緒用來自動儲存當前檔案。

        :param file_to_save: file we want to auto save
                             要自動儲存的檔案路徑
        :param editor: code editor to auto save
                       要自動儲存內容的編輯器元件
        """
        jeditor_logger.info(f"Init CodeEditSaveThread "
                            f"file_to_save: {file_to_save} "
                            f"editor: {editor}")
        super().__init__()
        self.file: str = file_to_save
        self.editor: Union[None, CodeEditor] = editor
        self.still_run: bool = True   # 控制執行緒是否繼續運行 / Flag to control thread loop
        self.daemon = True            # 設定為守護執行緒，主程式結束時自動結束
                                      # Set as daemon thread, ends with main program
        self.skip_this_round: bool = False  # 是否跳過本次儲存 / Skip this save cycle

    def run(self) -> None:
        """
        loop and save current edit file
        持續迴圈，每隔一段時間自動儲存當前編輯檔案
        """
        jeditor_logger.info("CodeEditSaveThread run")
        if self.file is not None:
            path = Path(self.file)
            # 當檔案存在且編輯器不為 None 時持續運行
            # Keep running while file exists and editor is valid
            while path.is_file() and self.editor is not None:
                time.sleep(5)  # 每 5 秒檢查一次 / Check every 5 seconds
                if self.still_run:
                    if self.skip_this_round:
                        # 如果設定跳過本輪，什麼都不做
                        # Skip this round if flag is set
                        pass
                    else:
                        # 將編輯器內容寫入檔案
                        # Write editor content to file
                        write_file(self.file, self.editor.toPlainText())
                else:
                    # 如果 still_run 為 False，結束迴圈
                    # Exit loop if still_run is False
                    break