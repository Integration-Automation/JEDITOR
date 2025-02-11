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
        :param file_to_save: file we want to auto save
        :param editor: code editor to auto save
        """
        jeditor_logger.info(f"Init CodeEditSaveThread "
                            f"file_to_save: {file_to_save} "
                            f"editor: {editor}")
        super().__init__()
        self.file: str = file_to_save
        self.editor: Union[None, CodeEditor] = editor
        self.still_run: bool = True
        # set daemon
        self.daemon = True
        self.skip_this_round: bool = False

    def run(self) -> None:
        """
        loop and save current edit file
        """
        jeditor_logger.info("CodeEditSaveThread run")
        if self.file is not None:
            path = Path(self.file)
            while path.is_file() and self.editor is not None:
                time.sleep(5)
                if self.still_run:
                    if self.skip_this_round:
                        pass
                    else:
                        write_file(self.file, self.editor.toPlainText())
                else:
                    break
