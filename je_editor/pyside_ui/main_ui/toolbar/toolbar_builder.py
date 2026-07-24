from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QToolBar, QComboBox, QStyle, QLabel, QWidget, QMessageBox
)

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def _icon(widget: QWidget, std: QStyle.StandardPixmap) -> QIcon:
    """從 QStyle 取得內建圖示 / Get built-in icon from QStyle"""
    return widget.style().standardIcon(std)


def build_toolbar(main_window: EditorMain) -> None:
    """
    建立主工具列，類似 JetBrains 的快捷按鈕列
    Build main toolbar with quick-action buttons similar to JetBrains
    """
    jeditor_logger.info("toolbar_builder.py build_toolbar")
    lang = language_wrapper.language_word_dict.get

    toolbar = QToolBar(lang("toolbar_title"))
    toolbar.setMovable(False)
    toolbar.setIconSize(toolbar.iconSize())
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
    main_window.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
    main_window.main_toolbar = toolbar

    # ── File actions ──────────────────────────────────────────
    act_new = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileIcon),
                      lang("toolbar_new_file"), main_window)
    act_new.setToolTip(lang("toolbar_new_file"))
    act_new.triggered.connect(lambda: _new_file(main_window))
    toolbar.addAction(act_new)

    act_open = QAction(_icon(main_window, QStyle.StandardPixmap.SP_DirOpenIcon),
                       lang("toolbar_open_file"), main_window)
    act_open.setToolTip(lang("toolbar_open_file"))
    act_open.triggered.connect(lambda: _open_file(main_window))
    toolbar.addAction(act_open)

    act_save = QAction(_icon(main_window, QStyle.StandardPixmap.SP_DialogSaveButton),
                       lang("toolbar_save_file"), main_window)
    act_save.setToolTip(lang("toolbar_save_file"))
    act_save.triggered.connect(lambda: _save_file(main_window))
    toolbar.addAction(act_save)

    toolbar.addSeparator()

    # ── Run / Debug / Stop ────────────────────────────────────
    act_run = QAction(_icon(main_window, QStyle.StandardPixmap.SP_MediaPlay),
                      lang("toolbar_run"), main_window)
    act_run.setToolTip(lang("toolbar_run"))
    act_run.setShortcut("F5")
    act_run.triggered.connect(lambda: _run_program(main_window))
    toolbar.addAction(act_run)

    act_debug = QAction(_icon(main_window, QStyle.StandardPixmap.SP_MediaSeekForward),
                        lang("toolbar_debug"), main_window)
    act_debug.setToolTip(lang("toolbar_debug"))
    act_debug.setShortcut("F9")
    act_debug.triggered.connect(lambda: _run_debugger(main_window))
    toolbar.addAction(act_debug)

    act_stop = QAction(_icon(main_window, QStyle.StandardPixmap.SP_MediaStop),
                       lang("toolbar_stop"), main_window)
    act_stop.setToolTip(lang("toolbar_stop"))
    act_stop.setShortcut("Shift+F5")
    act_stop.triggered.connect(lambda: _stop_program(main_window))
    toolbar.addAction(act_stop)

    toolbar.addSeparator()

    # ── Git branch ────────────────────────────────────────────
    git_label = QLabel(f"  {lang('toolbar_git_branch')} ")
    toolbar.addWidget(git_label)

    branch_combo = QComboBox()
    branch_combo.setMinimumWidth(160)
    branch_combo.setToolTip(lang("toolbar_git_branch"))
    toolbar.addWidget(branch_combo)
    main_window.toolbar_branch_combo = branch_combo

    act_checkout = QAction(_icon(main_window, QStyle.StandardPixmap.SP_BrowserReload),
                           lang("toolbar_git_checkout"), main_window)
    act_checkout.setToolTip(lang("toolbar_git_checkout"))
    act_checkout.triggered.connect(lambda: _git_checkout(main_window))
    toolbar.addAction(act_checkout)

    act_refresh_branches = QAction(
        _icon(main_window, QStyle.StandardPixmap.SP_ArrowDown),
        lang("toolbar_git_refresh"), main_window)
    act_refresh_branches.setToolTip(lang("toolbar_git_refresh"))
    act_refresh_branches.triggered.connect(lambda: _git_refresh_branches(main_window))
    toolbar.addAction(act_refresh_branches)

    toolbar.addSeparator()

    # ── Search ────────────────────────────────────────────────
    act_search = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogContentsView),
                         lang("toolbar_search"), main_window)
    act_search.setToolTip(lang("toolbar_search"))
    act_search.setShortcut("Ctrl+Shift+F")
    act_search.triggered.connect(lambda: _open_search(main_window))
    toolbar.addAction(act_search)

    # ── Command palette ───────────────────────────────────────
    # 使用 Ctrl+Shift+A（JetBrains 的 Find Action）；Ctrl+Shift+P 已被 pip 安裝佔用
    # Uses Ctrl+Shift+A (JetBrains "Find Action"); Ctrl+Shift+P is taken by pip install
    act_palette = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogDetailedView),
                          lang("toolbar_command_palette"), main_window)
    act_palette.setToolTip(lang("toolbar_command_palette"))
    act_palette.setShortcut("Ctrl+Shift+A")
    act_palette.triggered.connect(lambda: _open_command_palette(main_window))
    toolbar.addAction(act_palette)
    main_window.command_palette_action = act_palette

    act_quick_open = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogListView),
                             lang("toolbar_quick_open"), main_window)
    act_quick_open.setToolTip(lang("toolbar_quick_open"))
    act_quick_open.setShortcut("Ctrl+P")
    act_quick_open.triggered.connect(lambda: _open_quick_open(main_window))
    toolbar.addAction(act_quick_open)
    main_window.quick_open_action = act_quick_open

    act_go_to_symbol = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogInfoView),
                               lang("toolbar_go_to_symbol"), main_window)
    act_go_to_symbol.setToolTip(lang("toolbar_go_to_symbol"))
    act_go_to_symbol.setShortcut("Ctrl+Shift+O")
    act_go_to_symbol.triggered.connect(lambda: _open_go_to_symbol(main_window))
    toolbar.addAction(act_go_to_symbol)
    main_window.go_to_symbol_action = act_go_to_symbol

    # 初始載入 git 分支 / Initial git branch load
    _git_refresh_branches(main_window)


# ── Callbacks ─────────────────────────────────────────────────

def _get_editor_widget(main_window: EditorMain) -> EditorWidget | None:
    """取得當前的 EditorWidget / Get current EditorWidget"""
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    widget = main_window.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        return widget
    return None


def _new_file(main_window: EditorMain) -> None:
    """新增檔案 / New file"""
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    editor_widget = EditorWidget(main_window)
    main_window.tab_widget.addTab(
        editor_widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{main_window.tab_widget.count()}"
    )
    main_window.tab_widget.setCurrentWidget(editor_widget)


def _open_file(main_window: EditorMain) -> None:
    """開啟檔案 / Open file"""
    from je_editor.pyside_ui.dialog.file_dialog.open_file_dialog import choose_file_get_open_file_path
    choose_file_get_open_file_path(main_window)


def _save_file(main_window: EditorMain) -> None:
    """儲存檔案 / Save file"""
    from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
    choose_file_get_save_file_path(main_window)


def _run_program(main_window: EditorMain) -> None:
    """執行程式 / Run program"""
    from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_program_menu import run_program
    run_program(main_window)


def _run_debugger(main_window: EditorMain) -> None:
    """執行除錯器 / Run debugger"""
    from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_debug_menu import run_debugger
    run_debugger(main_window)


def _stop_program(main_window: EditorMain) -> None:
    """停止程式 / Stop program"""
    from je_editor.pyside_ui.main_ui.menu.run_menu.build_run_menu import stop_program
    stop_program(main_window)


def _open_search(main_window: EditorMain) -> None:
    """開啟搜尋與取代 / Open search & replace"""
    widget = _get_editor_widget(main_window)
    if widget:
        widget.code_edit.open_search_replace_dialog()


def _open_command_palette(main_window: EditorMain) -> None:
    """開啟指令面板 / Open the command palette"""
    from je_editor.pyside_ui.main_ui.command_palette.command_palette_dialog import (
        open_command_palette
    )
    open_command_palette(main_window)


def _open_quick_open(main_window: EditorMain) -> None:
    """開啟快速開啟檔案面板 / Open the quick open file picker"""
    from je_editor.pyside_ui.main_ui.command_palette.quick_open_dialog import open_quick_open
    open_quick_open(main_window)


def _open_go_to_symbol(main_window: EditorMain) -> None:
    """開啟前往符號面板 / Open the go-to-symbol picker"""
    from je_editor.pyside_ui.main_ui.command_palette.go_to_symbol_dialog import open_go_to_symbol
    open_go_to_symbol(main_window)


class _GitBranchWorker(QObject):
    """背景取得 Git 分支清單 / Fetch git branches in background"""
    finished = Signal(list, str)  # (branch_names, current_branch_or_sha)
    error = Signal(str)

    def run(self) -> None:
        try:
            from git import Repo
            import os
            repo = Repo(os.getcwd(), search_parent_directories=True)
            if repo.bare:
                self.finished.emit([], "")
                return
            heads = [h.name for h in repo.heads]
            try:
                current = repo.active_branch.name
            except TypeError:
                current = repo.head.commit.hexsha[:8]
            self.finished.emit(heads, current)
        except Exception:
            self.finished.emit([], "")


class _GitCheckoutWorker(QObject):
    """背景執行 Git checkout / Run git checkout in background"""
    finished = Signal()
    error = Signal(str)

    def __init__(self, target: str) -> None:
        super().__init__()
        self._target = target

    def run(self) -> None:
        try:
            from git import Repo
            import os
            repo = Repo(os.getcwd(), search_parent_directories=True)
            repo.git.checkout(self._target)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# 保持背景執行緒的引用，避免垃圾回收 / Keep thread references to prevent GC
_bg_threads = []


def _run_in_background(worker: QObject, thread_parent: QObject) -> QThread:
    """通用的背景執行緒啟動器 / Generic background thread runner"""
    global _bg_threads
    thread = QThread(thread_parent)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    if hasattr(worker, 'error'):
        worker.error.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)
    _bg_threads = [t for t in _bg_threads if t.isRunning()]
    _bg_threads.append(thread)
    thread.start()
    return thread


def _git_refresh_branches(main_window: EditorMain) -> None:
    """重新載入 Git 分支清單 (背景執行) / Refresh git branch list in background"""
    combo: QComboBox = main_window.toolbar_branch_combo

    worker = _GitBranchWorker()

    def on_done(heads: list[str], current: str) -> None:
        combo.clear()
        if heads:
            combo.addItems(heads)
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif current:
                combo.setEditable(True)
                combo.setEditText(current)

    worker.finished.connect(on_done)
    _run_in_background(worker, main_window)


def _git_checkout(main_window: EditorMain) -> None:
    """切換 Git 分支 (背景執行) / Checkout git branch in background"""
    combo: QComboBox = main_window.toolbar_branch_combo
    target = combo.currentText().strip()
    if not target:
        return

    worker = _GitCheckoutWorker(target)

    def on_done() -> None:
        _git_refresh_branches(main_window)
        # 同步更新底部面板的 GitGui (如果有的話)
        # Sync bottom panel GitGui if available
        widget = _get_editor_widget(main_window)
        if widget and hasattr(widget, "git_gui") and widget.git_gui.current_repo:
            widget.git_gui._refresh_branch_list()
            widget.git_gui._refresh_change_list()

    def on_error(err: str) -> None:
        QMessageBox.critical(main_window, "Checkout Error", err)

    worker.finished.connect(on_done)
    worker.error.connect(on_error)
    _run_in_background(worker, main_window)
