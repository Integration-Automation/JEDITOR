# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING, Callable

# 匯入 Qt 動作與訊息框
# Import QAction and QMessageBox from PySide6
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox, QMenu

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger
# 匯入多語言包裝器
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


_PLUGIN_MENU_ABOUT = "plugin_menu_about"
_PLUGIN_MENU_RUN_WITH = "plugin_menu_run_with"


def _add_about_action(menu: QMenu, plugin_name: str, plugin_version: str,
                      plugin_author: str) -> None:
    """在選單加上「關於」項目 / Append an About action to the given menu."""
    about_action = QAction(
        language_wrapper.language_word_dict.get(_PLUGIN_MENU_ABOUT, "About"), menu)
    about_action.triggered.connect(
        _make_about_callback(plugin_name, plugin_version, plugin_author))
    menu.addAction(about_action)


def _add_run_action(menu: QMenu, ui_we_want_to_set: EditorMain, run_config: dict,
                    action_text: str) -> None:
    """在選單加上「執行」項目 / Append a Run action to the given menu."""
    run_action = QAction(
        language_wrapper.language_word_dict.get(_PLUGIN_MENU_RUN_WITH, "Run with {name}").format(
            name=action_text), menu)
    run_action.triggered.connect(_make_run_callback(ui_we_want_to_set, run_config))
    menu.addAction(run_action)


def _build_run_submenu(ui_we_want_to_set: EditorMain, meta: dict, run_config: dict) -> None:
    """為單一有 run_config 的插件建立子選單 / Build submenu for a plugin with run_config."""
    plugin_name = meta.get("name", "Unknown")
    plugin_author = meta.get("author", "")
    plugin_version = meta.get("version", "")
    suffixes = run_config.get("suffixes", ())
    config_name = run_config.get("name", plugin_name)

    sub_menu = ui_we_want_to_set.plugin_menu.addMenu(config_name)
    _add_about_action(sub_menu, plugin_name, plugin_version, plugin_author)
    sub_menu.addSeparator()
    if len(suffixes) > 1:
        for suffix in suffixes:
            _add_run_action(sub_menu, ui_we_want_to_set, run_config, f"{config_name} ({suffix})")
    else:
        _add_run_action(sub_menu, ui_we_want_to_set, run_config, config_name)


def _build_about_only_entry(ui_we_want_to_set: EditorMain, meta: dict) -> None:
    """無執行設定的插件只顯示 About / Plugins without run_config show About only."""
    plugin_name = meta.get("name", "Unknown")
    plugin_author = meta.get("author", "")
    plugin_version = meta.get("version", "")
    about_action = QAction(plugin_name, ui_we_want_to_set.plugin_menu)
    about_action.triggered.connect(
        _make_about_callback(plugin_name, plugin_version, plugin_author))
    ui_we_want_to_set.plugin_menu.addAction(about_action)


def set_plugin_menu(ui_we_want_to_set: EditorMain) -> None:
    """建立插件選單 / Build the Plugin menu."""
    jeditor_logger.info(f"build_plugin_menu.py set_plugin_menu ui_we_want_to_set: {ui_we_want_to_set}")
    from je_editor.plugins import get_all_plugin_metadata

    ui_we_want_to_set.plugin_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("plugin_menu_label", "Plugins"))

    browse_action = QAction(
        language_wrapper.language_word_dict.get("plugin_browser_tab_name", "Plugin Browser"),
        ui_we_want_to_set.plugin_menu)
    browse_action.triggered.connect(lambda: _open_plugin_browser(ui_we_want_to_set))
    ui_we_want_to_set.plugin_menu.addAction(browse_action)
    ui_we_want_to_set.plugin_menu.addSeparator()

    for meta in get_all_plugin_metadata():
        run_config = meta.get("run_config")
        if run_config is not None:
            _build_run_submenu(ui_we_want_to_set, meta, run_config)
        else:
            _build_about_only_entry(ui_we_want_to_set, meta)


def _open_plugin_browser(ui_we_want_to_set: EditorMain) -> None:
    """
    開啟插件瀏覽器分頁。
    Open plugin browser tab.
    """
    from je_editor.pyside_ui.main_ui.plugin_browser.plugin_browser_widget import PluginBrowserWidget

    tab_name = language_wrapper.language_word_dict.get("plugin_browser_tab_name", "Plugin Browser")
    ui_we_want_to_set.tab_widget.addTab(
        PluginBrowserWidget(),
        f"{tab_name} {ui_we_want_to_set.tab_widget.count()}"
    )


def _make_about_callback(name: str, version: str, author: str) -> Callable[[], None]:
    """
    建立顯示插件資訊的回呼函式。
    Create a callback to show plugin info dialog.
    """
    def callback() -> None:
        message_box = QMessageBox()
        message_box.setWindowTitle(name)
        message_box.setText(
            f"{name}\n"
            f"Version: {version}\n"
            f"Author: {author}"
        )
        message_box.exec()
    return callback


def _make_run_callback(ui_we_want_to_set: EditorMain, run_config: dict) -> Callable[[], None]:
    """
    建立使用插件執行設定來執行程式的回呼函式。
    Create a callback to run a program using plugin run config.
    """
    def callback() -> None:
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
        from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
        from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import \
            please_close_current_running_messagebox

        widget = ui_we_want_to_set.tab_widget.currentWidget()
        if not isinstance(widget, EditorWidget):
            return

        if widget.exec_program is not None:
            please_close_current_running_messagebox(ui_we_want_to_set)
            return

        if not choose_file_get_save_file_path(ui_we_want_to_set):
            return

        code_exec = ExecManager(widget, program_encoding=ui_we_want_to_set.encoding)
        code_exec.later_init()
        code_exec.exec_with_plugin_config(widget.current_file, run_config)
        widget.exec_program = code_exec

    return callback
