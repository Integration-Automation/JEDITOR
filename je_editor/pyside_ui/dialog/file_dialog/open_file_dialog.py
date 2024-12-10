from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save.auto_save_manager import init_new_auto_save_thread, file_is_open_manager_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict, read_user_setting
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.venv_check.check_venv import check_and_choose_venv

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_file_path(parent_qt_instance: EditorMain) -> None:
    """
    Open file and set code edit content
    :param parent_qt_instance: Pyside parent
    :return: None
    """
    jeditor_logger.info("open_file_dialog.py choose_file_get_open_file_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    widget = parent_qt_instance.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        file_path = QFileDialog().getOpenFileName(
            parent=parent_qt_instance,
            dir=str(Path.cwd()),
            filter="""Python file (*.py);;
            HTML file (*.html);;
            File (*.*)"""
        )[0]
        if file_path is not None and file_path != "":
            if file_is_open_manager_dict.get(str(Path(file_path)), None) is not None:
                widget.tab_manager.setCurrentWidget(
                    widget.tab_manager.findChild(EditorWidget, str(Path(file_path).name)))
                return
            else:
                file_is_open_manager_dict.update({file_path: str(Path(file_path).name)})
            widget.current_file = file_path
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(
                file_content
            )
            if widget.current_file is not None and widget.code_save_thread is None:
                init_new_auto_save_thread(widget.current_file, widget)
            else:
                widget.code_save_thread.file = widget.current_file
            user_setting_dict.update({"last_file": str(widget.current_file)})
            widget.rename_self_tab()


def choose_dir_get_dir_path(parent_qt_instance: EditorMain) -> None:
    jeditor_logger.info("open_file_dialog.py choose_dir_get_dir_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    dir_path = QFileDialog().getExistingDirectory(parent=parent_qt_instance, )
    if dir_path != "":
        check_path = Path(dir_path)
    else:
        return
    if check_path.exists() and check_path.is_dir():
        parent_qt_instance.working_dir = dir_path
        os.chdir(dir_path)
        for code_editor in range(parent_qt_instance.tab_widget.count()):
            widget = parent_qt_instance.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                widget.project_treeview.setRootIndex(widget.project_treeview_model.index(dir_path))
                widget.code_edit.check_env()
        if sys.platform in ["win32", "cygwin", "msys"]:
            venv_path = Path(os.getcwd() + "/venv/Scripts")
        else:
            venv_path = Path(os.getcwd() + "/venv/bin")
        parent_qt_instance.python_compiler = check_and_choose_venv(venv_path)
        read_user_setting()
        parent_qt_instance.startup_setting()
        language_wrapper.reset_language(user_setting_dict.get("language", "English"))
