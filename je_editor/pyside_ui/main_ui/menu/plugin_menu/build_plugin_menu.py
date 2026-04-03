# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入 Qt 動作與訊息框
# Import QAction and QMessageBox from PySide6
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

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


def set_plugin_menu(ui_we_want_to_set: EditorMain) -> None:
    """
    建立插件選單，顯示所有已載入插件的名稱、版本、作者。
    Build Plugin menu showing all loaded plugins with name, version, author.
    同一語言若支援多種副檔名，以子選單呈現。
    If a language plugin supports multiple suffixes, show them in a submenu.
    """
    jeditor_logger.info(f"build_plugin_menu.py set_plugin_menu ui_we_want_to_set: {ui_we_want_to_set}")

    from je_editor.plugins import get_all_plugin_metadata

    # 建立 Plugin 選單
    # Create Plugin menu
    ui_we_want_to_set.plugin_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("plugin_menu_label", "Plugins")
    )

    # 插件瀏覽器入口 / Plugin browser entry
    browse_action = QAction(
        language_wrapper.language_word_dict.get("plugin_browser_tab_name", "Plugin Browser"),
        ui_we_want_to_set.plugin_menu,
    )
    browse_action.triggered.connect(lambda: _open_plugin_browser(ui_we_want_to_set))
    ui_we_want_to_set.plugin_menu.addAction(browse_action)
    ui_we_want_to_set.plugin_menu.addSeparator()

    metadata_list = get_all_plugin_metadata()

    for meta in metadata_list:
        plugin_name = meta.get("name", "Unknown")
        plugin_author = meta.get("author", "")
        plugin_version = meta.get("version", "")
        run_config = meta.get("run_config")

        if run_config is not None:
            suffixes = run_config.get("suffixes", ())
            config_name = run_config.get("name", plugin_name)

            if len(suffixes) > 1:
                # 多種副檔名：建立子選單
                # Multiple suffixes: create a submenu
                sub_menu = ui_we_want_to_set.plugin_menu.addMenu(config_name)

                # 「關於」動作
                # "About" action
                about_action = QAction(
                    language_wrapper.language_word_dict.get("plugin_menu_about", "About"),
                    sub_menu,
                )
                about_action.triggered.connect(
                    _make_about_callback(plugin_name, plugin_version, plugin_author)
                )
                sub_menu.addAction(about_action)
                sub_menu.addSeparator()

                # 每個副檔名一個執行動作
                # One run action per suffix
                for suffix in suffixes:
                    run_action = QAction(
                        language_wrapper.language_word_dict.get(
                            "plugin_menu_run_with", "Run with {name}"
                        ).format(name=f"{config_name} ({suffix})"),
                        sub_menu,
                    )
                    run_action.triggered.connect(
                        _make_run_callback(ui_we_want_to_set, run_config, suffix)
                    )
                    sub_menu.addAction(run_action)
            else:
                # 單一副檔名：直接加入選單
                # Single suffix: add directly to menu
                sub_menu = ui_we_want_to_set.plugin_menu.addMenu(config_name)

                about_action = QAction(
                    language_wrapper.language_word_dict.get("plugin_menu_about", "About"),
                    sub_menu,
                )
                about_action.triggered.connect(
                    _make_about_callback(plugin_name, plugin_version, plugin_author)
                )
                sub_menu.addAction(about_action)
                sub_menu.addSeparator()

                suffix = suffixes[0] if suffixes else ""
                run_action = QAction(
                    language_wrapper.language_word_dict.get(
                        "plugin_menu_run_with", "Run with {name}"
                    ).format(name=config_name),
                    sub_menu,
                )
                run_action.triggered.connect(
                    _make_run_callback(ui_we_want_to_set, run_config, suffix)
                )
                sub_menu.addAction(run_action)
        else:
            # 沒有執行設定的插件（如翻譯插件），只顯示關於
            # Plugins without run config (e.g. translation), show about only
            about_action = QAction(plugin_name, ui_we_want_to_set.plugin_menu)
            about_action.triggered.connect(
                _make_about_callback(plugin_name, plugin_version, plugin_author)
            )
            ui_we_want_to_set.plugin_menu.addAction(about_action)


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


def _make_about_callback(name: str, version: str, author: str):
    """
    建立顯示插件資訊的回呼函式。
    Create a callback to show plugin info dialog.
    """
    def callback():
        message_box = QMessageBox()
        message_box.setWindowTitle(name)
        message_box.setText(
            f"{name}\n"
            f"Version: {version}\n"
            f"Author: {author}"
        )
        message_box.exec()
    return callback


def _make_run_callback(ui_we_want_to_set: EditorMain, run_config: dict, suffix: str):
    """
    建立使用插件執行設定來執行程式的回呼函式。
    Create a callback to run a program using plugin run config.
    """
    def callback():
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
