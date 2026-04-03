"""
插件瀏覽器 Widget / Plugin Browser Widget

提供 UI 讓使用者瀏覽 GitHub Repo 上的插件，檢視資訊並下載到 jeditor_plugins/。
Provides a UI for browsing plugins on a GitHub repo, viewing info, and downloading to jeditor_plugins/.
"""
from __future__ import annotations

from pathlib import Path
from threading import Thread

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QTextEdit, QMessageBox,
    QHeaderView, QSplitter, QProgressBar,
)

from je_editor.pyside_ui.main_ui.plugin_browser.github_api import (
    fetch_repo_tree, fetch_plugin_metadata, download_plugin_file,
)
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 預設插件 Repo / Default plugin repo
_DEFAULT_REPO_URL = "https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins"


class _WorkerSignals(QObject):
    """用於背景執行緒回報結果的信號 / Signals for background thread results."""
    finished = Signal(list)       # 插件列表 / Plugin list
    metadata = Signal(dict)       # 插件元資料 / Plugin metadata
    error = Signal(str)           # 錯誤訊息 / Error message
    download_done = Signal(str)   # 下載完成路徑 / Download done path


class PluginBrowserWidget(QWidget):
    """
    插件瀏覽器主 Widget。
    Plugin browser main widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        jeditor_logger.info("Init PluginBrowserWidget")

        self._signals = _WorkerSignals()
        self._signals.finished.connect(self._on_plugins_loaded)
        self._signals.metadata.connect(self._on_metadata_loaded)
        self._signals.error.connect(self._on_error)
        self._signals.download_done.connect(self._on_download_done)

        self._plugins: list[dict] = []
        self._current_plugin: dict | None = None

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # === 頂部：Repo URL 輸入 ===
        # === Top: Repo URL input ===
        top_layout = QHBoxLayout()
        self._repo_label = QLabel(
            language_wrapper.language_word_dict.get("plugin_browser_repo_label", "Repository URL:"))
        self._repo_input = QLineEdit(_DEFAULT_REPO_URL)
        self._repo_input.setPlaceholderText("https://github.com/owner/repo")
        self._fetch_btn = QPushButton(
            language_wrapper.language_word_dict.get("plugin_browser_fetch_btn", "Fetch Plugins"))
        self._fetch_btn.clicked.connect(self._on_fetch_clicked)

        top_layout.addWidget(self._repo_label)
        top_layout.addWidget(self._repo_input, stretch=1)
        top_layout.addWidget(self._fetch_btn)
        main_layout.addLayout(top_layout)

        # === 進度條 ===
        # === Progress bar ===
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setVisible(False)
        main_layout.addWidget(self._progress)

        # === 中間：插件列表 + 詳細資訊 ===
        # === Middle: plugin list + detail ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側：插件樹狀清單 / Left: plugin tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels([
            language_wrapper.language_word_dict.get("plugin_browser_col_name", "Plugin"),
            language_wrapper.language_word_dict.get("plugin_browser_col_path", "Path"),
            language_wrapper.language_word_dict.get("plugin_browser_col_size", "Size"),
        ])
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.currentItemChanged.connect(self._on_item_selected)
        splitter.addWidget(self._tree)

        # 右側：詳細資訊面板 / Right: detail panel
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(4, 4, 4, 4)

        self._detail_title = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._detail_title.setFont(title_font)
        detail_layout.addWidget(self._detail_title)

        self._detail_info = QLabel()
        self._detail_info.setWordWrap(True)
        detail_layout.addWidget(self._detail_info)

        self._detail_text = QTextEdit()
        self._detail_text.setReadOnly(True)
        self._detail_text.setPlaceholderText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_select_hint", "Select a plugin to view details"))
        detail_layout.addWidget(self._detail_text, stretch=1)

        # 下載按鈕 / Download button
        btn_layout = QHBoxLayout()
        self._download_btn = QPushButton(
            language_wrapper.language_word_dict.get("plugin_browser_download_btn", "Download && Install"))
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download_clicked)
        btn_layout.addStretch()
        btn_layout.addWidget(self._download_btn)
        detail_layout.addLayout(btn_layout)

        splitter.addWidget(detail_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter, stretch=1)

        # === 底部：狀態列 ===
        # === Bottom: status bar ===
        self._status = QLabel(
            language_wrapper.language_word_dict.get(
                "plugin_browser_status_ready", "Ready"))
        main_layout.addWidget(self._status)

    # ----- Actions / 動作 -----

    def _on_fetch_clicked(self):
        """使用者按下 Fetch 按鈕 / User clicks Fetch button."""
        repo_url = self._repo_input.text().strip().rstrip("/")
        # 解析 owner/repo / Parse owner/repo
        # 支援格式: https://github.com/owner/repo 或 owner/repo
        # Supports: https://github.com/owner/repo or owner/repo
        if "github.com/" in repo_url:
            parts = repo_url.split("github.com/")[1].split("/")
        else:
            parts = repo_url.split("/")

        if len(parts) < 2:
            self._on_error(language_wrapper.language_word_dict.get(
                "plugin_browser_invalid_url", "Invalid repository URL"))
            return

        owner, repo = parts[0], parts[1]
        self._set_loading(True)
        self._status.setText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_status_fetching", "Fetching plugin list..."))
        self._tree.clear()
        self._plugins.clear()

        Thread(target=self._fetch_worker, args=(owner, repo), daemon=True).start()

    def _fetch_worker(self, owner: str, repo: str):
        """背景取得插件列表 / Background fetch plugin list."""
        try:
            plugins = fetch_repo_tree(owner, repo)
            # 為每個插件取得元資料 / Fetch metadata for each plugin
            for plugin in plugins:
                url = plugin.get("download_url", "")
                if url:
                    meta = fetch_plugin_metadata(url)
                    plugin.update(meta)
            self._signals.finished.emit(plugins)
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_plugins_loaded(self, plugins: list[dict]):
        """插件列表載入完成 / Plugin list loaded."""
        self._set_loading(False)
        self._plugins = plugins

        # 按目錄分群 / Group by directory
        groups: dict[str, list[dict]] = {}
        for p in plugins:
            parts = p["path"].split("/")
            group = parts[0] if len(parts) > 1 else ""
            groups.setdefault(group, []).append(p)

        self._tree.clear()
        for group_name, group_plugins in sorted(groups.items()):
            if group_name:
                # 有目錄的分群 / Grouped under directory
                group_item = QTreeWidgetItem(self._tree, [group_name, "", ""])
                group_item.setExpanded(True)
                for p in sorted(group_plugins, key=lambda x: x["name"]):
                    display = p.get("PLUGIN_NAME", p["name"])
                    child = QTreeWidgetItem(group_item, [
                        display, p["path"], f'{p["size"]} B'
                    ])
                    child.setData(0, Qt.ItemDataRole.UserRole, p)
            else:
                # 根目錄的檔案 / Root-level files
                for p in sorted(group_plugins, key=lambda x: x["name"]):
                    display = p.get("PLUGIN_NAME", p["name"])
                    item = QTreeWidgetItem(self._tree, [
                        display, p["path"], f'{p["size"]} B'
                    ])
                    item.setData(0, Qt.ItemDataRole.UserRole, p)

        count = len(plugins)
        self._status.setText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_status_loaded", "Loaded {count} plugins").format(count=count))

    def _on_item_selected(self, current: QTreeWidgetItem, _previous):
        """使用者選取插件 / User selects a plugin."""
        if current is None:
            return
        plugin = current.data(0, Qt.ItemDataRole.UserRole)
        if plugin is None:
            # 群組節點 / Group node
            self._download_btn.setEnabled(False)
            self._detail_title.setText("")
            self._detail_info.setText("")
            self._detail_text.setPlainText("")
            return

        self._current_plugin = plugin
        self._download_btn.setEnabled(True)

        name = plugin.get("PLUGIN_NAME", plugin["name"])
        author = plugin.get("PLUGIN_AUTHOR", "")
        version = plugin.get("PLUGIN_VERSION", "")

        self._detail_title.setText(name)
        info_parts = []
        if version:
            info_parts.append(f"Version: {version}")
        if author:
            info_parts.append(f"Author: {author}")
        info_parts.append(f"File: {plugin['name']}")
        info_parts.append(f"Path: {plugin['path']}")
        self._detail_info.setText("\n".join(info_parts))

        # 顯示「載入原始碼…」並背景下載 / Show "loading source..." and fetch in background
        self._detail_text.setPlainText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_loading_source", "Loading source code..."))

        Thread(
            target=self._fetch_source_worker,
            args=(plugin.get("download_url", ""),),
            daemon=True,
        ).start()

    def _fetch_source_worker(self, url: str):
        """背景下載原始碼預覽 / Background fetch source preview."""
        try:
            from je_editor.pyside_ui.main_ui.plugin_browser.github_api import _download_text
            source = _download_text(url)
            self._signals.metadata.emit({"_source": source})
        except Exception as e:
            self._signals.metadata.emit({"_source": f"Error: {e}"})

    def _on_metadata_loaded(self, data: dict):
        """原始碼預覽載入完成 / Source preview loaded."""
        source = data.get("_source", "")
        self._detail_text.setPlainText(source)

    def _on_download_clicked(self):
        """使用者按下下載按鈕 / User clicks download button."""
        if self._current_plugin is None:
            return

        plugin = self._current_plugin
        download_url = plugin.get("download_url", "")
        file_name = plugin["name"]

        if not download_url:
            self._on_error("No download URL available")
            return

        # 直接下載到 jeditor_plugins/ 根目錄
        # Download directly to jeditor_plugins/ root
        dest_dir = self._get_plugins_dir()
        installed = dest_dir / file_name

        # 確認下載 / Confirm download
        if installed.exists():
            reply = QMessageBox.question(
                self,
                language_wrapper.language_word_dict.get(
                    "plugin_browser_overwrite_title", "Plugin exists"),
                language_wrapper.language_word_dict.get(
                    "plugin_browser_overwrite_msg",
                    "{name} already exists. Overwrite?").format(name=file_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._set_loading(True)
        self._download_btn.setEnabled(False)
        self._status.setText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_status_downloading", "Downloading {name}...").format(name=file_name))

        Thread(
            target=self._download_worker,
            args=(download_url, str(dest_dir), file_name),
            daemon=True,
        ).start()

    def _download_worker(self, url: str, dest_dir: str, file_name: str):
        """背景下載插件 / Background download plugin."""
        try:
            saved = download_plugin_file(url, dest_dir, file_name)
            self._signals.download_done.emit(saved)
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_download_done(self, saved_path: str):
        """下載完成 / Download complete."""
        self._set_loading(False)
        self._download_btn.setEnabled(True)
        self._status.setText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_status_installed", "Installed: {path}").format(path=saved_path))

        msg = QMessageBox(self)
        msg.setWindowTitle(
            language_wrapper.language_word_dict.get("plugin_browser_download_btn", "Download & Install"))
        msg.setText(
            language_wrapper.language_word_dict.get(
                "plugin_browser_restart_hint",
                "Plugin downloaded to:\n{path}\n\nPlease restart the editor to activate."
            ).format(path=saved_path))
        msg.exec()

    def _on_error(self, error_msg: str):
        """顯示錯誤 / Show error."""
        jeditor_logger.error(f"PluginBrowserWidget error: {error_msg}")
        self._set_loading(False)
        self._status.setText(f"Error: {error_msg}")

    # ----- Helpers -----

    def _set_loading(self, loading: bool):
        """切換載入狀態 / Toggle loading state."""
        self._progress.setVisible(loading)
        self._fetch_btn.setEnabled(not loading)

    @staticmethod
    def _get_plugins_dir() -> Path:
        """
        取得 jeditor_plugins/ 目錄路徑，若不存在則建立。
        Get jeditor_plugins/ directory path, create if not exists.
        """
        plugins_dir = Path.cwd() / "jeditor_plugins"
        plugins_dir.mkdir(exist_ok=True)
        return plugins_dir
