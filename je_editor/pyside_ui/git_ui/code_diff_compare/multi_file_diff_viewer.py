from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from je_editor.pyside_ui.git_ui.code_diff_compare.side_by_side_diff_widget import SideBySideDiffWidget


class MultiFileDiffViewer(QWidget):
    """
    Multi-file diff viewer using tabs to display each file.
    多檔案差異檢視器，使用分頁 (tab) 來顯示每個檔案的差異。
    """

    def __init__(self, parent=None):
        """
        Initialize the multi-file diff viewer.
        初始化多檔案差異檢視器。
        """
        super().__init__(parent)
        # Tab widget to hold each file's diff
        # 用來存放每個檔案差異的分頁元件
        self.tabs = QTabWidget()

        # Layout: vertical box with only the tab widget
        # 版面配置：垂直佈局，僅包含分頁元件
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)

    def set_diff_text(self, diff_text: str):
        """
        Set the diff text and split it into per-file tabs.
        設定差異文字，並依檔案拆分成多個分頁。
        """
        self.tabs.clear()
        file_diffs = self._split_by_file(diff_text)
        for file_name, ftext in file_diffs:
            viewer = SideBySideDiffWidget()   # 每個檔案使用 side-by-side viewer
            viewer.set_diff_text(ftext)
            self.tabs.addTab(viewer, file_name)  # 新增分頁，標題為檔名

    def _split_by_file(self, diff_text: str):
        """
        Split a unified diff text into chunks per file.
        將 unified diff 文字依檔案切分。
        """
        chunks = []
        current = []
        file_name = None

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                # 如果遇到新的檔案 diff，先把前一個檔案的內容存起來
                if current and file_name:
                    chunks.append((file_name, "\n".join(current)))
                    current = []
                # 解析檔名，格式通常為 "diff --git a/file b/file"
                parts = line.split()
                if len(parts) >= 4:
                    file_name = parts[2][2:]  # 去掉 "a/"
                else:
                    file_name = "unknown"
                current.append(line)
            else:
                current.append(line)

        # 最後一個檔案也要加入結果
        if current and file_name:
            chunks.append((file_name, "\n".join(current)))

        return chunks

    def set_dark_theme(self):
        """
        Apply dark theme to all tabs.
        對所有分頁套用深色主題。
        """
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, SideBySideDiffWidget):
                w.set_dark_theme()

    def set_light_theme(self):
        """
        Apply light theme to all tabs.
        對所有分頁套用淺色主題。
        """
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, SideBySideDiffWidget):
                w.set_light_theme()