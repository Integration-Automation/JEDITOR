from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.code.variable_inspector.inspector_gui import VariableInspector
from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI
from je_editor.pyside_ui.main_ui.ipython_widget.ipython_console import IpythonWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_tab_tools_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.tab_menu.tools_menu = ui_we_want_to_set.tab_menu.addMenu(
        language_wrapper.language_word_dict.get("tab_menu_tools_submenu_label")
    )

    # === IPython 分頁 ===
    # === IPython Tab ===
    ui_we_want_to_set.tab_menu.tools_menu.add_ipython_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_ipython_tab_name"))
    ui_we_want_to_set.tab_menu.tools_menu.add_ipython_action.triggered.connect(
        lambda: add_ipython_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.tools_menu.addAction(ui_we_want_to_set.tab_menu.tools_menu.add_ipython_action)

    # === Variable Inspector 分頁 ===
    # === Variable Inspector Tab ===
    ui_we_want_to_set.tab_menu.tools_menu.add_variable_inspector_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_variable_inspector_tab_name"))
    ui_we_want_to_set.tab_menu.tools_menu.add_variable_inspector_ui_action.triggered.connect(
        lambda: add_variable_inspector_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.tools_menu.addAction(
        ui_we_want_to_set.tab_menu.tools_menu.add_variable_inspector_ui_action)

    # === Front Engine 分頁 ===
    # === Front Engine Tab ===
    ui_we_want_to_set.tab_menu.tools_menu.add_frontengine_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_frontengine_label"))
    ui_we_want_to_set.tab_menu.tools_menu.add_frontengine_action.triggered.connect(
        lambda: add_frontengine_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.tools_menu.addAction(ui_we_want_to_set.tab_menu.tools_menu.add_frontengine_action)

    # === Chat UI 分頁 ===
    # === Chat UI Tab ===
    ui_we_want_to_set.tab_menu.tools_menu.add_chat_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_chat_ui_tab_name"))
    ui_we_want_to_set.tab_menu.tools_menu.add_chat_ui_action.triggered.connect(
        lambda: add_chat_ui_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.tools_menu.addAction(ui_we_want_to_set.tab_menu.tools_menu.add_chat_ui_action)


def add_ipython_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 IPython 分頁
    # Log: add an IPython tab
    jeditor_logger.info(f"build_tab_menu.py add ipython tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增 IPython 互動式分頁
    # Add an IPython interactive tab
    ui_we_want_to_set.tab_widget.addTab(
        IpythonWidget(ui_we_want_to_set),  # 建立 IPython 元件 / Create IPython widget
        f"{language_wrapper.language_word_dict.get('tab_menu_ipython_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_variable_inspector_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 Variable Inspector 分頁
    # Log: add a Variable Inspector tab
    jeditor_logger.info(f"build_tab_menu.py add variable inspector tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增變數檢查器分頁
    # Add a variable inspector tab
    ui_we_want_to_set.tab_widget.addTab(
        VariableInspector(),  # 建立變數檢查器元件 / Create Variable Inspector widget
        f"{language_wrapper.language_word_dict.get('tab_menu_variable_inspector_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_frontengine_tab(ui_we_want_to_set: EditorMain) -> None:
    # 新增 FrontEngine 分頁
    # Add FrontEngine tab
    jeditor_logger.info(f"build_tab_menu.py add frontengine tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False),
        f"{language_wrapper.language_word_dict.get('tab_menu_frontengine_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_chat_ui_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 Chat UI 分頁
    # Log: add a Chat UI tab
    jeditor_logger.info(f"build_tab_menu.py add chat_ui tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增聊天分頁
    # Add a chat tab into the main editor
    ui_we_want_to_set.tab_widget.addTab(
        ChatUI(ui_we_want_to_set),  # 建立聊天元件 / Create Chat UI widget
        f"{language_wrapper.language_word_dict.get('tab_menu_chat_ui_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )
