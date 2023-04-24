from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.shell_process.shell_exec import shell_manager


def set_run_menu(ui_we_want_to_set: QMainWindow):
    # TODO run
    ui_we_want_to_set.run_program_action = QAction("Run Program")
    ui_we_want_to_set.run_program_action.triggered.connect(temp)
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_program_action)
    ui_we_want_to_set.run_on_shell_action = QAction("Run On Shell")
    ui_we_want_to_set.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_on_shell_action)
    # TODO clean result
    ui_we_want_to_set.clean_result_action = QAction("Clean Result")
    ui_we_want_to_set.clean_result_action.triggered.connect(temp)
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.clean_result_action)
    # TODO stop program
    ui_we_want_to_set.stop_program_action = QAction("Stop Program")
    ui_we_want_to_set.stop_program_action.triggered.connect(temp)
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.stop_program_action)


def temp():
    print("temp")


def shell_exec(ui_we_want_to_set):
    shell_manager.main_window = ui_we_want_to_set
    shell_manager.later_init()
    shell_manager.exec_shell(
        ui_we_want_to_set.code_edit.toPlainText()
    )
