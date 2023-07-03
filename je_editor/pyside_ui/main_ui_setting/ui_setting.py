from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QScrollArea, QSplitter

from je_editor.pyside_ui.code_editor.code_edit_plaintext import CodeEditor
from je_editor.pyside_ui.code_result.code_record import CodeRecord


def set_ui(ui_we_want_to_set: QMainWindow):
    # set qt window
    ui_we_want_to_set.setWindowTitle("JEditor")
    # Splitter
    ui_we_want_to_set.edit_splitter = QSplitter()
    ui_we_want_to_set.edit_splitter.setOrientation(Qt.Orientation.Vertical)
    ui_we_want_to_set.edit_splitter.setChildrenCollapsible(False)
    # code edit and code result plaintext
    ui_we_want_to_set.code_edit = CodeEditor()
    ui_we_want_to_set.code_result = CodeRecord()
    ui_we_want_to_set.code_edit_scroll_area = QScrollArea()
    ui_we_want_to_set.code_edit_scroll_area.setWidgetResizable(True)
    ui_we_want_to_set.code_edit_scroll_area.setViewportMargins(0, 0, 0, 0)
    ui_we_want_to_set.code_edit_scroll_area.setWidget(ui_we_want_to_set.code_edit)
    ui_we_want_to_set.code_result_scroll_area = QScrollArea()
    ui_we_want_to_set.code_result_scroll_area.setWidgetResizable(True)
    ui_we_want_to_set.code_result_scroll_area.setViewportMargins(0, 0, 0, 0)
    ui_we_want_to_set.code_result_scroll_area.setWidget(ui_we_want_to_set.code_result)
    ui_we_want_to_set.grid_layout.setRowStretch(0, 10)
    ui_we_want_to_set.grid_layout.setColumnStretch(1, 10)
    ui_we_want_to_set.edit_splitter.addWidget(ui_we_want_to_set.code_edit_scroll_area)
    ui_we_want_to_set.edit_splitter.addWidget(ui_we_want_to_set.code_result_scroll_area)
    ui_we_want_to_set.edit_splitter.setStretchFactor(0, 7)
    ui_we_want_to_set.grid_layout.addWidget(ui_we_want_to_set.edit_splitter, 0, 1)
