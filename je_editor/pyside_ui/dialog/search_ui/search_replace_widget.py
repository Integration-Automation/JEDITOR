from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QThread, QRegularExpression, Signal
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QLabel, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QPlainTextEdit, QMessageBox, QWidget
)

from je_editor.utils.file_scan.ignore_rules import (
    IGNORED_DIRECTORY_NAMES as _SKIP_DIRS,
    is_binary_file as _is_binary,
)
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget


class _SearchWorker(QThread):
    """
    背景搜尋執行緒：在資料夾或專案中搜尋文字
    Background search thread: search text in folder or project
    """
    match_found = Signal(str, int, str)  # (file_path, line_number, line_text)
    finished_signal = Signal(int)  # total_matches

    def __init__(self, root: str, pattern: str, case_sensitive: bool, use_regex: bool) -> None:
        super().__init__()
        self.root = root
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def _compile_pattern(self) -> Optional[re.Pattern]:
        """編譯搜尋樣式；失敗時回傳 None / Compile the search pattern; return None on failure."""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            return re.compile(self.pattern if self.use_regex else re.escape(self.pattern), flags)
        except re.error:
            return None

    def _scan_file(self, fpath: Path, compiled: re.Pattern) -> int:
        """在單一檔案中搜尋所有匹配，發送訊號並回傳匹配數 / Scan a file and emit matches."""
        hits = 0
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    if self._stop:
                        break
                    if compiled.search(line):
                        self.match_found.emit(str(fpath), line_no, line.rstrip("\n\r"))
                        hits += 1
        except (OSError, UnicodeDecodeError):
            # 無法讀取的檔案直接略過 (權限/二進位/鎖定)
            # Skip files that cannot be read (permissions/binary/locked)
            return 0
        return hits

    def run(self) -> None:
        compiled = self._compile_pattern()
        if compiled is None:
            self.finished_signal.emit(0)
            return
        total = 0
        for dirpath, dirnames, filenames in os.walk(self.root):
            if self._stop:
                break
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fname in filenames:
                if self._stop:
                    break
                fpath = Path(dirpath) / fname
                if _is_binary(fpath):
                    continue
                total += self._scan_file(fpath, compiled)
        self.finished_signal.emit(total)


class SearchReplaceDialog(QDialog):
    """
    搜尋與取代對話框，支援三種範圍：單個檔案、資料夾、整個專案
    Search & Replace dialog supporting three scopes: Current File, Folder, Project
    """

    def __init__(self, editor_widget: EditorWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.editor_widget = editor_widget
        self._worker: Optional[_SearchWorker] = None
        self._lang = language_wrapper.language_word_dict.get

        # 對話框設定 / Dialog settings
        self.setWindowTitle(self._lang("search_replace_tab_title"))
        self.setMinimumSize(700, 450)
        self.resize(850, 500)
        # 非模態：可以同時操作編輯器 / Non-modal: can interact with editor simultaneously
        self.setModal(False)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # === Row 1: 搜尋列 / Search row ===
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel(self._lang("search_replace_search_label")))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self._lang("search_replace_search_placeholder"))
        self.search_input.returnPressed.connect(self.do_search)
        search_row.addWidget(self.search_input, 1)

        self.btn_prev = QPushButton(self._lang("search_back_dialog_pushbutton"))
        self.btn_prev.clicked.connect(self.find_prev)
        self.btn_next = QPushButton(self._lang("search_next_dialog_pushbutton"))
        self.btn_next.clicked.connect(self.find_next)
        search_row.addWidget(self.btn_prev)
        search_row.addWidget(self.btn_next)

        self.btn_search = QPushButton(self._lang("search_replace_search_btn"))
        self.btn_search.clicked.connect(self.do_search)
        search_row.addWidget(self.btn_search)
        layout.addLayout(search_row)

        # === Row 2: 取代列 / Replace row ===
        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel(self._lang("search_replace_replace_label")))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText(self._lang("search_replace_replace_placeholder"))
        replace_row.addWidget(self.replace_input, 1)

        self.btn_replace = QPushButton(self._lang("search_replace_replace_btn"))
        self.btn_replace.clicked.connect(self.do_replace)
        self.btn_replace_all = QPushButton(self._lang("search_replace_replace_all_btn"))
        self.btn_replace_all.clicked.connect(self.do_replace_all)
        replace_row.addWidget(self.btn_replace)
        replace_row.addWidget(self.btn_replace_all)
        layout.addLayout(replace_row)

        # === Row 3: 選項列 / Options row ===
        options_row = QHBoxLayout()

        # 範圍選擇 / Scope selector
        options_row.addWidget(QLabel(self._lang("search_replace_scope_label")))
        self.scope_combo = QComboBox()
        self.scope_combo.addItem(self._lang("search_replace_scope_file"), "file")
        self.scope_combo.addItem(self._lang("search_replace_scope_folder"), "folder")
        self.scope_combo.addItem(self._lang("search_replace_scope_project"), "project")
        self.scope_combo.currentIndexChanged.connect(self._on_scope_changed)
        options_row.addWidget(self.scope_combo)

        # 資料夾路徑 / Folder path
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText(self._lang("search_replace_folder_placeholder"))
        self.folder_input.setVisible(False)
        options_row.addWidget(self.folder_input, 1)

        self.btn_pick_folder = QPushButton("…")
        self.btn_pick_folder.setFixedWidth(30)
        self.btn_pick_folder.setVisible(False)
        self.btn_pick_folder.clicked.connect(self._pick_folder)
        options_row.addWidget(self.btn_pick_folder)

        # 大小寫敏感 / Case sensitive
        self.chk_case = QCheckBox(self._lang("search_replace_case_sensitive"))
        options_row.addWidget(self.chk_case)

        # 正則表達式 / Regex
        self.chk_regex = QCheckBox(self._lang("search_replace_regex"))
        options_row.addWidget(self.chk_regex)

        options_row.addStretch()
        layout.addLayout(options_row)

        # === 狀態列 / Status bar ===
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # === 結果區 / Results area ===
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels([
            self._lang("search_replace_col_file"),
            self._lang("search_replace_col_line"),
            self._lang("search_replace_col_text"),
        ])
        self.result_tree.setColumnWidth(0, 300)
        self.result_tree.setColumnWidth(1, 60)
        self.result_tree.itemDoubleClicked.connect(self._on_result_double_click)
        layout.addWidget(self.result_tree, 1)

    # ---------- Scope UI ----------

    def _on_scope_changed(self, index: int) -> None:
        """根據範圍切換顯示/隱藏資料夾選擇 / Toggle folder picker visibility"""
        scope = self.scope_combo.currentData()
        is_folder = scope == "folder"
        self.folder_input.setVisible(is_folder)
        self.btn_pick_folder.setVisible(is_folder)

    def _pick_folder(self) -> None:
        """選擇搜尋資料夾 / Pick search folder"""
        d = QFileDialog.getExistingDirectory(self, self._lang("search_replace_pick_folder"), os.getcwd())
        if d:
            self.folder_input.setText(d)

    # ---------- Search ----------

    def do_search(self) -> None:
        """根據範圍執行搜尋 / Execute search based on scope"""
        pattern = self.search_input.text()
        if not pattern:
            return

        scope = self.scope_combo.currentData()
        if scope == "file":
            self._search_in_current_file(pattern)
        elif scope == "folder":
            folder = self.folder_input.text().strip()
            if not folder or not Path(folder).is_dir():
                self.status_label.setText(self._lang("search_replace_invalid_folder"))
                return
            self._search_in_directory(pattern, folder)
        elif scope == "project":
            project_root = self._get_project_root()
            self._search_in_directory(pattern, project_root)

    def _search_in_current_file(self, pattern: str) -> None:
        """在目前檔案中搜尋 / Search in current file"""
        self.result_tree.clear()
        editor = self.editor_widget.code_edit
        # 讓縮圖標出命中的行 / So the minimap marks the lines it hits
        editor.set_search_term(pattern)
        text = editor.toPlainText()
        case = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()

        flags = 0 if case else re.IGNORECASE
        try:
            compiled = re.compile(pattern if use_regex else re.escape(pattern), flags)
        except re.error as e:
            self.status_label.setText(f"Regex error: {e}")
            return

        count = 0
        file_label = self.editor_widget.current_file or self._lang("search_replace_untitled")
        for line_no, line in enumerate(text.splitlines(), 1):
            if compiled.search(line):
                item = QTreeWidgetItem([file_label, str(line_no), line.strip()])
                item.setData(0, Qt.ItemDataRole.UserRole, {"file": None, "line": line_no})
                self.result_tree.addTopLevelItem(item)
                count += 1

        self.status_label.setText(
            self._lang("search_replace_found_count").format(count=count))

        # 同時高亮第一個匹配 / Also highlight first match
        self.find_next()

    def _search_in_directory(self, pattern: str, root: str) -> None:
        """在資料夾中搜尋 / Search in directory"""
        self.result_tree.clear()
        self.status_label.setText(self._lang("search_replace_searching"))

        # 停止先前的搜尋 / Stop previous search
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()

        self._file_groups = {}
        self._worker = _SearchWorker(
            root, pattern, self.chk_case.isChecked(), self.chk_regex.isChecked()
        )
        self._worker.match_found.connect(self._on_match_found)
        self._worker.finished_signal.connect(self._on_search_finished)
        self._worker.start()

    def _on_match_found(self, file_path: str, line_no: int, line_text: str) -> None:
        """收到搜尋結果 / Receive search result"""
        if file_path not in self._file_groups:
            parent = QTreeWidgetItem([file_path, "", ""])
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            self.result_tree.addTopLevelItem(parent)
            self._file_groups[file_path] = parent
            parent.setExpanded(True)
        parent = self._file_groups[file_path]
        child = QTreeWidgetItem(["", str(line_no), line_text.strip()])
        child.setData(0, Qt.ItemDataRole.UserRole, {"file": file_path, "line": line_no})
        parent.addChild(child)

    def _on_search_finished(self, total: int) -> None:
        """搜尋完成 / Search finished"""
        self.status_label.setText(
            self._lang("search_replace_found_count").format(count=total))

    def _on_result_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """雙擊結果項目：跳轉到對應位置 / Double-click result: navigate to location"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        file_path = data.get("file")
        line_no = data.get("line", 1)

        if file_path is not None:
            # 外部檔案：在新分頁開啟 / External file: open in new tab
            path = Path(file_path)
            if path.is_file():
                self.editor_widget.main_window.go_to_new_tab(path)
                # 跳到指定行 / Jump to line
                current_widget = self.editor_widget.main_window.tab_widget.currentWidget()
                if hasattr(current_widget, "code_edit"):
                    self._goto_line(current_widget.code_edit, line_no)
        else:
            # 目前檔案 / Current file
            self._goto_line(self.editor_widget.code_edit, line_no)

    def _goto_line(self, editor: QPlainTextEdit, line_no: int) -> None:
        """跳轉到指定行 / Navigate to specific line"""
        block = editor.document().findBlockByNumber(line_no - 1)
        if block.isValid():
            cursor = editor.textCursor()
            cursor.setPosition(block.position())
            editor.setTextCursor(cursor)
            editor.centerCursor()
            editor.setFocus()

    # ---------- Find prev/next in current file ----------

    def find_next(self) -> None:
        """在目前檔案中尋找下一個 / Find next in current file"""
        self._find_in_editor(forward=True)

    def find_prev(self) -> None:
        """在目前檔案中尋找上一個 / Find previous in current file"""
        self._find_in_editor(forward=False)

    def _editor_find(self, editor: QPlainTextEdit, pattern: str, flags: "QTextDocument.FindFlag") -> bool:
        """呼叫底層 find，自動處理 regex / Call underlying find with optional regex."""
        if self.chk_regex.isChecked():
            regex = self._build_qregex(pattern)
            return bool(editor.find(regex, flags)) if regex else False
        return bool(editor.find(pattern, flags))

    def _find_in_editor(self, forward: bool) -> None:
        """在編輯器中搜尋，找不到時繞回頭尾 / Search in editor; wrap around when not found."""
        pattern = self.search_input.text()
        if not pattern:
            return
        editor = self.editor_widget.code_edit
        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        if self.chk_case.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self._editor_find(editor, pattern, flags):
            return

        cursor = editor.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.Start if forward else QTextCursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        self._editor_find(editor, pattern, flags)

    def _build_qregex(self, pattern: str) -> Optional[QRegularExpression]:
        """建立 QRegularExpression / Build QRegularExpression"""
        options = QRegularExpression.PatternOption.NoPatternOption
        if not self.chk_case.isChecked():
            options |= QRegularExpression.PatternOption.CaseInsensitiveOption
        regex = QRegularExpression(pattern, options)
        if not regex.isValid():
            return None
        return regex

    # ---------- Replace ----------

    def do_replace(self) -> None:
        """取代目前選取的匹配項 / Replace current selected match"""
        scope = self.scope_combo.currentData()
        if scope == "file":
            self._replace_in_current_editor()
        else:
            self._replace_selected_result()

    def do_replace_all(self) -> None:
        """全部取代 / Replace all"""
        pattern = self.search_input.text()
        replacement = self.replace_input.text()
        if not pattern:
            return

        scope = self.scope_combo.currentData()
        if scope == "file":
            self._replace_all_in_current_file(pattern, replacement)
        elif scope == "folder":
            folder = self.folder_input.text().strip()
            if not folder or not Path(folder).is_dir():
                self.status_label.setText(self._lang("search_replace_invalid_folder"))
                return
            self._replace_all_in_directory(pattern, replacement, folder)
        elif scope == "project":
            project_root = self._get_project_root()
            self._replace_all_in_directory(pattern, replacement, project_root)

    def _replace_in_current_editor(self) -> None:
        """在編輯器中取代目前選取的匹配 / Replace currently selected match in editor"""
        editor = self.editor_widget.code_edit
        replacement = self.replace_input.text()
        cursor = editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(replacement)
            editor.setTextCursor(cursor)
        # 跳到下一個匹配 / Move to next match
        self.find_next()

    def _replace_all_in_current_file(self, pattern: str, replacement: str) -> None:
        """在目前檔案中全部取代 / Replace all in current file"""
        editor = self.editor_widget.code_edit
        text = editor.toPlainText()
        case = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()

        flags = 0 if case else re.IGNORECASE
        try:
            compiled = re.compile(pattern if use_regex else re.escape(pattern), flags)
        except re.error as e:
            self.status_label.setText(f"Regex error: {e}")
            return

        new_text, count = compiled.subn(replacement, text)
        if count > 0:
            cursor = editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(new_text)
            cursor.endEditBlock()

        self.status_label.setText(
            self._lang("search_replace_replaced_count").format(count=count))
        self.do_search()

    def _replace_selected_result(self) -> None:
        """取代結果列表中目前選取的項目 / Replace selected result item"""
        items = self.result_tree.selectedItems()
        if not items:
            return
        item = items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        file_path = data.get("file")
        line_no = data.get("line")
        if not file_path or not line_no:
            return

        pattern = self.search_input.text()
        replacement = self.replace_input.text()
        case = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()
        flags = 0 if case else re.IGNORECASE

        try:
            compiled = re.compile(pattern if use_regex else re.escape(pattern), flags)
        except re.error:
            return

        try:
            # 僅從受信任的 project_root 與經驗證的相對路徑重新組合，
            # 切斷從使用者輸入流入 write_text() 的 taint 鏈 (SonarCloud S2083)
            # Rebuild the target path from the trusted project root plus a
            # validated relative component so user-controlled data never flows
            # directly into write_text() (SonarCloud S2083).
            project_root = Path(self._get_project_root()).resolve()
            try:
                relative_part = Path(file_path).resolve().relative_to(project_root)
            except ValueError:
                self.status_label.setText(f"Error: invalid file path {file_path}")
                return
            p = project_root.joinpath(*relative_part.parts)
            if not p.is_file():
                self.status_label.setText(f"Error: invalid file path {file_path}")
                return
            raw = p.read_bytes()
            enc = "utf-8"
            for _enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
                try:
                    raw.decode(_enc)
                    enc = _enc
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            lines = raw.decode(enc, errors="ignore").splitlines(keepends=True)
            if 0 < line_no <= len(lines):
                lines[line_no - 1] = compiled.sub(replacement, lines[line_no - 1], count=1)
                p.write_text("".join(lines), encoding=enc)
                item.setText(2, lines[line_no - 1].strip())
                self.status_label.setText(
                    self._lang("search_replace_replaced_in_file").format(file=p.name, line=line_no))
        except OSError as e:
            self.status_label.setText(f"Error: {e}")

    @staticmethod
    def _decode_bytes(raw: bytes) -> tuple[str, str] | None:
        """嘗試以多種編碼解碼；失敗回傳 None / Decode bytes trying common encodings."""
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return raw.decode(enc), enc
            except (UnicodeDecodeError, LookupError):
                continue
        return None

    def _replace_all_in_single_file(self, fpath: Path, compiled: re.Pattern, replacement: str) -> int:
        """對單一檔案做替換，回傳替換次數 / Replace in one file; return replace count."""
        try:
            decoded = self._decode_bytes(fpath.read_bytes())
            if decoded is None:
                return 0
            content, enc = decoded
            new_content, count = compiled.subn(replacement, content)
            if count > 0:
                fpath.write_text(new_content, encoding=enc)
            return count
        except OSError:
            return 0

    def _replace_all_in_directory(self, pattern: str, replacement: str, root: str) -> None:
        """在整個目錄中全部取代 / Replace all matches inside every file under the directory."""
        case = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()
        flags = 0 if case else re.IGNORECASE

        try:
            compiled = re.compile(pattern if use_regex else re.escape(pattern), flags)
        except re.error as e:
            self.status_label.setText(f"Regex error: {e}")
            return

        confirm = QMessageBox.question(
            self,
            self._lang("search_replace_confirm_title"),
            self._lang("search_replace_confirm_replace_all").format(root=root),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        total_files = 0
        total_replacements = 0

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if _is_binary(fpath):
                    continue
                count = self._replace_all_in_single_file(fpath, compiled, replacement)
                if count > 0:
                    total_files += 1
                    total_replacements += count

        self.status_label.setText(
            self._lang("search_replace_replaced_summary").format(
                count=total_replacements, files=total_files))
        # 重新搜尋以更新結果 / Re-search to update results
        self.do_search()

    # ---------- Helpers ----------

    def _get_project_root(self) -> str:
        """取得專案根目錄 / Get project root directory"""
        # 使用 treeview 的根目錄，或者 cwd
        if self.editor_widget.project_treeview_model:
            root = self.editor_widget.project_treeview_model.rootPath()
            if root:
                return root
        return os.getcwd()

    def closeEvent(self, event: QCloseEvent) -> None:
        """關閉對話框時停止搜尋執行緒並清掉縮圖標記 / Stop the worker and clear the marks"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait()
        editor = getattr(self.editor_widget, "code_edit", None)
        if editor is not None:
            editor.set_search_term("")
        super().closeEvent(event)
