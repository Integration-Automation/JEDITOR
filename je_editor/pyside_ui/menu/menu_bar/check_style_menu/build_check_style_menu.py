from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow
from yapf.yapflib.yapf_api import FormatCode


def set_check_menu(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.check_python_action = QAction("yapf")
    ui_we_want_to_set.check_python_action.setShortcut("Ctrl+y")
    ui_we_want_to_set.check_python_action.triggered.connect(
        lambda: check_python_code(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_python_action)


def check_python_code(ui_we_want_to_set):
    code_text = ui_we_want_to_set.code_edit.toPlainText()
    ui_we_want_to_set.code_result.setPlainText("")
    format_code = FormatCode(
        unformatted_source=code_text,
        verify=True,
        style_config="google"
    )
    if type(format_code) == tuple:
        ui_we_want_to_set.code_edit.setPlainText(format_code[0])
