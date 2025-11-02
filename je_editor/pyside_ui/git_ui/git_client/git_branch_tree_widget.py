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
from je_editor.pyside_ui.git_ui.git_client.commit_table import CommitTable
from je_editor.pyside_ui.git_ui.git_client.graph_view import CommitGraphView
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class GitTreeViewGUI(QWidget):
    """
    GitTreeViewGUI: Git 提交歷史圖形化檢視器
    GitTreeViewGUI: A graphical viewer for Git commit history
    """

    def __init__(self):
        super().__init__()
        self.language_wrapper_get = language_wrapper.language_word_dict.get
        self.setWindowTitle(self.language_wrapper_get("git_graph_title"))

        # === 主版面配置 / Main layout ===
        git_treeview_main_layout = QVBoxLayout(self)
        git_treeview_main_layout.setContentsMargins(0, 0, 0, 0)
        git_treeview_main_layout.setSpacing(0)

        # === 工具列 / Toolbar ===
        git_treeview_toolbar = QToolBar()

        # 開啟 Git 專案動作 / Action to open Git repo
        open_repo_action = QAction(self.language_wrapper_get("git_graph_toolbar_open"), self)
        open_repo_action.triggered.connect(self.open_repo)
        git_treeview_toolbar.addAction(open_repo_action)

        # 刷新圖表動作 / Action to refresh graph
        act_refresh = QAction(self.language_wrapper_get("git_graph_toolbar_refresh"), self)
        act_refresh.triggered.connect(self.refresh_graph)
        git_treeview_toolbar.addAction(act_refresh)

        git_treeview_main_layout.addWidget(git_treeview_toolbar)

        # === 分割器 (左：圖形檢視 / 右：提交表格) ===
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.graph_view = CommitGraphView()  # 提交圖形檢視器 / commit graph view
        self.commit_table = CommitTable()  # 提交表格 / commit table
        splitter.addWidget(self.graph_view)
        splitter.addWidget(self.commit_table)
        splitter.setSizes([600, 400])  # 左右比例 / left-right ratio
        git_treeview_main_layout.addWidget(splitter, 1)  # stretch=1 表示可伸縮

        # === 狀態列 / Status bar ===
        self.status = QStatusBar()
        git_treeview_main_layout.addWidget(self.status)

        # === Git 相關屬性 ===
        self.repo_path = None
        self.git = None

        # === 檔案監控器 / File system watcher ===
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._on_git_changed)
        self.watcher.fileChanged.connect(self._on_git_changed)

        # === 定時器 (延遲刷新) / Timer for delayed refresh ===
        self.refresh_timer = QTimer()
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.refresh_graph)

        # === 表格選擇事件 / Table selection event ===
        self.commit_table.selectionModel().selectionChanged.connect(self._on_table_selection)

    def _on_table_selection(self, selected, _):
        """
        當使用者在提交表格中選擇某一列時，讓圖形檢視器聚焦到該行
        When user selects a row in commit table, focus graph view on that row
        """
        if not selected.indexes():
            return
        row = selected.indexes()[0].row()
        self.graph_view.focus_row(row)

    def open_repo(self):
        """
        開啟 Git 專案並初始化圖形檢視
        Open a Git repository and set up the graph view
        """
        path = QFileDialog.getExistingDirectory(self, self.language_wrapper_get("git_graph_menu_open_repo"))
        if not path:
            return
        repo_path = Path(path)
        git = GitCLI(repo_path)
        if not git.is_git_repo():
            # 若不是 Git 專案，顯示警告
            # Show warning if not a Git repo
            QMessageBox.warning(self, self.language_wrapper_get("git_graph_title"),
                                self.language_wrapper_get("git_graph_error_not_git"))
            return
        self.repo_path = repo_path
        self.git = git
        self._setup_watcher()
        self.refresh_graph()

    def _setup_watcher(self):
        """
        設定檔案監控，監控 .git 目錄與相關檔案
        Setup file watcher to monitor .git directory and related files
        """
        self.watcher.removePaths(self.watcher.files())
        self.watcher.removePaths(self.watcher.directories())
        if not self.repo_path:
            return
        git_dir = self.repo_path / ".git_client"  # ⚠️ 這裡應該是 ".git"，可能是自訂路徑
        if git_dir.exists():
            self.watcher.addPath(str(git_dir))
            for f in ["HEAD", "packed-refs"]:
                fp = git_dir / f
                if fp.exists():
                    self.watcher.addPath(str(fp))
            refs_dir = git_dir / "refs"
            if refs_dir.exists():
                self.watcher.addPath(str(refs_dir))

    def _on_git_changed(self):
        """
        當 Git 目錄變更時，啟動延遲刷新
        When Git directory changes, start delayed refresh
        """
        self.refresh_timer.start(500)

    def refresh_graph(self):
        """
        刷新 Git 提交圖與提交表格
        Refresh Git commit graph and commit table
        """
        if not self.git:
            return
        try:
            refs = self.git.get_all_refs()  # 取得所有 refs
            commits = self.git.get_commits(max_count=500)  # 取得最近 500 筆提交
            graph = CommitGraph()
            graph.build(commits, refs)  # 建立提交圖
            self.graph_view.set_graph(graph)  # 更新圖形檢視
            self.commit_table.set_commits(commits)  # 更新提交表格
        except Exception as e:
            QMessageBox.critical(self, self.language_wrapper_get("git_graph_title"),
                                 f"{self.language_wrapper_get('git_graph_error_exec_failed')}\n{e}")
