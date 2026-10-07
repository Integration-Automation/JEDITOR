# PROGRESS：JEditor 待辦

只放還沒做的事。做完就在同一個 commit 裡刪掉這條，並在 `docs/updates/` 新增一筆 `#done` 紀錄（格式與查詢方式見 `docs/updates/README.md`）。不放已完成的項目、不寫流水帳、不寫規則（規則在 `CLAUDE.md`）。
本檔納入版控。PyBreeze 的待辦寫在 PyBreeze 自己的 `progress.md`。
編號 `#n` 不重用。標記：〔決定〕需擁有者拍板、〔阻塞〕在等別的事、〔未確認〕觀察到但還沒證實。
跨專案與工作區層級的待辦在 `D:\Codes\progress.md`（與本專案相關：X-16、X-17）。

## 待辦

- **#1** SonarCloud 的 S125 是誤判，需要在網站上標記：`extend_system_tray.py:27` 的
  `# 初始化並記錄日誌` 被當成「註解掉的程式碼」。這是本專案雙語註解的正常寫法，不該刪。
  要清掉這一項得在 SonarCloud 把 issue 轉成 False Positive（用 API 改狀態需要 Administer
  Issues 權限）。
- **#18** 〔決定〕`ruff` 沒有釘版本、repo 也沒有 ruff 設定，而 ruff 0.16 的預設規則從 118 條變成
  826 條。2026-10-08 用 ruff 0.16.10 跑 `ruff check`：全 repo 526 筆（`I001` 匯入排序 276、`UP006` 93、
  `UP035` 35、`RUF100` 27、`UP045` 23、`BLE001` 22…，449 筆可自動修正）；同一份程式碼用 ruff 0.15.8，
  或用 0.16.10 加 `--select E4,E7,E9,F`（舊的預設），都是乾淨的。要選一個：釘 `ruff<0.16`、在
  `pyproject.toml` 寫明規則，或整個 repo 照新規則修一輪。`je_editor/core/` 與它的測試在新規則下只剩
  `I001`（9 筆，寫法跟現有程式碼一致）與 `RUF022`（1 筆，`__all__` 依主題分組）。
- **#19** 〔未確認〕`test_file_scan.py::TestIndexProjectFiles::test_depth_limit_prunes_deep_trees` 在沒有
  開啟長路徑的 Windows（`LongPathsEnabled = 0`）上失敗：`deep.mkdir()` 丟 `WinError 206`，建出來的目錄樹
  超過 260 字元。2026-10-08 在 `da90c4f` 的乾淨工作樹上同樣失敗，所以跟當時的修改無關；CI 與原本的
  開發機沒有這個問題。要不要讓測試不依賴長路徑設定，還沒看。
- **#20** 〔未確認〕pytest 9.1 對「class 範圍的 fixture 寫成實例方法」發出 `PytestRemovedIn10Warning`，
  `test_logging_hygiene.py` 的 `probe_result` 是這種寫法，pytest 10 會變成錯誤。

### 下一代編輯器藍圖（`docs/roadmap/2026-editor-next.md`，PR #270）

M0（`je_editor/core/` 服務層）已完成，見 U-20261008-01。以下每個里程碑一個 PR，順序依相依關係；
#13 只相依 M0，可以先做。

- **#9** M1（UI 重新設計、指令與快捷鍵、語系補齊）。可以先做不改變外觀的部分：每個指令有不隨翻譯
  變動的 ID。語系那一項大部分已經有了：四份字典各 438 個鍵，鍵與佔位符的 parity、空白值、退回英文都
  由 `test/test_languages.py` 在 CI 守著；還沒做的是「語系載入改成資料驅動」。〔決定〕UI 的版面方向
  （活動列、編輯區、側邊面板、底部面板）要先定，才能動視窗層。
- **#10** M2（Tree-sitter、統一診斷）。問題面板、底線、縮圖改用 `core/diagnostics`（現在靠
  `legacy_diagnostics.py` 互轉）；`utils/lsp/lsp_protocol.diagnostic_entries` 沒有帶出伺服器給的
  嚴重度，要補上；`LanguageService` 的「發問、等回覆」呼叫形式在這裡定。
- **#11** M3（工作區與多根專案）。`EditorMain` 持有 `EditorServices`，`working_dir` 改由 `Workspace`
  提供；LSP 連線以「伺服器 + 根目錄」為鍵；搜尋、索引、TODO、Git、診斷改成認得工作區。
- **#12** M4（除錯器改走 DAP）。實作 `DebugSession`；堆疊、變數、求值的非同步查詢形式在這裡定；
  需要一個本機的 `TaskRunner` 實作來啟動轉接器。
- **#13** M5（AI 供應者 + Anthropic）。`LangChainInterface` 改成 `AIProvider` 的實作並新增
  Anthropic；設定改成依供應者分組。
- **#14** M6（遠端開發）。實作 `RemoteSession`，並補上遠端檔案系統、連接埠轉送、直譯器探索的介面。
  〔決定〕第一個傳輸是不是 SSH（PR #270 的審查問題 3）。
- **#15** M7（可嵌入元件）。`import je_editor.core` 不再載入 Qt（頂層 `__init__` 要改成延後匯入）；
  搬動 `pyside_ui/` 底下不含 Qt 的模組時，保留 PyBreeze 以模組路徑匯入的名稱
  （`test/test_public_api_contract.py` 列著）。
- **#16** M8（教學文件）。相依 M7。
- **#17** 〔決定〕PR #270 的審查問題 1、5 還沒有答覆：里程碑是否都以 `dev` 為整合分支、哪些里程碑要
  另開追蹤 issue。M0 目前直接提交在 PR #270 的分支 `roadmap/editor-next` 上；PR 的描述仍寫著
  「這個 PR 不含實作」，要改。
