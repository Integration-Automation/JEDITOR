from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.code_process.code_exec import exec_manage
from je_editor.pyside_ui.file_dialog.save_file_dialog import choose_file_get_save_filename
from je_editor.pyside_ui.shell_process.shell_exec import shell_manager


def set_run_menu(ui_we_want_to_set: QMainWindow):

    ui_we_want_to_set.run_program_action = QAction("Run Program")
    ui_we_want_to_set.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_program_action)
    ui_we_want_to_set.run_on_shell_action = QAction("Run On Shell")
    ui_we_want_to_set.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_on_shell_action)
    ui_we_want_to_set.clean_result_action = QAction("Clean Result")
    ui_we_want_to_set.clean_result_action.triggered.connect(
        lambda: clean_result(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.clean_result_action)

    ui_we_want_to_set.stop_program_action = QAction("Stop Program")
    ui_we_want_to_set.stop_program_action.triggered.connect(
        stop_program
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.stop_program_action)


def run_program(ui_we_want_to_set):
    choose_file_get_save_filename(ui_we_want_to_set)
    exec_manage.main_window = ui_we_want_to_set
    exec_manage.later_init()
    exec_manage.exec_code(
        ui_we_want_to_set.current_file
    )


def shell_exec(ui_we_want_to_set):
    shell_manager.main_window = ui_we_want_to_set
    shell_manager.later_init()
    shell_manager.exec_shell(
        ui_we_want_to_set.code_edit.toPlainText()
    )


def stop_program():
    exec_manage.exit_program()


def clean_result(ui_we_want_to_set):
    ui_we_want_to_set.code_result.setPlainText("")
