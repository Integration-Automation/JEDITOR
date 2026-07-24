"""
前往符號：在目前檔案中以模糊搜尋跳到類別、函式或變數
Go to symbol: fuzzy-search the current file and jump to a class, function or variable.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import (
    CommandPaletteDialog
)
from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.symbols.python_symbols import SymbolInfo, extract_python_symbols

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def build_symbol_entries(symbols: list[SymbolInfo], code_edit=None) -> list[CommandEntry]:
    """
    把符號轉成可放進模糊搜尋清單的項目
    Turn symbols into entries the fuzzy picker can rank.

    :param symbols: 萃取出的符號 / The extracted symbols
    :param code_edit: 要跳轉的編輯器元件，``None`` 時項目沒有觸發動作
        / The editor to jump in; ``None`` leaves entries without a trigger
    :return: 對應的項目清單 / The matching entries
    """
    return [
        CommandEntry(
            title=symbol.name,
            path=f"{symbol.kind}  {symbol.qualified_name}  :{symbol.line}",
            shortcut="",
            payload=make_symbol_jumper(code_edit, symbol.line),
        )
        for symbol in symbols
    ]


def make_symbol_jumper(code_edit, line: int):
    """
    建立跳到指定行的觸發函式
    Build a trigger that jumps the editor to a line.

    閉包只捕捉編輯器與行號，不捕捉對話框；對話框設定了 ``WA_DeleteOnClose``，
    觸發時它已經被銷毀。
    The closure captures only the editor and line, never the dialog: it sets
    ``WA_DeleteOnClose`` and is already gone when the trigger fires.

    :param code_edit: 要跳轉的編輯器元件 / The editor widget to move
    :param line: 1 起算的行號 / The 1-based line number
    :return: 可直接呼叫的觸發函式 / A callable trigger
    """

    def jump() -> None:
        if code_edit is not None and hasattr(code_edit, "jump_to_line"):
            code_edit.jump_to_line(line)

    return jump


def current_code_edit(main_window: EditorMain):
    """
    取得目前分頁的程式碼編輯器
    Return the code editor of the current tab.

    :param main_window: 主編輯器視窗 / The main editor window
    :return: 程式碼編輯器，目前分頁不是編輯器時回傳 ``None``
        / The code editor, or ``None`` when the current tab is not an editor
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    widget = main_window.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        return widget.code_edit
    return None


def open_go_to_symbol(main_window: EditorMain) -> CommandPaletteDialog | None:
    """
    建立並顯示前往符號面板
    Build and show the go-to-symbol picker.

    目前分頁不是程式碼編輯器，或檔案沒有可用符號時不會開啟面板。
    The picker stays closed when the current tab is not a code editor or when the
    file yields no symbols.

    :param main_window: 主編輯器視窗 / The main editor window
    :return: 已顯示的對話框，沒有符號時回傳 ``None``
        / The shown dialog, or ``None`` when there is nothing to show
    """
    code_edit = current_code_edit(main_window)
    if code_edit is None:
        return None
    symbols = extract_python_symbols(code_edit.toPlainText())
    jeditor_logger.info(f"go_to_symbol_dialog.py found {len(symbols)} symbols")
    if not symbols:
        return None
    word = language_wrapper.language_word_dict
    dialog = CommandPaletteDialog(
        main_window,
        build_symbol_entries(symbols, code_edit),
        title=word.get("go_to_symbol_title"),
        placeholder=word.get("go_to_symbol_placeholder"),
    )
    dialog.show()
    return dialog
