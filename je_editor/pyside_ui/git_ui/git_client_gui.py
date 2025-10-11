import traceback

from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QComboBox, QHBoxLayout, QListWidget, QPlainTextEdit, \
    QSizePolicy, QSplitter, QLineEdit, QVBoxLayout, QMessageBox, QFileDialog, QInputDialog

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.git_client.git import Worker, GitService
from je_editor.git_client.github import GitCloneHandler


class Gitgui(QWidget):

    def __init__(self):
        super().__init__()
        self.git = GitService()
        self.clone_handler = GitCloneHandler()
        self.language_wrapper_get = language_wrapper.language_word_dict.get
        self._init_ui()

    def _init_ui(self):
        # Top controls
        self.repo_label = QLabel(self.language_wrapper_get("label_repo_initial"))
        self.btn_open = QPushButton(self.language_wrapper_get("btn_open_repo"))
        self.branch_combo = QComboBox()
        self.btn_checkout = QPushButton(self.language_wrapper_get("btn_switch_branch"))
        self.btn_pull = QPushButton(self.language_wrapper_get("btn_pull"))
        self.btn_push = QPushButton(self.language_wrapper_get("btn_push"))
        self.remote_combo = QComboBox()
        self.clone_button = QPushButton(self.language_wrapper_get("btn_clone_remote"))
        self.clone_button.clicked.connect(self._on_clone_remote_repo)

        top = QHBoxLayout()
        top.addWidget(self.repo_label, 2)
        top.addWidget(self.btn_open)
        top.addWidget(QLabel(self.language_wrapper_get("label_remote")))
        top.addWidget(self.remote_combo)
        top.addWidget(QLabel(self.language_wrapper_get("label_branch")))
        top.addWidget(self.branch_combo, 1)
        top.addWidget(self.btn_checkout)
        top.addWidget(self.btn_pull)
        top.addWidget(self.btn_push)
        top.addWidget(self.clone_button)

        # Left commits list
        self.commit_list = QListWidget()
        self.commit_list.setMinimumWidth(380)

        # Right diff viewer
        self.diff_view = QPlainTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.diff_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.diff_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        mono = self.font()
        mono.setFamily("Consolas")
        mono.setPointSize(10)
        self.diff_view.setFont(mono)

        splitter = QSplitter()
        splitter.addWidget(self.commit_list)
        splitter.addWidget(self.diff_view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # Bottom commit box
        self.msg_edit = QLineEdit()
        self.msg_edit.setPlaceholderText(self.language_wrapper_get("placeholder_commit_message"))
        self.btn_stage_all = QPushButton(self.language_wrapper_get("btn_stage_all"))
        self.btn_commit = QPushButton(self.language_wrapper_get("btn_commit"))

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel(self.language_wrapper_get("label_message")))
        bottom.addWidget(self.msg_edit, 1)
        bottom.addWidget(self.btn_stage_all)
        bottom.addWidget(self.btn_commit)

        # Layout
        center_layout = QVBoxLayout()
        center_layout.addLayout(top)
        center_layout.addWidget(splitter, 1)
        center_layout.addLayout(bottom)
        self.setLayout(center_layout)

        # Events
        self.btn_open.clicked.connect(self.on_open_repo)
        self.branch_combo.currentTextChanged.connect(self.on_branch_changed)
        self.btn_checkout.clicked.connect(self.on_checkout)
        self.commit_list.itemSelectionChanged.connect(self.on_commit_selected)
        self.btn_stage_all.clicked.connect(self.on_stage_all)
        self.btn_commit.clicked.connect(self.on_commit)
        self.btn_pull.clicked.connect(self.on_pull)
        self.btn_push.clicked.connect(self.on_push)

        self._update_controls(enabled=False)

    # ------------- UI helpers -------------
    def _update_controls(self, enabled: bool):
        for w in [
            self.branch_combo, self.btn_checkout, self.commit_list,
            self.btn_stage_all, self.btn_commit, self.btn_pull, self.btn_push, self.remote_combo
        ]:
            w.setEnabled(enabled)

    def _error(self, title: str, err: Exception):
        traceback.print_exc()
        QMessageBox.critical(self, title, f"{title}\n\n{err}")

    def _info(self, title: str, msg: str):
        QMessageBox.information(self, title, msg)

    # ------------- Event handlers -------------
    def on_open_repo(self):
        path = QFileDialog.getExistingDirectory(self, self.language_wrapper_get("dialog_choose_repo"))
        if not path:
            return
        try:
            self.git.open_repo(path)
            self.repo_label.setText(f"Repo: {path}")
            self._refresh_branches()
            self._refresh_remotes()
            self._update_controls(enabled=True)
            self._load_commits_async()
        except Exception as e:
            self._error(self.language_wrapper_get("err_open_repo"), e)

    def _refresh_remotes(self):
        self.remote_combo.clear()
        try:
            remotes = self.git.remotes()
            self.remote_combo.addItems(remotes if remotes else [self.language_wrapper_get("default_remote")])
        except Exception:
            self.remote_combo.addItem(self.language_wrapper_get("default_remote"))

    def _refresh_branches(self):
        self.branch_combo.blockSignals(True)
        self.branch_combo.clear()
        try:
            branches = self.git.list_branches()
            self.branch_combo.addItems(branches)
            cur = self.git.current_branch()
            idx = self.branch_combo.findText(cur)
            if idx >= 0:
                self.branch_combo.setCurrentIndex(idx)
        except Exception as e:
            self._error(self.language_wrapper_get("err_load_branches"), e)
        finally:
            self.branch_combo.blockSignals(False)

    def on_branch_changed(self, branch: str):
        if not branch:
            return
        self._load_commits_async(branch)

    def _load_commits_async(self, branch: str | None = None):
        if branch is None:
            try:
                branch = self.git.current_branch()
            except Exception:
                return
        self.commit_list.clear()
        self.diff_view.setPlainText("")
        self.worker = Worker(self.git.list_commits, branch, 200)
        self.worker.done.connect(self._on_commits_loaded)
        self.worker.start()

    def _on_commits_loaded(self, result, error):
        if error:
            self._error(self.language_wrapper_get("err_load_commits"), error)
            return
        for c in result:
            self.commit_list.addItem(f"{c['hexsha'][:8]}  {c['date']}  {c['author']}  {c['summary']}")
        self.commit_list.setProperty("commit_data", result)

    def on_checkout(self):
        branch = self.branch_combo.currentText()
        if not branch:
            return

        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_checkout"), err)
            else:
                self._refresh_branches()
                self._load_commits_async(branch)
                self._info(
                    self.language_wrapper_get("info_checkout_title"),
                    f"{self.language_wrapper_get('info_checkout_msg')} {branch}"
                )
        self.worker = Worker(self.git.checkout, branch)
        self.worker.done.connect(after)
        self.worker.start()

    def on_commit_selected(self):
        items = self.commit_list.selectedIndexes()
        if not items:
            return
        idx = items[0].row()
        data = self.commit_list.property("commit_data") or []
        if idx >= len(data):
            return
        sha = data[idx]["hexsha"]

        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_read_diff"), err)
            else:
                self.diff_view.setPlainText(res)

        self.worker = Worker(self.git.show_diff_of_commit, sha)
        self.worker.done.connect(after)
        self.worker.start()

    def on_stage_all(self):
        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_stage"), err)
            else:
                self._info(self.language_wrapper_get("info_stage_title"), self.language_wrapper_get("info_stage_msg"))

        self.worker = Worker(self.git.stage_all)
        self.worker.done.connect(after)
        self.worker.start()

    def on_commit(self):
        msg = self.msg_edit.text()

        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_commit"), err)
            else:
                self.msg_edit.clear()
                self._load_commits_async()
                self._info(self.language_wrapper_get("info_commit_title"), self.language_wrapper_get("info_commit_msg"))

        self.worker = Worker(self.git.commit, msg)
        self.worker.done.connect(after)
        self.worker.start()

    def on_pull(self):
        remote = self.remote_combo.currentText() or self.language_wrapper_get("default_remote")
        branch = self.branch_combo.currentText()

        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_pull"), err)
            else:
                self._load_commits_async()
                self._info(self.language_wrapper_get("info_pull_title"), str(res))

        self.worker = Worker(self.git.pull, remote, branch)
        self.worker.done.connect(after)
        self.worker.start()

    def on_push(self):
        remote = self.remote_combo.currentText() or self.language_wrapper_get("default_remote")
        branch = self.branch_combo.currentText()

        def after(res, err):
            if err:
                self._error(self.language_wrapper_get("err_push"), err)
            else:
                self._info(self.language_wrapper_get("info_push_title"), str(res))

        self.worker = Worker(self.git.push, remote, branch)
        self.worker.done.connect(after)
        self.worker.start()

    def _on_clone_remote_repo(self):
        """
        UI handler for cloning a remote repository.
        """
        url, ok = QInputDialog.getText(self,
                                       self.language_wrapper_get("dialog_clone_title"),
                                       self.language_wrapper_get("dialog_clone_prompt"))
        if not ok or not url.strip():
            return

        local_dir = QFileDialog.getExistingDirectory(self, self.language_wrapper_get("dialog_select_folder"))
        if not local_dir:
            return

        try:
            repo_path = self.clone_handler.clone_repo(url.strip(), local_dir)
            self.git.open_repo(repo_path)
            QMessageBox.information(self,
                                    self.language_wrapper_get("info_clone_success_title"),
                                    f"{self.language_wrapper_get('info_clone_success_msg')} {repo_path}")
        except Exception as e:
            QMessageBox.critical(self, self.language_wrapper_get("err_clone_failed_title"), str(e))

