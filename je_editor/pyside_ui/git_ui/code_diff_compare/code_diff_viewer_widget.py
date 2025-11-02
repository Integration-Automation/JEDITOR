from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMenuBar, QFileDialog, QMessageBox
)
from git import Repo

from je_editor.pyside_ui.git_ui.code_diff_compare.multi_file_diff_viewer import MultiFileDiffViewer


class DiffViewerWidget(QWidget):
    """
    Git Diff Viewer Application
    Git 差異檢視器應用程式
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Git Diff Viewer")

        # === Main diff viewer widget / 主要的差異檢視元件 ===
        self.viewer = MultiFileDiffViewer()

        # === Menu bar / 選單列 ===
        self.menubar = QMenuBar(self)
        file_menu = self.menubar.addMenu("File")  # File 選單
        view_menu = self.menubar.addMenu("View")  # View 選單

        # --- File → Open Git Repo ---
        # Action to open a Git repository
        # 開啟 Git 專案的動作
        open_repo_action = QAction("Open Git Repo", self)
        open_repo_action.triggered.connect(self.open_repo)
        file_menu.addAction(open_repo_action)

        # === View → Theme switching (exclusive) / 主題切換（單選模式） ===
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)  # 確保只能選擇一個主題 / ensure only one theme can be selected

        dark_action = QAction("Dark Mode", self, checkable=True)  # 深色模式 / dark mode
        light_action = QAction("Light Mode", self, checkable=True)  # 淺色模式 / light mode

        theme_group.addAction(dark_action)
        theme_group.addAction(light_action)

        # Default to dark mode / 預設為深色模式
        dark_action.setChecked(True)
        self.viewer.set_dark_theme()

        # Connect theme actions / 綁定主題切換事件
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        light_action.triggered.connect(lambda: self.set_theme("light"))

        view_menu.addAction(dark_action)
        view_menu.addAction(light_action)

        # === Layout / 版面配置 ===
        layout = QVBoxLayout(self)
        layout.setMenuBar(self.menubar)  # 把選單列放在上方 / put menu bar at the top
        layout.addWidget(self.viewer)  # 把差異檢視器放在主要區域 / add diff viewer in main area

    def open_repo(self):
        """
        Open a Git repository and display its diff.
        開啟一個 Git 專案並顯示差異。
        """
        path = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if not path:
            return
        try:
            repo = Repo(path)  # 嘗試載入 Git 專案 / try to load Git repo
            diff_text = repo.git.diff()  # 取得差異文字 / get diff text
            if not diff_text.strip():
                # 如果沒有差異，顯示提示訊息 / show info if no changes
                QMessageBox.information(self, "Info", "No changes in repo.")
            else:
                # 如果有差異，顯示在 viewer 中 / show diff in viewer
                self.viewer.set_diff_text(diff_text)
        except Exception as e:
            # 如果開啟失敗，顯示錯誤訊息 / show error if failed
            QMessageBox.critical(self, "Error", f"Failed to open repo:\n{e}")

    def set_theme(self, mode: str):
        """
        Switch between dark and light themes.
        切換深色與淺色主題。
        """
        if mode == "dark":
            self.viewer.set_dark_theme()
        else:
            self.viewer.set_light_theme()
