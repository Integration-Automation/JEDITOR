from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextOption, QTextCharFormat, QColor, QFont, QSyntaxHighlighter, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem, QPlainTextEdit,
    QLineEdit, QSizePolicy, QSplitter, QFileDialog, QMessageBox, QInputDialog, QMenuBar
)
from git import Repo, InvalidGitRepositoryError, NoSuchPathError, GitCommandError


class GitChangeItem:
    """Simple data holder for a file change entry.
    簡單的資料結構，用來存放檔案變更資訊。
    """

    def __init__(self, path: str, status: str):
        self.path = path  # repo 相對路徑 / repo-relative path
        self.status = status  # 狀態，例如 'untracked', 'modified', 'deleted', 'renamed', 'staged'


class GitGui(QWidget):
    def __init__(self):
        super().__init__()
        self.current_repo: Repo | None = None
        self.last_opened_repo_path = None
        self._init_ui()  # 初始化 UI
        self._restore_last_opened_repository()  # 嘗試還原上次開啟的 repo

    def _init_ui(self):
        # === Top controls / 上方控制區 ===
        self.repo_path_label = QLabel("Repository: (none)")
        self.open_repo_button = QPushButton("Open Repo")
        self.branch_selector = QComboBox()
        self.checkout_button = QPushButton("Checkout")
        self.clone_repo_button = QPushButton("Clone Repo")
        self.repo_status_label = QLabel("Status: -")
        self.commit_status_label = QLabel("Unpushed commits: ...")

        top = QHBoxLayout()
        top.addWidget(self.repo_path_label, 1)
        top.addWidget(QLabel("Branch:"))
        top.addWidget(self.branch_selector, 1)
        top.addWidget(self.checkout_button)
        top.addWidget(self.open_repo_button)
        top.addWidget(self.clone_repo_button)

        # === Left: changes list / 左側：變更清單 ===
        self.changes_list_widget = QListWidget()
        self.changes_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # === Right: diff / info viewer / 右側：差異或資訊檢視器 ===
        self.diff_viewer = QPlainTextEdit()
        self.diff_viewer.setReadOnly(True)
        self.diff_viewer.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.diff_viewer.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.diff_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 設定等寬字型 / Use monospaced font
        mono = self.font()
        mono.setFamily("Consolas")
        mono.setPointSize(10)
        self.diff_viewer.setFont(mono)

        # 差異高亮器 / Diff syntax highlighter
        self.highlighter = GitDiffHighlighter(self.diff_viewer.document())
        self.highlighter.configure_theme_colors()
        self.highlighter.rehighlight()

        # 左右分割器 / Splitter for changes list and diff viewer
        splitter = QSplitter()
        splitter.addWidget(self.changes_list_widget)
        splitter.addWidget(self.diff_viewer)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # === Bottom: staging and commit controls / 下方：stage 與 commit 控制 ===
        self.commit_message_input = QLineEdit()
        self.commit_message_input.setPlaceholderText("Commit message...")
        self.stage_selected_button = QPushButton("Stage Selected")
        self.unstage_selected_button = QPushButton("Unstage Selected")
        self.stage_all_button = QPushButton("Stage All")
        self.commit_button = QPushButton("Commit")
        self.unstage_all_button = QPushButton("Unstage All")
        self.track_all_untracked_button = QPushButton("Track All Untracked")
        self.git_push_button = QPushButton("Push")

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Message:"))
        bottom.addWidget(self.commit_message_input, 1)
        bottom.addWidget(self.stage_selected_button)
        bottom.addWidget(self.unstage_selected_button)
        bottom.addWidget(self.unstage_all_button)
        bottom.addWidget(self.stage_all_button)
        bottom.addWidget(self.commit_button)
        bottom.addWidget(self.track_all_untracked_button)
        bottom.addWidget(self.git_push_button)

        # === Main layout / 主版面配置 ===
        center_layout = QVBoxLayout()
        center_layout.addLayout(top)
        center_layout.addWidget(self.repo_status_label)
        center_layout.addWidget(self.commit_status_label)
        center_layout.addWidget(splitter, 1)
        center_layout.addLayout(bottom)
        self.setLayout(center_layout)

        # === Events / 事件綁定 ===
        self.open_repo_button.clicked.connect(self.on_open_repository_requested)
        self.clone_repo_button.clicked.connect(self.on_clone_repository_requested)
        self.branch_selector.currentTextChanged.connect(self.on_branch_selection_changed)
        self.checkout_button.clicked.connect(self.on_checkout_branch_requested)
        self.changes_list_widget.itemSelectionChanged.connect(self.on_change_selection_changed)
        self.stage_selected_button.clicked.connect(self.on_stage_selected_changes)
        self.unstage_selected_button.clicked.connect(self.on_unstage_selected_changes)
        self.stage_all_button.clicked.connect(self.on_stage_all_changes)
        self.commit_button.clicked.connect(self.on_commit_staged_changes)
        self.unstage_all_button.clicked.connect(self.on_unstage_all_changes)
        self.track_all_untracked_button.clicked.connect(self.on_track_all_untracked_files)
        self.git_push_button.clicked.connect(self.on_push_to_github)

        self._update_ui_controls(enabled=False)

        # === MenuBar / 選單列 ===
        menubar = QMenuBar(self)
        theme_menu = menubar.addMenu("Theme")

        light_action = QAction("Light", self)
        dark_action = QAction("Dark", self)

        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)

        light_action.triggered.connect(self.apply_light_theme)
        dark_action.triggered.connect(self.apply_dark_theme)

        center_layout.setMenuBar(menubar)

        # === Timer ===
        self.update_commit_status_timer = QTimer()
        self.update_commit_status_timer.setInterval(1000)
        self.update_commit_status_timer.timeout.connect(self.update_commit_status)
        self.update_commit_status_timer.start()

    # ---------- Repo operations ----------
    # ---------- 儲存庫操作 ----------

    def _restore_last_opened_repository(self):
        """
        Restore the last opened repository if available.
        如果有記錄上次開啟的儲存庫，則嘗試重新載入。
        """
        if self.last_opened_repo_path:
            self._load_repository_from_path(Path(self.last_opened_repo_path))

    def on_open_repository_requested(self):
        """
        Open a Git repository via file dialog.
        透過檔案選擇對話框開啟 Git 儲存庫。
        """
        repo_directory = QFileDialog.getExistingDirectory(self, "Open Git Repository")
        if not repo_directory:
            return
        self._load_repository_from_path(Path(repo_directory))
        self.last_opened_repo_path = str(repo_directory)

    def _load_repository_from_path(self, selected_directory_path: Path):
        """
        Load a Git repository from a given folder.
        從指定資料夾載入 Git 儲存庫。
        """
        try:
            self.current_repo = Repo(selected_directory_path)
            if self.current_repo.bare:
                # 不支援 bare repo
                raise InvalidGitRepositoryError(f"Bare repository not supported: {selected_directory_path}")
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            # 如果不是合法的 Git repo，顯示錯誤訊息並重置 UI
            QMessageBox.critical(self, "Error", f"Not a valid git repository:\n{e}")
            self.current_repo = None
            self._update_ui_controls(False)
            self.repo_path_label.setText("Repository: (none)")
            self.branch_selector.clear()
            self.changes_list_widget.clear()
            self.diff_viewer.setPlainText("")
            self.repo_status_label.setText("Status: -")
            return

        # 成功載入 repo，更新 UI
        self.repo_path_label.setText(f"Repository: {selected_directory_path}")
        self._refresh_branch_list()
        self._refresh_change_list()
        self._update_ui_controls(True)

    def _refresh_branch_list(self):
        """
        Refresh branch list in the combo box.
        更新分支清單。
        """
        if not self.current_repo:
            self.branch_selector.clear()
            return

        heads = [h.name for h in self.current_repo.heads]
        self.branch_selector.clear()
        self.branch_selector.addItems(heads)

        # 設定目前分支
        try:
            current = self.current_repo.active_branch.name
            idx = self.branch_selector.findText(current)
            if idx >= 0:
                self.branch_selector.setCurrentIndex(idx)
        except TypeError:
            # Detached HEAD 狀態
            self.branch_selector.setEditable(True)
            self.branch_selector.setEditText(self.current_repo.head.commit.hexsha[:8])

    def on_branch_selection_changed(self):
        """
        Triggered when branch selection changes.
        分支選擇改變時觸發，目前不做動作，需按下 Checkout 才會生效。
        """
        pass

    def on_checkout_branch_requested(self):
        """
        Checkout the selected branch.
        切換到選取的分支。
        """
        if not self.current_repo:
            return
        target = self.branch_selector.currentText().strip()
        if not target:
            QMessageBox.warning(self, "Checkout", "Branch name is empty.")
            return
        try:
            self.current_repo.git.checkout(target)
            self._refresh_branch_list()
            self._refresh_change_list()
        except GitCommandError as e:
            QMessageBox.critical(self, "Checkout Error", str(e))

    # ---------- Changes & staging ----------
    # ---------- 變更與暫存 ----------

    def _is_binary_path(self, abs_path: Path, sniff_bytes: int = 2048) -> bool:
        """簡單嗅探檔案是否為二進位：若包含 NUL bytes，視為二進位。"""
        try:
            with open(abs_path, 'rb') as f:
                chunk = f.read(sniff_bytes)
                return b'\x00' in chunk
        except Exception:
            return False

    def _safe_set_diff_text(self, text: str):
        # 套用高亮顏色
        self.diff_viewer.setPlainText(text if text else "(no content)")
        if hasattr(self, "highlighter"):
            self.highlighter.rehighlight()

    def _show_diff_for_change(self, change: GitChangeItem):
        current_repo = self.current_repo
        if not current_repo:
            self._safe_set_diff_text("Error: repository not loaded.")
            return

        # Normalize paths (for rename "a -> b" 取目的與來源)
        src, dst = None, None
        if "->" in change.path and change.status in ("renamed", "staged"):
            parts = [p.strip() for p in change.path.split("->")]
            if len(parts) == 2:
                src, dst = parts
        rel = dst or change.path
        abs_path = Path(current_repo.working_tree_dir) / Path(rel)

        try:
            # Untracked: 顯示新增檔案的內容（模擬 unified diff）
            if change.status == "untracked":
                if not abs_path.exists():
                    self._safe_set_diff_text(f"(untracked file missing: {rel})")
                    return
                if self._is_binary_path(abs_path):
                    self._safe_set_diff_text(f"(binary file, no textual diff: {rel})")
                    return
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                header = f"--- /dev/null\n+++ b/{rel}\n"
                body = "\n".join(f"+{line}" for line in content.splitlines())
                self._safe_set_diff_text(header + body)
                return

            # Deleted: 顯示與 HEAD/Index 的差異（若工作樹檔案不存在也能呈現）
            if change.status == "deleted":
                # working tree vs index（未暫存刪除）
                if rel and not current_repo.index.diff(None, paths=[rel]):
                    # 若 diff(None) 空，試試 index vs HEAD
                    diff_text = current_repo.git.diff("--cached", rel)
                else:
                    diff_text = current_repo.git.diff(rel)
                if not diff_text.strip():
                    self._safe_set_diff_text(f"(deleted file; no textual diff or already committed: {rel})")
                else:
                    self._safe_set_diff_text(diff_text)
                return

            # Renamed: 顯示 rename 變更；若僅 rename 無內容改動，diff 可能為空
            if change.status == "renamed":
                # 優先顯示 staged rename
                diff_text = ""
                try:
                    if dst:
                        diff_text = current_repo.git.diff("--cached", dst)
                except GitCommandError:
                    pass
                if not diff_text.strip():
                    # fallback: working tree
                    try:
                        diff_text = current_repo.git.diff(dst or rel)
                    except GitCommandError:
                        diff_text = ""
                if not diff_text.strip():
                    # 顯示 rename meta
                    self._safe_set_diff_text(
                        f"diff --git a/{src} b/{dst}\nrename from {src}\nrename to {dst}\n(no line changes)")
                else:
                    self._safe_set_diff_text(diff_text)
                return

            # Staged vs HEAD
            if change.status == "staged":
                diff_text = current_repo.git.diff("--cached", rel)
                if not diff_text.strip():
                    self._safe_set_diff_text("(no staged changes vs HEAD)")
                else:
                    self._safe_set_diff_text(diff_text)
                return

            # Modified / general unstaged
            if change.status in ("modified",):
                # working tree vs index
                diff_text = current_repo.git.diff(rel)
                if not diff_text.strip():
                    # 若空，嘗試 index vs HEAD（可能已被暫存）
                    try:
                        diff_text = current_repo.git.diff("--cached", rel)
                    except GitCommandError:
                        diff_text = ""
                if not diff_text.strip():
                    self._safe_set_diff_text("(no unstaged changes; file may be already staged)")
                else:
                    self._safe_set_diff_text(diff_text)
                return

            # Fallback
            self._safe_set_diff_text(f"(no diff handler for status: {change.status})")

        except GitCommandError as e:
            self._safe_set_diff_text(f"Git error while generating diff:\n{e}")
        except FileNotFoundError:
            self._safe_set_diff_text(f"(file missing in working tree: {rel})")
        except Exception as e:
            self._safe_set_diff_text(f"Unexpected error while generating diff:\n{e}")

    def _refresh_change_list(self):
        """
        Collect changes from working tree and index, then render list.
        收集工作目錄與索引的變更，並更新清單。
        """
        if not self.current_repo:
            self.changes_list_widget.clear()
            self.diff_viewer.setPlainText("")
            self.repo_status_label.setText("Status: -")
            return

        repository = self.current_repo

        # === Untracked files / 未追蹤檔案 ===
        untracked_files = list(repository.untracked_files)

        # === Unstaged changes (working tree vs index) / 未暫存變更 ===
        working_tree_vs_index_diff = repository.index.diff(None)  # None 表示與工作目錄比較
        unstaged_changes = []
        for d in working_tree_vs_index_diff:
            path = d.a_path if d.a_path else d.b_path
            status = "modified"
            if d.change_type == "D":
                status = "deleted"
            elif d.change_type == "R":
                status = "renamed"
                path = f"{d.a_path} -> {d.b_path}"
            unstaged_changes.append(GitChangeItem(path, status))

        # === Staged changes (index vs HEAD) / 已暫存變更 ===
        index_vs_head_diff = repository.index.diff("HEAD")
        staged_changes = []
        for d in index_vs_head_diff:
            path = d.a_path if d.a_path else d.b_path
            status = "staged"
            staged_changes.append(GitChangeItem(path, status))

        # === Render list / 渲染清單 ===
        self.changes_list_widget.clear()

        def add_item(txt: str, bold=False, disabled=False):
            """
            Add a section header item to the list.
            新增一個區段標題項目到清單。
            """
            list_item = QListWidgetItem(txt)
            if bold:
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)
            if disabled:
                list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
            self.changes_list_widget.addItem(list_item)

        # 區段標題與檔案項目
        add_item("— Untracked —", bold=True, disabled=True)
        for path in untracked_files:
            self._add_change_item(GitChangeItem(path, "untracked_files"))

        add_item("— Unstaged —", bold=True, disabled=True)
        for item in unstaged_changes:
            self._add_change_item(item)

        add_item("— Staged —", bold=True, disabled=True)
        for item in staged_changes:
            self._add_change_item(item)

        # === Status summary / 狀態摘要 ===
        summary = (
            f"Branch: {getattr(repository.head, 'reference', None) and repository.active_branch.name if not repository.head.is_detached else '(detached)'}\n"
            f"Untracked: {len(untracked_files)} | Unstaged: {len(unstaged_changes)} | Staged: {len(staged_changes)}"
        )
        self.repo_status_label.setText(f"Status: {summary}")
        self.diff_viewer.setPlainText("Select files to stage/unstage.")

    def _add_change_item(self, change: GitChangeItem):
        """
        Add a file change entry to the list.
        將檔案變更項目加入清單。
        """
        item_text = f"[{change.status}] {change.path}"
        list_item = QListWidgetItem(item_text)
        list_item.setData(Qt.ItemDataRole.UserRole, change)  # 存放 GitChangeItem 物件
        list_item.setCheckState(Qt.CheckState.Unchecked)  # 預設未勾選
        self.changes_list_widget.addItem(list_item)

    def _get_selected_changes(self):
        """
        Collect all checked selected_items from the list.
        收集所有被勾選的檔案項目。
        """
        selected_items = []
        for i in range(self.changes_list_widget.count()):
            list_item = self.changes_list_widget.item(i)
            if list_item.checkState() == Qt.CheckState.Checked:
                change = list_item.data(Qt.ItemDataRole.UserRole)
                if isinstance(change, GitChangeItem):
                    selected_items.append(change)
        return selected_items

    def on_change_selection_changed(self):
        """
        Show diff for the selected file.
        顯示選取檔案的差異。
        """
        if not self.current_repo:
            return
        selected_items = self.changes_list_widget.selectedItems()
        if not selected_items:
            self.diff_viewer.clear()
            return

        # 取最後一個被選中的項目 / Take the last selected item
        list_item = selected_items[-1]
        change = list_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(change, GitChangeItem):
            self._show_diff_for_change(change)

    def on_stage_selected_changes(self):
        """
        Stage selected_changes files.
        將選取的檔案加入暫存區。
        """
        if not self.current_repo:
            return
        selected_changes = self._get_selected_changes()
        if not selected_changes:
            QMessageBox.information(self, "Stage", "No files selected_changes.")
            return
        try:
            # 處理重新命名的檔案 "a -> b"，需要同時 stage 移除 a 與新增 b
            file_paths = []
            for change_entry in selected_changes:
                if "->" in change_entry.path and change_entry.status in ("renamed", "modified", "staged"):
                    parts = change_entry.path.split("->")
                    source_path = parts[0].strip()
                    destination_path = parts[1].strip()
                    file_paths.extend([source_path, destination_path])
                else:
                    file_paths.append(change_entry.path)
            self.current_repo.index.add(file_paths)
            self.current_repo.index.write()
            self._refresh_change_list()
        except GitCommandError as e:
            QMessageBox.critical(self, "Stage Error", str(e))

    def on_unstage_selected_changes(self):
        """
        Unstage selected_changes files.
        將選取的檔案從暫存區移除。
        """
        if not self.current_repo:
            return
        selected_changes = self._get_selected_changes()
        if not selected_changes:
            QMessageBox.information(self, "Unstage", "No files selected_changes.")
            return
        try:
            file_paths = []
            for change_entry in selected_changes:
                print(change_entry.path)
                if "->" in change_entry.path and change_entry.status in ("renamed", "staged"):
                    parts = change_entry.path.split("->")
                    source_path = parts[0].strip()
                    destination_path = parts[1].strip()
                    file_paths.extend([source_path, destination_path])
                else:
                    file_paths.append(change_entry.path)

            if self.current_repo.head.is_valid():
                # 有 HEAD 的情況：reset index
                self.current_repo.git.reset("HEAD", "--", *file_paths)
            else:
                # 初始 commit（沒有 HEAD）：直接從 index 移除
                for file_path in file_paths:
                    try:
                        self.current_repo.index.remove([file_path], working_tree=True)
                    except Exception:
                        pass
            self._refresh_change_list()
        except GitCommandError as e:
            QMessageBox.critical(self, "Unstage Error", str(e))

    def on_stage_all_changes(self):
        """
        Stage all changes (equivalent to git add -A).
        將所有變更加入暫存區（等同於 git add -A）。
        """
        if not self.current_repo:
            return
        try:
            self.current_repo.git.add("-A")
            self._refresh_change_list()
        except GitCommandError as e:
            QMessageBox.critical(self, "Stage All Error", str(e))

    def on_commit_staged_changes(self):
        """
        Commit staged changes with a message.
        提交已暫存的變更。
        """
        if not self.current_repo:
            return
        commit_message = self.commit_message_input.text().strip()
        if not commit_message:
            QMessageBox.warning(self, "Commit", "Commit message is empty.")
            return
        # 確認是否有 staged 變更
        staged_changes = list(self.current_repo.index.diff("HEAD"))
        if not staged_changes and self.current_repo.head.is_valid():
            QMessageBox.information(self, "Commit", "No staged changes to commit.")
            return
        try:
            # 支援初始 commit（沒有 HEAD）
            self.current_repo.index.commit(commit_message)
            self.commit_message_input.clear()
            self._refresh_change_list()
            QMessageBox.information(self, "Commit", "Commit successful.")
        except GitCommandError as e:
            QMessageBox.critical(self, "Commit Error", str(e))

    def _update_ui_controls(self, enabled: bool):
        """
        Enable or disable UI controls depending on repo state.
        根據是否有開啟 repo 來啟用或停用 UI 控制項。
        """
        for widget in (
                self.branch_selector, self.checkout_button, self.changes_list_widget,
                self.diff_viewer, self.commit_message_input, self.stage_selected_button,
                self.unstage_selected_button, self.stage_all_button, self.commit_button,
                self.unstage_all_button, self.track_all_untracked_button, self.git_push_button
        ):
            widget.setEnabled(enabled)

    def on_unstage_all_changes(self):
        """
        Unstage all changes.
        將所有檔案從暫存區移除。
        """
        if not self.current_repo:
            return
        try:
            if self.current_repo.head.is_valid():
                # 有 HEAD 的情況：reset index
                self.current_repo.git.reset("HEAD")
            else:
                # 初始 commit（沒有 HEAD）：清空 index
                self.current_repo.index.clear()
                self.current_repo.index.write()
            self._refresh_change_list()
        except Exception as e:
            QMessageBox.critical(self, "Unstage All Error", str(e))

    def on_track_all_untracked_files(self):
        """
        Track all untracked files.
        將所有未追蹤檔案加入暫存區。
        """
        if not self.current_repo:
            return
        try:
            untracked_files = self.current_repo.untracked_files
            if not untracked_files:
                QMessageBox.information(self, "Track Untracked", "No untracked_files files found.")
                return
            self.current_repo.index.add(untracked_files)
            self.current_repo.index.write()
            self._refresh_change_list()
            QMessageBox.information(self, "Track Untracked", f"Tracked {len(untracked_files)} untracked_files files.")
        except Exception as e:
            QMessageBox.critical(self, "Track Untracked Error", str(e))

    def on_clone_repository_requested(self):
        """
        Clone a remote repository into a local folder.
        複製遠端 Git 儲存庫到本地資料夾。
        """
        # 輸入遠端 URL
        remote_url, is_confirmed = QInputDialog.getText(self, "Clone Repository", "Remote URL:")
        if not is_confirmed or not remote_url.strip():
            return

        # 選擇目標資料夾
        target_directory = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if not target_directory:
            return

        try:
            # 在目標資料夾下建立 repo
            repository_path = Path(target_directory) / Path(remote_url).name.replace(".git", "")
            if repository_path.exists():
                QMessageBox.warning(self, "Clone Repo", f"Target folder already exists:\n{repository_path}")
                return

            Repo.clone_from(remote_url, repository_path)
            QMessageBox.information(self, "Clone Repo", f"Repository cloned to:\n{repository_path}")

            # 自動載入新 repo
            self._load_repository_from_path(repository_path)

        except GitCommandError as e:
            QMessageBox.critical(self, "Clone Error", str(e))

    # ===== GitHub =====

    def on_push_to_github(self):
        if not self.current_repo:
            QMessageBox.warning(self, "Warning", "No repository opened.")
            return
        try:
            origin = self.current_repo.remote(name="origin")
            result = origin.push()
            msg = "\n".join(str(r) for r in result)
            QMessageBox.information(self, "Push Result", f"Pushed to origin:\n{msg}")
        except Exception as e:
            QMessageBox.critical(self, "Track Untracked Error", str(e))

    def get_unpushed_commit_count(self, remote_name: str = "origin") -> dict:
        try:
            repo = self.current_repo
            if repo is None:
                return {"ahead": 0, "behind": 0, "error": "No repo loaded"}
            if repo.bare:
                return {"ahead": 0, "behind": 0, "error": "Repository is bare"}
            if repo.head.is_detached:
                return {"ahead": 0, "behind": 0, "error": "HEAD is detached"}

            branch = repo.active_branch
            remote = repo.remote(remote_name)
            remote.fetch()

            upstream_ref = f"{remote_name}/{branch.name}"
            if upstream_ref not in repo.refs:
                return {"ahead": 0, "behind": 0, "error": f"No upstream branch for {branch.name}"}

            ahead_commits = list(repo.iter_commits(f"{upstream_ref}..{branch.name}"))
            behind_commits = list(repo.iter_commits(f"{branch.name}..{upstream_ref}"))

            return {"ahead": len(ahead_commits), "behind": len(behind_commits), "error": None}

        except GitCommandError as e:
            return {"ahead": 0, "behind": 0, "error": f"Git error: {e}"}
        except Exception as e:
            return {"ahead": 0, "behind": 0, "error": str(e)}

    def update_commit_status(self):
        result = self.get_unpushed_commit_count()
        if result["error"]:
            self.commit_status_label.setText(f"Error: {result['error']}")
        else:
            self.commit_status_label.setText(
                f"Ahead (push): {result['ahead']} | Behind (pull): {result['behind']}"
            )

    # ===== Theme =====

    def apply_light_theme(self):
        """
        Switch to light theme highlighting.
        切換到淺色主題的高亮顯示。
        """
        self.highlighter.configure_theme_colors(use_light_mode=True)
        self.highlighter.rehighlight()

    def apply_dark_theme(self):
        """
        Switch to dark theme highlighting.
        切換到深色主題的高亮顯示。
        """
        self.highlighter.configure_theme_colors()
        self.highlighter.rehighlight()


class GitDiffHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Git diff text.
    Git diff 文字的語法高亮器。
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.configure_theme_colors()

    def configure_theme_colors(self, use_light_mode: bool = False):
        """
        Update colors depending on theme.
        根據主題更新顏色。
        """
        if use_light_mode:
            # 淺色模式配色（GitHub 風格）
            self.color_added = QColor("#22863a")  # 綠色（新增行）
            self.color_removed = QColor("#cb2431")  # 紅色（刪除行）
            self.color_header = QColor("#005cc5")  # 藍色（hunk header）
            self.color_meta = QColor("#6a737d")  # 灰色（meta 資訊）
        else:
            # 深色模式配色（VSCode / GitHub Dark 風格）
            self.color_added = QColor("#85e89d")  # 淺綠
            self.color_removed = QColor("#f97583")  # 淺紅
            self.color_header = QColor("#79b8ff")  # 淺藍
            self.color_meta = QColor("#959da5")  # 淺灰

        # === 格式定義 / Format definitions ===
        self.added_format = QTextCharFormat()
        self.added_format.setForeground(self.color_added)

        self.removed_format = QTextCharFormat()
        self.removed_format.setForeground(self.color_removed)

        self.header_format = QTextCharFormat()
        self.header_format.setForeground(self.color_header)
        self.header_format.setFontWeight(QFont.Weight.Bold)

        self.meta_format = QTextCharFormat()
        self.meta_format.setForeground(self.color_meta)

    def highlightBlock(self, line_text: str):
        """
        Apply highlighting rules to each line of diff text.
        對 diff 文字的每一行套用高亮規則。
        """
        if line_text.startswith("+") and not line_text.startswith("+++"):
            # 新增行 / Added line
            self.setFormat(0, len(line_text), self.added_format)
        elif line_text.startswith("-") and not line_text.startswith("---"):
            # 刪除行 / Removed line
            self.setFormat(0, len(line_text), self.removed_format)
        elif line_text.startswith("@@"):
            # Hunk header
            self.setFormat(0, len(line_text), self.header_format)
        elif line_text.startswith("diff ") or line_text.startswith("index ") or line_text.startswith(
                "---") or line_text.startswith(
                "+++"):
            # Meta 資訊（檔案路徑、index、diff header）
            self.setFormat(0, len(line_text), self.meta_format)
