from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


def set_run_menu(ui_we_want_to_set: QMainWindow):
    # TODO run
    ui_we_want_to_set.run_program_action = QAction("Run Program")
    ui_we_want_to_set.run_program_action.triggered.connect(temp)
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_program_action)
    # TODO run on shell
    ui_we_want_to_set.run_on_shell_action = QAction("Run On Shell")
    ui_we_want_to_set.run_on_shell_action.triggered.connect(temp)
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
