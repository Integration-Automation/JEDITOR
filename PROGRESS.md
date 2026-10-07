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
- **#21** 〔未確認〕整套測試在機器忙碌時偶爾被 Qt 中止（`Fatal Python error: Aborted`，結束代碼 3）。
  2026-10-08 看到兩次，都是主工作樹裡同時還有別的 pytest 行程在跑的時候；其中一次留有紀錄，停在
  `test_toolbar_actions.py::TestTheBranchScan::test_a_subdirectory_still_finds_the_repository` 的 setup，
  pytest-qt 的 `_process_events` 裡。在獨立的工作樹各跑三次（`132246e` 與診斷那次修改）六次都通過，
  所以不是那次修改造成的。還沒用 `pytest -s` 抓到 Qt 的訊息，不知道是哪個物件。

### 下一代編輯器藍圖（`docs/roadmap/2026-editor-next.md`，PR #270）

M0（`je_editor/core/` 服務層）、M2（診斷模型與 Tree-sitter 語法引擎）、M3（工作區與多根專案）、M5（AI 供應者）已完成，見 `docs/updates/2026-10.md`。
以下依相依關係排序。

- **#9** M1（UI 重新設計、指令與快捷鍵、語系補齊）。可以先做不改變外觀的部分：每個指令有不隨翻譯
  變動的 ID。語系那一項大部分已經有了：四份字典的鍵與佔位符的 parity、空白值、退回英文都
  由 `test/test_languages.py` 在 CI 守著；還沒做的是「語系載入改成資料驅動」。〔決定〕UI 的版面方向
  （活動列、編輯區、側邊面板、底部面板）要先定，才能動視窗層。
- **#23** M2 沒有涵蓋的部分（語法引擎與高亮已完成，見 U-20261008-08）：語法樹目前只用來上色。大綱
  （`utils/symbols`）、折疊（`utils/code_folding`）與智慧選取（`utils/selection`）仍然用各自的分析，
  還沒有改用 `SyntaxSession.regions()`；編輯器是直接向引擎要 session，沒有經過 `DocumentStore`，
  所以 `SyntaxLanguageService` 只有宿主程式自己開文件時才用得到；`LspClient` 也還沒有包成
  `LanguageService`。支援的語言只有 Python、JavaScript、JSON，其餘仍用關鍵字表。
- **#24** 升級 `tree-sitter` 之前要重新確認：0.26.0 的 `Point.row` / `Point.column` 每讀一次就少算
  那個整數一次參考（Python 3.11 上讀幾萬次後行程當掉），引擎因此一律以索引讀取位置，
  `test_syntax_engine.py::TestTheBindingIsUsedSafely` 守著。這個問題還沒有回報給上游（這台機器沒有
  `gh`）。另外 `tree-sitter-json` 0.24.8 自帶的高亮查詢是照「先寫的規則優先」排的，跟 Python、
  JavaScript 的文法相反，所以 `queries/json/highlights.scm` 重新指定了鍵；文法升級後可能不再需要。
- **#22** M3 沒有涵蓋的部分（工作區本身已完成，見 U-20261008-07）：執行程式、測試面板、終端機、Git
  工具列與 Python 直譯器（venv）仍然只認主要的根目錄，也就是工作目錄。藍圖要的「每個根目錄有自己的
  語言 / 工具設定與環境」還沒做；Git 面板也還沒有依根目錄切換。
- **#12** M4（除錯器改走 DAP）。實作 `DebugSession`；堆疊、變數、求值的非同步查詢形式在這裡定；
  需要一個本機的 `TaskRunner` 實作來啟動轉接器。
- **#14** M6（遠端開發）。實作 `RemoteSession`，並補上遠端檔案系統、連接埠轉送、直譯器探索的介面。
  〔決定〕第一個傳輸是不是 SSH（PR #270 的審查問題 3）。
- **#15** M7（可嵌入元件）。`import je_editor.core` 不再載入 Qt（頂層 `__init__` 要改成延後匯入）；
  搬動 `pyside_ui/` 底下不含 Qt 的模組時，保留 PyBreeze 以模組路徑匯入的名稱
  （`test/test_public_api_contract.py` 列著）。
- **#16** M8（教學文件）。相依 M7。
- **#17** 〔決定〕PR #270 的審查問題 1、5 還沒有答覆：里程碑是否都以 `dev` 為整合分支、哪些里程碑要
  另開追蹤 issue。M0 目前直接提交在 PR #270 的分支 `roadmap/editor-next` 上；PR 的描述仍寫著
  「這個 PR 不含實作」，要改。
