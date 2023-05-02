from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox

from je_editor.pyside_ui.code_process.code_exec import exec_manage
from je_editor.pyside_ui.file_dialog.save_file_dialog import choose_file_get_save_filename
from je_editor.pyside_ui.shell_process.shell_exec import shell_manager


def set_run_menu(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.run_menu.run_program_action = QAction("Run Program")
    ui_we_want_to_set.run_menu.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_program_action)
    ui_we_want_to_set.run_menu.run_on_shell_action = QAction("Run On Shell")
    ui_we_want_to_set.run_menu.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_on_shell_action)
    ui_we_want_to_set.run_menu.clean_result_action = QAction("Clean Result")
    ui_we_want_to_set.run_menu.clean_result_action.triggered.connect(
        lambda: clean_result(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.clean_result_action)

    ui_we_want_to_set.run_menu.stop_program_action = QAction("Stop Program")
    ui_we_want_to_set.run_menu.stop_program_action.triggered.connect(
        stop_program
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_program_action)
    # Run help menu
    ui_we_want_to_set.run_menu.run_help_menu = ui_we_want_to_set.run_menu.addMenu("Run Help")
    # Run help action
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action = QAction("Run Help")
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action.triggered.connect(
        show_run_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.run_help_action)
    # Shell help action
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action = QAction("Shell Help")
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action.triggered.connect(
        show_shell_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.shell_help_action)


def run_program(ui_we_want_to_set: QMainWindow):
    choose_file_get_save_filename(ui_we_want_to_set)
    exec_manage.main_window = ui_we_want_to_set
    exec_manage.later_init()
    exec_manage.exec_code(
        ui_we_want_to_set.current_file
    )


def shell_exec(ui_we_want_to_set: QMainWindow):
    shell_manager.main_window = ui_we_want_to_set
    shell_manager.later_init()
    shell_manager.exec_shell(
        ui_we_want_to_set.code_edit.toPlainText()
    )


def stop_program():
    exec_manage.exit_program()


def clean_result(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.code_result.setPlainText("")


def show_run_help():
    message_box = QMessageBox()
    message_box.setText(
        """
If you are unable to run a Python program, please make sure you are not using the default system Python.
(For Windows, you can use the Windows Store or Venv.)
(For Linux & MacOS, you can use Venv.)
        """
    )
    message_box.exec()


def show_shell_help():
    message_box = QMessageBox()
    message_box.setText(
        """
When executing a shell command, if you encounter a decoding error, 
please make sure that the current encoding is consistent with the default encoding of the system shell.
        """
    )
    message_box.exec()
