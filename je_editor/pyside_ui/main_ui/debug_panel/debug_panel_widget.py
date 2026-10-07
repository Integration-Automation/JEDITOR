"""
除錯面板：控制按鈕、執行緒、呼叫堆疊、變數、求值與輸出
The debug panel: controls, threads, the call stack, variables, evaluation and output.

面板只跟 ``DebugController`` 說話。它要什麼就向控制器要，答案從控制器的訊號回來，
所以這裡沒有任何一行知道轉接器或協定。
The panel talks to the ``DebugController`` only. Whatever it needs it asks the
controller for, and the answers come back through the controller's signals, so
nothing here knows about adapters or the protocol.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.core.debug.debug_session import (
    DebugReply, DebugState, ExceptionInfo, Scope, StackFrame, StepKind, StopEvent, Variable
)
from je_editor.core.uri.resource_uri import to_path
from je_editor.pyside_ui.main_ui.debug_panel.debug_controller import DebugController
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

COLUMN_NAME = 0
COLUMN_VALUE = 1
COLUMN_TYPE = 2
# 樹狀項目上記著「展開時要用哪個編號去查子項目」/ Where a tree item keeps the handle for fetching its children
REFERENCE_ROLE = Qt.ItemDataRole.UserRole
# 列表項目上記著那一層堆疊 / Where a list item keeps its stack frame
FRAME_ROLE = Qt.ItemDataRole.UserRole
EXCEPTION_REASON = "exception"
# 輸出最多留這麼多行，長時間除錯才不會把記憶體吃光
# The most lines of output kept, so a long session does not eat the memory
MAX_OUTPUT_LINES = 5000
_STATE_KEYS = {
    DebugState.IDLE: "debug_panel_state_idle",
    DebugState.STARTING: "debug_panel_state_starting",
    DebugState.RUNNING: "debug_panel_state_running",
    DebugState.PAUSED: "debug_panel_state_paused",
    DebugState.TERMINATED: "debug_panel_state_terminated",
}


def _word(key: str) -> str:
    """取得目前語言的介面文字 / The UI text in the current language."""
    return language_wrapper.language_word_dict.get(key, key)


class DebugPanelWidget(QWidget):
    """
    顯示並控制一次除錯的面板
    The panel that shows and controls a debug run.
    """

    # 使用者選了一層堆疊：檔案路徑與行號（1 起算）；沒有原始碼時路徑是空字串
    # A frame was chosen: its file path and 1-based line; the path is empty when it has no source
    frame_selected = Signal(str, int)

    def __init__(self, controller: DebugController, parent: QWidget | None = None) -> None:
        """
        :param controller: 這個視窗的除錯控制 / the window's debugging control
        :param parent: Qt 父元件 / the Qt parent
        """
        super().__init__(parent)
        self._controller = controller
        self._thread_id = 0
        self._stop_reason = ""
        self._build_controls()
        self._build_views()
        self._connect()
        self.retranslate()
        self._show_state(controller.state())

    def _build_controls(self) -> None:
        """建立上方的控制按鈕與狀態 / Build the control buttons and the status line."""
        self.continue_button = QPushButton()
        self.pause_button = QPushButton()
        self.step_over_button = QPushButton()
        self.step_into_button = QPushButton()
        self.step_out_button = QPushButton()
        self.stop_button = QPushButton()
        self.status_label = QLabel()
        self._controls = QHBoxLayout()
        for button in (self.continue_button, self.pause_button, self.step_over_button,
                       self.step_into_button, self.step_out_button, self.stop_button):
            self._controls.addWidget(button)
        self._controls.addWidget(self.status_label, 1)

    def _build_views(self) -> None:
        """建立堆疊、變數、輸出與求值 / Build the stack, the variables, the output and the evaluator."""
        self.thread_label = QLabel()
        self.thread_combobox = QComboBox()
        self.stack_label = QLabel()
        self.stack_list = QListWidget()
        stack_side = QWidget()
        stack_layout = QVBoxLayout(stack_side)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        for widget in (self.thread_label, self.thread_combobox, self.stack_label, self.stack_list):
            stack_layout.addWidget(widget)
        self.variable_tree = QTreeWidget()
        self.variable_tree.setColumnCount(COLUMN_TYPE + 1)
        # 名稱那一欄跟著內容變寬，長一點的變數名稱才不會被截掉
        # The name column grows with its content, so a longer variable name is not cut off
        self.variable_tree.header().setSectionResizeMode(
            COLUMN_NAME, QHeaderView.ResizeMode.ResizeToContents)
        self.output_view = QPlainTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setMaximumBlockCount(MAX_OUTPUT_LINES)
        self.evaluate_input = QLineEdit()
        upper = QSplitter(Qt.Orientation.Horizontal)
        upper.addWidget(stack_side)
        upper.addWidget(self.variable_tree)
        lower = QWidget()
        lower_layout = QVBoxLayout(lower)
        lower_layout.setContentsMargins(0, 0, 0, 0)
        lower_layout.addWidget(self.output_view)
        lower_layout.addWidget(self.evaluate_input)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(upper)
        splitter.addWidget(lower)
        layout = QVBoxLayout(self)
        layout.addLayout(self._controls)
        layout.addWidget(splitter)

    def _connect(self) -> None:
        """把按鈕接到控制器、把控制器的訊號接到畫面 / Wire the buttons to the controller and its signals to the views."""
        controller = self._controller
        self.continue_button.clicked.connect(controller.resume)
        self.pause_button.clicked.connect(controller.pause)
        self.step_over_button.clicked.connect(lambda: controller.step(StepKind.OVER))
        self.step_into_button.clicked.connect(lambda: controller.step(StepKind.INTO))
        self.step_out_button.clicked.connect(lambda: controller.step(StepKind.OUT))
        self.stop_button.clicked.connect(controller.stop)
        self.thread_combobox.activated.connect(self._on_thread_chosen)
        self.stack_list.currentItemChanged.connect(self._on_frame_chosen)
        self.variable_tree.itemExpanded.connect(self._on_item_expanded)
        self.evaluate_input.returnPressed.connect(self._evaluate)
        controller.state_changed.connect(self._show_state)
        controller.stopped.connect(self._on_stopped)
        controller.output.connect(self._on_output)
        controller.threads_ready.connect(self._show_threads)
        controller.stack_ready.connect(self._show_stack)
        controller.scopes_ready.connect(self._show_scopes)
        controller.variables_ready.connect(self._show_variables)
        controller.evaluated.connect(self._show_evaluation)
        controller.exception_ready.connect(self._show_exception)

    def retranslate(self) -> None:
        """換語言之後重設每一段文字 / Reset every piece of text after a language change."""
        self.continue_button.setText(_word("debug_panel_continue"))
        self.pause_button.setText(_word("debug_panel_pause"))
        self.step_over_button.setText(_word("debug_panel_step_over"))
        self.step_into_button.setText(_word("debug_panel_step_into"))
        self.step_out_button.setText(_word("debug_panel_step_out"))
        self.stop_button.setText(_word("debug_panel_stop"))
        self.thread_label.setText(_word("debug_panel_threads"))
        self.stack_label.setText(_word("debug_panel_call_stack"))
        self.variable_tree.setHeaderLabels([
            _word("debug_panel_col_name"), _word("debug_panel_col_value"),
            _word("debug_panel_col_type")])
        self.evaluate_input.setPlaceholderText(_word("debug_panel_evaluate_placeholder"))
        self._show_state(self._controller.state())

    def selected_frame(self) -> StackFrame | None:
        """
        目前選的那一層堆疊
        The stack frame that is selected.

        :return: 那一層堆疊，沒有選時為 ``None`` / the frame, or ``None`` when none is selected
        """
        item = self.stack_list.currentItem()
        return None if item is None else item.data(FRAME_ROLE)

    def _show_state(self, state: DebugState) -> None:
        """依狀態更新按鈕與狀態文字 / Update the buttons and the status text for a state."""
        paused = state is DebugState.PAUSED
        running = state is DebugState.RUNNING
        active = paused or running or state is DebugState.STARTING
        self.continue_button.setEnabled(paused)
        self.pause_button.setEnabled(running)
        for button in (self.step_over_button, self.step_into_button, self.step_out_button):
            button.setEnabled(paused)
        self.stop_button.setEnabled(active)
        self.evaluate_input.setEnabled(paused)
        text = _word(_STATE_KEYS[state])
        self.status_label.setText(text.format(reason=self._stop_reason) if paused else text)
        if not paused:
            self._clear_stack()
            self.variable_tree.clear()

    def _clear_stack(self) -> None:
        """
        清空堆疊清單，而不把途中的項目當成使用者選的
        Empty the stack list without taking an item passed on the way for the user's choice.

        清空時 Qt 會先把「目前項目」移到下一個再刪，每移一次都送出訊號；不擋住的話，
        程式明明在跑，面板卻去查那一層的變數、還請編輯器標出它的行。
        While clearing, Qt moves the current item to the next one before deleting,
        and signals each move. Left unblocked, the panel would ask for that
        frame's variables and have its line marked while the program is running.
        """
        was_blocked = self.stack_list.blockSignals(True)
        self.stack_list.clear()
        self.stack_list.blockSignals(was_blocked)

    def _on_stopped(self, stop: StopEvent) -> None:
        """程式停下來了：記下原因，開始查執行緒與堆疊 / The program stopped: note why, then ask for threads and the stack."""
        self._thread_id = stop.thread_id
        self._stop_reason = stop.description or stop.reason
        self._show_state(DebugState.PAUSED)
        self._controller.request_threads()
        self._controller.request_stack(stop.thread_id)
        if stop.reason == EXCEPTION_REASON:
            self._controller.request_exception(stop.thread_id)

    def _on_output(self, _category: str, text: str) -> None:
        """把輸出接在最後面 / Append output at the end."""
        self.output_view.moveCursor(self.output_view.textCursor().MoveOperation.End)
        self.output_view.insertPlainText(text)

    def _show_threads(self, threads: tuple) -> None:
        """列出執行緒，選中停下來的那一條 / List the threads and select the one that stopped."""
        self.thread_combobox.clear()
        for thread in threads:
            self.thread_combobox.addItem(thread.name or str(thread.thread_id), thread.thread_id)
        index = self.thread_combobox.findData(self._thread_id)
        if index >= 0:
            self.thread_combobox.setCurrentIndex(index)

    def _on_thread_chosen(self, index: int) -> None:
        """使用者換了一條執行緒：查它的堆疊 / Another thread was chosen: ask for its stack."""
        thread_id = self.thread_combobox.itemData(index)
        if isinstance(thread_id, int):
            self._thread_id = thread_id
            self._controller.request_stack(thread_id)

    def _show_stack(self, thread_id: int, frames: tuple) -> None:
        """列出堆疊並選中最裡面的一層 / List the stack and select the innermost frame."""
        if thread_id != self._thread_id:
            return
        self._clear_stack()
        for frame in frames:
            path = to_path(frame.uri) if frame.uri else ""
            label = f"{frame.name}  {path.replace(chr(92), '/').rsplit('/', 1)[-1]}:{frame.line}"
            item = QListWidgetItem(label if path else frame.name)
            item.setData(FRAME_ROLE, frame)
            item.setToolTip(path)
            self.stack_list.addItem(item)
        if frames:
            self.stack_list.setCurrentRow(0)

    def _on_frame_chosen(self, current: QListWidgetItem | None, _previous: object) -> None:
        """選了一層堆疊：查它的變數，並請視窗顯示那一行 / A frame was chosen: ask for its variables and have its line shown."""
        self.variable_tree.clear()
        if current is None:
            return
        frame = current.data(FRAME_ROLE)
        self._controller.request_scopes(frame.frame_id)
        self.frame_selected.emit(to_path(frame.uri) if frame.uri else "", frame.line)

    def _show_scopes(self, frame_id: int, scopes: tuple[Scope, ...]) -> None:
        """列出變數群組；不花時間的群組直接展開 / List the scopes, expanding those that are cheap to fetch."""
        frame = self.selected_frame()
        if frame is None or frame.frame_id != frame_id:
            return
        self.variable_tree.clear()
        for scope in scopes:
            item = QTreeWidgetItem(self.variable_tree, [scope.name, "", ""])
            self._make_expandable(item, scope.variables_reference)
            if not scope.expensive:
                item.setExpanded(True)

    @staticmethod
    def _make_expandable(item: QTreeWidgetItem, reference: int) -> None:
        """有子項目的項目先放一個佔位，展開時才去查 / An item with children gets a placeholder, fetched on expanding."""
        item.setData(COLUMN_NAME, REFERENCE_ROLE, reference)
        if reference:
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """展開一個還沒查過的項目：去查它的子項目 / An item not fetched yet was expanded: ask for its children."""
        reference = item.data(COLUMN_NAME, REFERENCE_ROLE)
        if isinstance(reference, int) and reference and item.childCount() == 0:
            self._controller.request_variables(reference)

    def _show_variables(self, reference: int, variables: tuple[Variable, ...]) -> None:
        """把查到的變數放到等著它們的那個項目底下 / Put the variables under the item that waits for them."""
        for parent in self._items_waiting_for(reference):
            for variable in variables:
                child = QTreeWidgetItem(parent, [variable.name, variable.value, variable.type_name])
                self._make_expandable(child, variable.children_reference)

    def _items_waiting_for(self, reference: int) -> list[QTreeWidgetItem]:
        """找出記著某個編號、還沒有子項目的項目 / The items holding a handle that have no children yet."""
        waiting = []
        pending = [self.variable_tree.topLevelItem(index)
                   for index in range(self.variable_tree.topLevelItemCount())]
        while pending:
            item = pending.pop()
            if item.data(COLUMN_NAME, REFERENCE_ROLE) == reference and item.childCount() == 0:
                waiting.append(item)
            pending.extend(item.child(index) for index in range(item.childCount()))
        return waiting

    def _evaluate(self) -> None:
        """在選中的那一層堆疊裡求值 / Evaluate in the selected frame."""
        expression = self.evaluate_input.text().strip()
        if not expression:
            return
        frame = self.selected_frame()
        self._controller.evaluate(expression, 0 if frame is None else frame.frame_id)
        self.evaluate_input.clear()

    def _show_evaluation(self, expression: str, reply: DebugReply) -> None:
        """把求值的結果寫進輸出 / Write the result of an evaluation into the output."""
        result = reply.value.value if reply.ok and reply.value is not None else reply.error
        self._on_output("", f">>> {expression}\n{result}\n")

    def _show_exception(self, info: ExceptionInfo | None) -> None:
        """把例外的名稱、訊息與追蹤寫進輸出 / Write an exception's name, message and traceback into the output."""
        if info is None:
            return
        self._on_output("", f"{info.exception_id}: {info.description}\n{info.stack_trace}\n")
