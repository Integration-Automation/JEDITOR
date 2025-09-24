import logging
from pathlib import Path

from PySide6.QtCore import QTimer, QFileSystemWatcher, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog, QToolBar, QMessageBox, QStatusBar,
    QSplitter, QWidget, QVBoxLayout
)

from je_editor.git_client.commit_graph import CommitGraph
from je_editor.git_client.git_cli import GitCLI
from je_editor.pyside_ui.git_ui.commit_table import CommitTable
from je_editor.pyside_ui.git_ui.graph_view import CommitGraphView
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class GitTreeViewGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.language_wrapper_get = language_wrapper.language_word_dict.get
        self.setWindowTitle(self.language_wrapper_get("git_graph_title"))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = QToolBar()
        act_open = QAction(self.language_wrapper_get("git_graph_toolbar_open"), self)
        act_open.triggered.connect(self.open_repo)
        toolbar.addAction(act_open)

        act_refresh = QAction(self.language_wrapper_get("git_graph_toolbar_refresh"), self)
        act_refresh.triggered.connect(self.refresh_graph)
        toolbar.addAction(act_refresh)

        main_layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.graph_view = CommitGraphView()
        self.commit_table = CommitTable()
        splitter.addWidget(self.graph_view)
        splitter.addWidget(self.commit_table)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter, 1)  # 1 表示可伸縮

        self.status = QStatusBar()
        main_layout.addWidget(self.status)

        self.repo_path = None
        self.git = None

        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._on_git_changed)
        self.watcher.fileChanged.connect(self._on_git_changed)

        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.refresh_graph)

        self.commit_table.selectionModel().selectionChanged.connect(self._on_table_selection)

    def _on_table_selection(self, selected, _):
        if not selected.indexes():
            return
        row = selected.indexes()[0].row()
        self.graph_view.focus_row(row)

    def open_repo(self):
        path = QFileDialog.getExistingDirectory(self, self.language_wrapper_get("git_graph_menu_open_repo"))
        if not path:
            return
        repo_path = Path(path)
        git = GitCLI(repo_path)
        if not git.is_git_repo():
            QMessageBox.warning(self, self.language_wrapper_get("git_graph_title"),
                                self.language_wrapper_get("git_graph_error_not_git"))
            return
        self.repo_path = repo_path
        self.git = git
        self._setup_watcher()
        self.refresh_graph()

    def _setup_watcher(self):
        self.watcher.removePaths(self.watcher.files())
        self.watcher.removePaths(self.watcher.directories())
        if not self.repo_path:
            return
        git_dir = self.repo_path / ".git_client"
        if git_dir.exists():
            self.watcher.addPath(str(git_dir))
            for f in ["HEAD", "packed-refs"]:
                fp = git_dir / f
                if fp.exists():
                    self.watcher.addPath(str(fp))
            refs_dir = git_dir / "refs"
            if refs_dir.exists():
                self.watcher.addPath(str(refs_dir))

    def _on_git_changed(self, path):
        self.refresh_timer.start(500)

    def refresh_graph(self):
        if not self.git:
            return
        try:
            refs = self.git.get_all_refs()
            commits = self.git.get_commits(max_count=500)
            graph = CommitGraph()
            graph.build(commits, refs)
            self.graph_view.set_graph(graph)
            self.commit_table.set_commits(commits)
        except Exception as e:
            QMessageBox.critical(self, self.language_wrapper_get("git_graph_title"),
                                 f"{self.language_wrapper_get('git_graph_error_exec_failed')}\n{e}")

