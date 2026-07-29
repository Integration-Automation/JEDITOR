from __future__ import annotations

import os
import subprocess  # nosec B404 - 呼叫 git 子命令皆以引數清單送入，未使用 shell
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QToolBar, QComboBox, QStyle, QLabel, QWidget, QMessageBox
)

from je_editor.pyside_ui.main_ui.save_settings.shortcut_setting import bind
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


# 分支標籤的名字，換語言時用它找回那個標籤
# The branch label's name, which a language change uses to find it again
GIT_BRANCH_LABEL_NAME = "toolbar_git_branch_label"


def _icon(widget: QWidget, std: QStyle.StandardPixmap) -> QIcon:
    """從 QStyle 取得內建圖示 / Get built-in icon from QStyle"""
    return widget.style().standardIcon(std)


def git_branch_label_text() -> str:
    """
    分支標籤上的文字，含左右間距
    The branch label's text, spacing and all.

    :return: 標籤文字 / the label's text
    """
    return f"  {language_wrapper.language_word_dict.get('toolbar_git_branch')} "


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
    bind(act_run, "run_program")
    act_run.triggered.connect(lambda: _run_program(main_window))
    toolbar.addAction(act_run)

    act_debug = QAction(_icon(main_window, QStyle.StandardPixmap.SP_MediaSeekForward),
                        lang("toolbar_debug"), main_window)
    act_debug.setToolTip(lang("toolbar_debug"))
    bind(act_debug, "run_debugger")
    act_debug.triggered.connect(lambda: _run_debugger(main_window))
    toolbar.addAction(act_debug)

    act_stop = QAction(_icon(main_window, QStyle.StandardPixmap.SP_MediaStop),
                       lang("toolbar_stop"), main_window)
    act_stop.setToolTip(lang("toolbar_stop"))
    bind(act_stop, "stop_program")
    act_stop.triggered.connect(lambda: _stop_program(main_window))
    toolbar.addAction(act_stop)

    toolbar.addSeparator()

    # ── Git branch ────────────────────────────────────────────
    git_label = QLabel(git_branch_label_text())
    # 換語言時要找回這個標籤：它的文字帶著間距，不是字典裡的原字
    # Naming it lets a language change find it again: its text carries spacing
    # and so is not the dictionary's own string
    git_label.setObjectName(GIT_BRANCH_LABEL_NAME)
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
    bind(act_search, "search_in_files")
    act_search.triggered.connect(lambda: _open_search(main_window))
    toolbar.addAction(act_search)

    # ── Command palette ───────────────────────────────────────
    # 使用 Ctrl+Shift+A（JetBrains 的 Find Action）；Ctrl+Shift+P 已被 pip 安裝佔用
    # Uses Ctrl+Shift+A (JetBrains "Find Action"); Ctrl+Shift+P is taken by pip install
    act_palette = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogDetailedView),
                          lang("toolbar_command_palette"), main_window)
    act_palette.setToolTip(lang("toolbar_command_palette"))
    bind(act_palette, "command_palette")
    act_palette.triggered.connect(lambda: _open_command_palette(main_window))
    toolbar.addAction(act_palette)
    main_window.command_palette_action = act_palette

    act_quick_open = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogListView),
                             lang("toolbar_quick_open"), main_window)
    act_quick_open.setToolTip(lang("toolbar_quick_open"))
    bind(act_quick_open, "quick_open")
    act_quick_open.triggered.connect(lambda: _open_quick_open(main_window))
    toolbar.addAction(act_quick_open)
    main_window.quick_open_action = act_quick_open

    act_go_to_symbol = QAction(_icon(main_window, QStyle.StandardPixmap.SP_FileDialogInfoView),
                               lang("toolbar_go_to_symbol"), main_window)
    act_go_to_symbol.setToolTip(lang("toolbar_go_to_symbol"))
    bind(act_go_to_symbol, "go_to_symbol")
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


# git 子命令的等待上限（秒）；掛在無回應的網路磁碟上時不要跟著卡住
# Seconds to wait for a git subcommand, so an unresponsive network share does
# not take the thread with it
_GIT_TIMEOUT_SECONDS = 20


def _git_output(*arguments: str) -> str:
    """
    在工作目錄執行一個 git 子命令並取得輸出
    Run one git subcommand in the working directory and return its output.

    這裡直接叫 git，而不是用 GitPython。``Repo`` 會帶起常駐的 ``git cat-file`` 子程
    序與執行緒區域狀態，在背景執行緒裡反覆開關並不安穩；工具列只要兩行文字，一次
    問完就結束的子程序剛好夠用，也是 ``git_cli.py`` 的做法。
    This calls git directly rather than going through GitPython. A ``Repo``
    brings up long-lived ``git cat-file`` children and thread-local state, and
    opening and closing that repeatedly from a background thread is not steady.
    The toolbar needs two pieces of text, so a subprocess that answers once and
    exits is enough -- and it is what ``git_cli.py`` already does.

    :param arguments: git 的引數 / the arguments to give git
    :return: git 的標準輸出 / what git wrote to stdout
    :raises RuntimeError: git 回傳非零時 / when git exits non-zero
    """
    # 固定可執行檔 "git" 加引數清單，沒有經過 shell
    # A fixed "git" binary plus an argument list; no shell involved
    result = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
        ["git", *arguments],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(arguments)} failed")
    return result.stdout


class _GitBranchScan(QThread):
    """
    背景取得 Git 分支清單
    Fetch the git branch list in the background.

    這裡是 ``QThread`` 的子類，而不是搬到執行緒上的 worker。編輯器其他地方的背景工
    作都是這樣寫的，而且執行的物件就是執行緒本身——不會有「worker 被回收了但執行緒
    還在」或是從別的執行緒銷毀它的問題。
    A ``QThread`` subclass rather than a worker moved onto a thread. Every other
    background job in the editor is written this way, and the object doing the
    work is the thread itself -- so there is no worker to be collected out from
    under a running thread, or destroyed from the wrong one.
    """

    # 名字不能叫 finished：那是 QThread 自己的訊號
    # Not named finished: QThread has a signal by that name of its own
    scanned = Signal(list, str)  # (branch_names, current_branch_or_sha)

    def __init__(self) -> None:
        super().__init__()
        # 具名執行緒：萬一它在執行中被銷毀，Qt 的中止訊息才說得出是哪一條
        # A named thread, so Qt's abort message says which one if it is ever
        # destroyed while still running
        self.setObjectName("ToolbarGitBranchScan")

    def run(self) -> None:
        try:
            heads = [
                line.strip() for line in
                _git_output("branch", "--format=%(refname:short)").splitlines()
                if line.strip()
            ]
            # detached HEAD 時 --abbrev-ref 回的是字面上的 "HEAD"，這時改顯示 sha
            # On a detached HEAD --abbrev-ref answers the literal "HEAD", so the
            # short sha is shown instead
            current = _git_output("rev-parse", "--abbrev-ref", "HEAD").strip()
            if current == "HEAD":
                current = _git_output("rev-parse", "--short=8", "HEAD").strip()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            # 沒有 repo、壞掉的 repo、讀不到的磁碟都會走到這裡。分支欄空著就好，不
            # 需要打斷使用者，但完全不留紀錄的話就查不出來了。
            # No repository, a broken one, an unreadable drive: all land here. An
            # empty branch box is a fine outcome and not worth interrupting anyone
            # over, but leaving no trace at all makes it impossible to look into.
            jeditor_logger.warning(f"Toolbar git branch scan failed: {error}")
            self.scanned.emit([], "")
            return
        self.scanned.emit(heads, current)


class _GitCheckout(QThread):
    """背景執行 Git checkout / Run git checkout in the background"""

    checked_out = Signal()
    failed = Signal(str)

    def __init__(self, target: str) -> None:
        super().__init__()
        self.setObjectName("ToolbarGitCheckout")
        self._target = target

    def run(self) -> None:
        try:
            _git_output("checkout", self._target)
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            self.failed.emit(str(error))
            return
        self.checked_out.emit()


# 保持背景執行緒的引用，避免垃圾回收 / Keep thread references to prevent GC
_bg_threads: list[QThread] = []


def _run_in_background(thread: QThread) -> QThread:
    """
    記住一條背景執行緒並啟動它
    Remember a background thread and start it.

    引用一定要留著。沒有人抓著的話，Python 會在它還在跑的時候就回收掉，而銷毀一條
    still-running 的 QThread 會讓 Qt 直接中止整個程序。
    The reference has to be kept. With nobody holding it, Python collects it
    while it is still running, and destroying a running QThread makes Qt abort
    the process outright.

    :param thread: 還沒啟動的執行緒 / the thread, not yet started
    :return: 同一條執行緒 / that same thread
    """
    global _bg_threads
    _bg_threads = [running for running in _bg_threads if running.isRunning()]
    _bg_threads.append(thread)
    thread.start()
    return thread


def stop_background_threads() -> int:
    """
    等所有工具列的背景執行緒結束
    Wait for every toolbar background thread to finish.

    還在跑的時候被銷毀，Qt 會直接讓程序中止（``QThread: Destroyed while thread is
    still running``）。git 分支掃描在大的或放在網路磁碟上的儲存庫要跑上一段時間，
    關閉時剛好還沒跑完並不罕見。
    Destroyed while still running, they make Qt abort the process outright
    (``QThread: Destroyed while thread is still running``). Scanning git branches
    takes a while on a large repository or one on a network share, so still
    running at closing time is not unusual.

    :return: 等了幾條執行緒 / how many threads were waited for
    """
    global _bg_threads
    threads, _bg_threads = _bg_threads, []
    waited = 0
    for thread in threads:
        try:
            if thread.isRunning():
                thread.quit()
                thread.wait()
                waited += 1
        except RuntimeError:
            # 它已經跑完並被刪除了 / It already finished and was deleted
            continue
    return waited


def _a_branch_scan_is_running() -> bool:
    """是否已經有一次分支掃描在跑 / Whether a branch scan is already going."""
    return any(
        isinstance(thread, _GitBranchScan) and thread.isRunning()
        for thread in _bg_threads
    )


def _git_refresh_branches(main_window: EditorMain) -> None:
    """
    重新載入 Git 分支清單 (背景執行)
    Refresh the git branch list in the background.

    已經有一次在跑就跳過。這個函式在建立工具列時、切換分支之後、以及每次換語言
    重建工具列時都會被呼叫，不擋的話一個大的儲存庫上會疊出好幾條同時掃描的執行緒，
    而它們要的答案是一樣的。
    A scan already going means this one is skipped. This runs when the toolbar is
    built, after a checkout, and every time a language change rebuilds the
    toolbar; unchecked, a large repository ends up with several scans at once, all
    after the same answer.
    """
    if _a_branch_scan_is_running():
        return
    combo: QComboBox = main_window.toolbar_branch_combo

    scan = _GitBranchScan()

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

    scan.scanned.connect(on_done)
    _run_in_background(scan)


def _git_checkout(main_window: EditorMain) -> None:
    """切換 Git 分支 (背景執行) / Checkout git branch in background"""
    combo: QComboBox = main_window.toolbar_branch_combo
    target = combo.currentText().strip()
    if not target:
        return

    checkout = _GitCheckout(target)

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

    checkout.checked_out.connect(on_done)
    checkout.failed.connect(on_error)
    _run_in_background(checkout)
