# JEditor 架構導覽 / Architecture Exploration

> 產出時間：2026-08-03　對應版本：`dev` 分支（commit `f17e07a`）
> 涵蓋範圍：`je_editor/` 全部 277 個 `.py`（170 個實作模組 + 107 個 `__init__.py`），共 30,465 行。
> 這份文件記錄「每個模組負責什麼」與「模組之間怎麼串起來」，不是使用手冊（使用說明見 `README.md`、插件說明見 `PLUGIN_GUIDE.md`）。

---

## 1. 專案概觀

JEditor 是以 PySide6（Qt for Python）寫成的程式碼編輯器，功能涵蓋語法高亮、程式碼折疊、
多重游標、LSP、ruff 診斷、pytest 面板、Git 整合、內嵌瀏覽器、IPython 主控台與 LangChain AI 對話。

| 項目 | 內容 |
| --- | --- |
| 語言 / 版本 | Python 3.10+（CI 測 3.10 / 3.11 / 3.12） |
| UI 框架 | PySide6 6.11.0 + qt-material 主題 |
| 主要相依 | `jedi`（Python 補全）、`ruff`（診斷）、`yapf` / `pycodestyle`（格式化與檢查）、`gitpython`、`watchdog`、`qtconsole` + `IPython`、`langchain_openai` + `langchain_core`、`frontengine` |
| 測試 | pytest + pytest-qt，88 個測試檔、約 13,400 行 |
| 靜態分析 | ruff、SonarCloud（`sonar.sources=je_editor`）、Codacy、bandit |

### 各套件規模

| 套件 | 模組數 | 行數 | 定位 |
| --- | ---: | ---: | --- |
| `pyside_ui/` | 98 | 20,311 | View / Controller：所有 Qt 元件與選單 |
| `utils/` | 59 | 8,544 | 純邏輯層（絕大多數不 import Qt，可單獨測試） |
| `git_client/` | 6 | 777 | Git 操作（GitPython + git CLI 兩條路） |
| `code_scan/` | 4 | 365 | ruff 執行與 watchdog 檔案監看 |
| `plugins/` | 1 | 337 | 插件註冊表與外部插件載入器 |
| 頂層 | 2 | 131 | `__main__.py`、`start_editor.py`（另有 `__init__.py` 匯出公開 API） |

（行數含各層 `__init__.py`，合計 30,465 行。）

---

## 2. 分層與依賴方向

```
                    ┌──────────────────────────────────────────┐
     進入點          │ __main__.py  →  start_editor.py          │
                    └──────────────────┬───────────────────────┘
                                       │ 建 QApplication、載插件、套主題
                    ┌──────────────────▼───────────────────────┐
     視窗層          │ main_ui/main_editor.py  (EditorMain)     │
                    │  ├ menu/        選單列（10 個子選單）      │
                    │  ├ toolbar/     工具列 + Git 分支切換      │
                    │  ├ editor/      EditorWidget（分頁本體）   │
                    │  ├ *_panel/     problems / todo / test / outline
                    │  ├ command_palette/  指令面板、快速開啟     │
                    │  ├ ai_widget/ console_widget/ ipython_widget/
                    │  └ save_settings/    設定持久化            │
                    └──────────────────┬───────────────────────┘
                    ┌──────────────────▼───────────────────────┐
     編輯器層        │ code/plaintext_code_edit/CodeEditor      │
                    │  組合十多個 manager：folding / bookmark / │
                    │  lint / lsp / diff / blame / snippet /    │
                    │  multi_cursor / breakpoint / selection    │
                    └──────────────────┬───────────────────────┘
                    ┌──────────────────▼───────────────────────┐
     邏輯層          │ utils/（純函式與資料類別，不含 Qt）        │
                    │ code_scan/ · git_client/ · plugins/       │
                    └──────────────────────────────────────────┘

依賴方向由上而下；`utils/` 幾乎不反向依賴 UI（例外：`utils/session/editor_state.py`
以 duck typing 操作 widget、`utils/multi_language/locale_match.py` 讀 Qt 的 QLocale）。
```

**設計慣例**：幾乎每個功能都拆成「純邏輯 + Qt 整合層」兩塊。
例如折疊 = `utils/code_folding/fold_regions.py`（算區塊）+ `pyside_ui/code/folding/folding_manager.py`（藏行、重畫）；
書籤 = `utils/bookmark/bookmark_navigation.py` + `pyside_ui/code/bookmark/bookmark_manager.py`。
這讓大部分邏輯可以不開視窗就測試，也是 `test/` 能有 88 個測試檔的原因。

---

## 3. 啟動流程

```
start_editor(debug_mode)                       je_editor/start_editor.py
 ├ quiet_chromium_logging()                    壓掉 QtWebEngine 啟動訊息（stderr 會被導到輸出面板）
 ├ QApplication(sys.argv)                      沒有既有實例才建
 ├ load_external_plugins()                     掃 jeditor_plugins/ 並註冊
 ├ EditorMain(debug_mode)                      主視窗
 │   ├ read_user_setting()                     .jeditor/user_setting.json
 │   ├ language_wrapper.reset_language(...)    第一次啟動照系統語系挑
 │   ├ jedi.settings.fast_parser = False       避免執行緒問題
 │   ├ read_user_color_setting()               .jeditor/user_color_setting.json
 │   ├ QTabWidget 建立、set_menu_bar()、build_toolbar()
 │   ├ 狀態列四個標籤（語言 / 行尾 / 編碼 / 游標位置）
 │   ├ redirect_manager_instance.set_redirect() 接管 stdout / stderr
 │   ├ QTimer 50ms  → redirect()               把佇列內容寫進輸出區
 │   ├ QTimer 60s   → _periodic_save_settings() 防當機丟設定
 │   ├ 加入分頁：EditorWidget、瀏覽器（非 debug）、EDITOR_EXTEND_TAB
 │   └ startup_setting()                       套字型 / 樣式 / 顏色、還原上次分頁
 ├ apply_stylesheet(dark_amber.xml)
 ├ window.showMaximized()
 └ app.exec() → os._exit(ret)
```

`debug_mode=True` 時不建瀏覽器分頁（QWebEngine 在無頭 CI 起不來），並在 10 秒後自動關閉視窗。

---

## 4. 執行期的全域狀態

模組層級單例，跨模組共享。修改它們等於改全域狀態，測試時要注意還原。

| 物件 | 位置 | 用途 |
| --- | --- | --- |
| `user_setting_dict` | `main_ui/save_settings/user_setting_file.py` | 字型、語言、樣式、縮排、最近檔案、開啟分頁、快捷鍵覆寫 |
| `user_setting_color_dict` / `actually_color_dict` | `main_ui/save_settings/user_color_setting_file.py` | 使用者顏色設定（RGB list）與換算後的 `QColor` |
| `language_wrapper` | `utils/multi_language/multi_language_wrapper.py` | 目前語言的字典，所有介面文字都從這裡取 |
| `redirect_manager_instance` | `utils/redirect_manager/redirect_manager_class.py` | stdout / stderr 兩個 `queue.Queue` |
| `run_instance_manager` | `pyside_ui/code/running_process_manager.py` | 追蹤所有執行中的程式 / shell 實例，關閉時統一收掉 |
| `session_registry` | `pyside_ui/code/lsp/lsp_session.py` | 語言伺服器程序池，同語言的分頁共用一個程序 |
| `auto_save_manager_dict` / `file_is_open_manager_dict` | `pyside_ui/code/auto_save/auto_save_manager.py` | 自動儲存執行緒表、避免同檔重複開分頁 |
| `syntax_rule_setting_dict` 等三個 | `pyside_ui/code/syntax/syntax_setting.py` | Python 高亮的規則、關鍵字與插件擴充位 |
| `EDITOR_EXTEND_TAB` | `main_ui/main_editor.py` | 給下游專案（PyBreeze）塞自訂分頁的掛載點 |
| `_plugin_metadata_list` 等 | `plugins/__init__.py` | 已註冊的語言 / 翻譯 / 執行設定 / 中繼資料 |

---

## 5. 模組逐一說明

### 5.1 頂層

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `__init__.py` | 57 | 公開 API 匯總（`__all__`）：`start_editor`、`EditorMain`、`EditorWidget`、例外類別、語言字典、插件註冊函式 |
| `__main__.py` | 18 | `python -m je_editor -s` 的 argparse 進入點 |
| `start_editor.py` | 56 | 建 `QApplication`、載插件、套 qt-material 主題、最大化顯示、`os._exit` 收場 |

---

### 5.2 `utils/` — 純邏輯層（59 模組 / 8,544 行）

#### 文字與行操作

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `line_ops/line_operations.py` | 130 | 排序 / 去重 / 自然排序 / 反轉 / 去空行 / 合併行 / 刪行 |
| `align/align.py` | 48 | 依分隔符對齊多行的第一個分隔符 |
| `case_convert/case_convert.py` | 63 | snake / kebab / camel / Pascal 命名互轉（含縮寫切分） |
| `text_cleanup/text_cleanup.py` | 57 | 去行尾空白、確保結尾換行、去結尾空行 |
| `text_stats/text_statistics.py` | 54 | 行數 / 詞數 / 字元數統計 |
| `number_ops/number_ops.py` | 103 | 找游標處整數、加減、進位轉換（0x / 0o / 0b） |
| `encode_decode/encode_decode.py` | 123 | Base64 / URL / HTML 實體 / JSON 字串的編解碼 |
| `json_format/json_process.py` | 64 | JSON 重新排版 |
| `selection/smart_selection.py` | 100 | 由小到大的候選選取範圍（智慧擴大選取） |
| `selection/surround.py` | 45 | 以括號 / 引號包住選取文字 |
| `occurrence/word_occurrences.py` | 130 | 取游標處識別字、找出所有出現位置、整字取代 |
| `indentation/indent_convert.py` | 142 | Tab ↔ 空白互轉、偵測檔案的縮排寬度與型態 |
| `indentation/indent_guides.py` | 75 | 計算縮排參考線欄位與尾端空白起點 |

#### 檔案、編碼與工作階段

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `file/open/open_file.py` | 99 | 讀檔並回報實際編碼與原始行尾（thread lock 保護） |
| `file/save/save_file.py` | 97 | 依指定編碼與行尾寫檔 |
| `encodings/text_codec.py` | 143 | 行尾偵測 / 正規化 / 套用；BOM 判斷編碼；位元組解碼 |
| `encodings/python_encodings.py` | 102 | 編碼選單用的完整編碼名稱清單 |
| `json/json_file.py` | 68 | JSON 讀寫（含鎖與例外轉換） |
| `session/open_files_session.py` | 170 | 分頁工作階段序列化：要記哪些檔、還原時哪些還能開（上限 20 檔） |
| `session/editor_state.py` | 63 | 單一分頁的游標行、書籤、折疊狀態的取出與套回 |
| `file_scan/file_indexer.py` | 106 | 專案檔案索引（深度上限 24、檔案上限 20000），供快速開啟 |
| `file_scan/ignore_rules.py` | 73 | 掃描時共用的忽略規則（`.git`、`__pycache__`、二進位副檔名、null byte 偵測） |
| `file_scan/todo_scanner.py` | 138 | 掃描 TODO / FIXME 註解，支援多種註解符號 |
| `venv_check/check_venv.py` | 75 | 找出 venv 的 Python 執行檔路徑 |

#### 差異、Git 與診斷

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `file_diff/line_status.py` | 238 | 緩衝區 vs 基準的逐行狀態（新增 / 修改 / 上方刪除）、`Hunk` 切分、單段套用、上下個變更 |
| `file_diff/unified.py` | 46 | 產生 HEAD vs 工作區的 unified diff |
| `lint/ruff_diagnostics.py` | 226 | 解析 ruff JSON → `Diagnostic`；規則代碼推嚴重度；依行分組 |

#### 程式碼結構與語言

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `symbols/python_symbols.py` | 160 | 以 `ast` 萃取類別 / 函式 / 方法 / 模組層級變數 |
| `symbols/outline_tree.py` | 74 | 依限定名稱把符號組成巢狀大綱樹 |
| `code_folding/fold_regions.py` | 123 | 以縮排計算可折疊區塊（掃描上限 50000 行） |
| `code_folding/brace_regions.py` | 161 | 以大括號配對計算折疊區塊，會跳過字串與註解內容 |
| `syntax/language_rules.py` | 136 | 各語言的關鍵字 / 註解 / 字串規則表 |
| `lsp/lsp_protocol.py` | 454 | LSP 訊息編解碼：`MessageReader`、request / notification、completion / hover / definition / references / symbols / rename / diagnostics 的回應解析 |
| `lsp/language_servers.py` | 95 | 副檔名 → 伺服器指令對照，並併入使用者設定 |
| `test_runner/pytest_output.py` | 291 | 解析 pytest 輸出：每筆結果、失敗位置、traceback、覆蓋率、結尾統計 |
| `debugger/pdb_commands.py` | 105 | 組出 pdb 指令（設 / 清中斷點、step into/over/out） |
| `format_code/yapf_format.py` | 46 | 以 yapf（google style）格式化原始碼 |

#### 編輯器行為

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `multi_cursor/cursor_positions.py` | 163 | 多重游標位置的增刪、插入 / 刪除後的位移、欄選取換算 |
| `navigation/location_history.py` | 127 | 游標跳轉歷史（上一步 / 下一步，上限 50） |
| `bookmark/bookmark_navigation.py` | 79 | 書籤行號的正規化與上下個書籤（可繞回） |
| `snippets/snippet_expand.py` | 223 | 展開 `$1` / `${1:預設}` 片段、計算定位點與複本位移、內建與使用者片段合併 |
| `macro/keystroke_macro.py` | 89 | 按鍵巨集的錄製與重播狀態（上限 2000 鍵） |
| `command_palette/fuzzy_matcher.py` | 174 | 模糊比對評分（連續 / 詞界 / 前綴 / 子字串加分，長度與前導罰分）與排序 |
| `minimap/minimap_layout.py` | 112 | 縮圖座標換算：取樣間隔、行↔像素、長條寬度、可視範圍方框 |
| `shortcuts/shortcut_registry.py` | 316 | 快捷鍵正規化、`ShortcutRegistry` 衝突偵測、預設表 `WINDOW_SHORTCUTS` / `EDITOR_SHORTCUTS`、使用者覆寫清理 |
| `status/status_text.py` | 71 | 狀態列文字：語言名稱、編碼、行尾、游標位置 |
| `theme/theme_colors.py` | 127 | 深 / 淺色調色盤，換主題時保留使用者自訂的顏色 |

#### 多語系

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `multi_language/english.py` | 483 | 英文字典（其他語言以此為鍵值基準） |
| `multi_language/traditional_chinese.py` | 473 | 繁體中文字典 |
| `multi_language/simplified_chinese.py` | 473 | 簡體中文字典 |
| `multi_language/japanese.py` | 473 | 日文字典 |
| `multi_language/multi_language_wrapper.py` | 150 | `LanguageWrapper` 單例：註冊語言、切換、啟動語言決策 |
| `multi_language/locale_match.py` | 116 | 系統語系 → 編輯器語言（含中文繁簡判定） |
| `multi_language/retranslate_text.py` | 154 | 反查「這段文字是哪個鍵翻出來的」，用於換語言時就地換字 |

#### 基礎設施

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `logging/loggin_instance.py` | 61 | `jeditor_logger` 與 `JEditorLoggingHandler`（RotatingFileHandler 子類） |
| `redirect_manager/redirect_manager_class.py` | 130 | 把 stdout / stderr 導入兩個 Queue，同時也是 logging Handler |
| `exception/exceptions.py` | 30 | 8 個 `JEditorException` 家族的例外類別 |
| `exception/exception_tags.py` | 28 | 例外訊息字串常數 |
| `browser/chromium_flags.py` | 64 | 設定 `QTWEBENGINE_CHROMIUM_FLAGS`，壓下內嵌 Chromium 的日誌 |

---

### 5.3 `code_scan/` — 靜態檢查與檔案監看

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `ruff_lint.py` | 171 | 找 ruff 執行檔、組指令、對「緩衝區內容」或整個專案跑 ruff（20 秒逾時）、套用 `--fix` |
| `ruff_thread.py` | 60 | 以 `threading.Thread` 執行 ruff 子程序並把輸出放進佇列 |
| `watchdog_implement.py` | 56 | watchdog 事件處理：Python 檔被改動就觸發一次 ruff |
| `watchdog_thread.py` | 78 | 跑 watchdog observer 的執行緒，含停止與輸出處理 |

### 5.4 `git_client/` — Git 操作

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `git_action.py` | 280 | `GitService`：以 GitPython 包裝分支 / checkout / commit / diff / pull / push / stash / 衝突處理，並寫 `audit.log` |
| `git_cli.py` | 69 | `GitCLI`：以 `subprocess` 直接呼叫 git，取得 refs 與 commit 清單 |
| `commit_graph.py` | 80 | 由 commit 清單算出圖形化的 lane 配置（`CommitNode` / `CommitGraph`） |
| `file_baseline.py` | 72 | 找出檔案所屬 repo，取得該檔在 HEAD 的內容（行尾統一為 `\n`） |
| `file_blame.py` | 98 | 逐行 blame（`BlameLine`：短 hash / 作者 / 摘要） |
| `file_staging.py` | 178 | 把「組出來的內容」寫進 index，實現 hunk 級暫存；unstage、commit index |

### 5.5 `plugins/` — 插件系統

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `__init__.py` | 171 | 插件註冊表：程式語言（語法高亮）、自然語言（UI 翻譯）、執行設定（run_config）、中繼資料，各自有 register / get 函式 |
| `plugin_loader.py` | 166 | 掃描所有 `jeditor_plugins/` 目錄（去重）、以 importlib 載入、呼叫 `register()` |

---

### 5.6 `pyside_ui/code/` — 編輯器核心

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `plaintext_code_edit/code_edit_plaintext.py` | **3,225** | `CodeEditor(QPlainTextEdit)`：整個編輯器的中樞。行號區 `LineNumber`、gutter（中斷點 / 書籤 / 折疊 / diff 標記）、自繪縮排參考線與 blame、jedi 背景補全 `_JediCompleteWorker`、括號配對、出現次數高亮、所有文字轉換動作、註解切換、縮放、快捷鍵註冊、LSP 訊號接線、右鍵選單 |
| `multi_cursor/multi_cursor_manager.py` | 530 | 額外游標的維護與批次套用（插入 / 刪除 / 移動 / 擴選 / 欄選取 / 下一個相同字） |
| `snippets/snippet_manager.py` | 280 | 片段展開、定位點跳轉、複本同步；使用者片段存於 `.jeditor/snippets.json` |
| `lsp/lsp_client.py` | 438 | 單一檔案這端的 LSP 連線：didOpen / didChange、completion / hover / rename / formatting / signature / references / codeAction / symbols / definition，回應以 Qt 訊號送出 |
| `lsp/lsp_session.py` | 242 | `LspSession`（一個伺服器程序）與 `LspSessionRegistry`（同語言分頁共用、引用計數、關閉時 shutdown） |
| `code_process/code_exec.py` | 237 | `ExecManager`：執行使用者程式（含插件 run_config），輸出導回面板 |
| `shell_process/shell_exec.py` | 132 | `ShellManager`：執行 shell 指令 |
| `base_process_manager.py` | 218 | 上兩者的共用基底：讀取執行緒、輸出佇列、pull timer、結束清理 |
| `running_process_manager.py` | 62 | `RunInstanceManager` 單例：追蹤並統一關閉所有執行實例 |
| `git_diff/diff_marker_manager.py` | 224 | `BaselineLoader(QThread)` 背景讀 HEAD 內容 + `DiffMarkerManager` 維護逐行差異狀態與 hunk 查詢 |
| `git_diff/blame_manager.py` | 149 | `BlameLoader(QThread)` 背景取 blame + `BlameManager` 開關與快取 |
| `lint/lint_manager.py` | 170 | `LintWorker(QThread)` 背景跑 ruff + `LintManager` 保存診斷、供行號查詢 |
| `folding/folding_manager.py` | 190 | 折疊狀態：計算區塊、藏 / 顯示行、重新布局、換檔重算 |
| `bookmark/bookmark_manager.py` | 134 | 書籤切換、跳轉、清空（Qt 整合層） |
| `breakpoint/breakpoint_manager.py` | 87 | 中斷點行號追蹤，並轉成 pdb 指令 |
| `selection/smart_selection_manager.py` | 87 | 智慧選取的擴大 / 縮回堆疊 |
| `minimap/minimap_widget.py` | 184 | 右側縮圖：長條繪製、搜尋命中標記、可視範圍方框、點擊捲動 |
| `split_view/split_editor_view.py` | 55 | 同一份 `QTextDocument` 的第二個檢視 |
| `syntax/python_syntax.py` | 93 | `PythonHighlighter`：Python 專用高亮（含插件規則） |
| `syntax/generic_syntax.py` | 134 | `GenericHighlighter`：依 `language_rules` 的通用高亮，處理跨行區塊註解 |
| `syntax/syntax_setting.py` | 95 | 高亮規則 / 關鍵字 / 插件擴充三個字典 |
| `code_format/pep8_format.py` | 124 | `PEP8FormatChecker`：pycodestyle Checker 子類，把檢查結果導到格式檢查面板 |
| `textedit_code_result/code_record.py` | 89 | `CodeRecord(QTextEdit)`：輸出區，支援搜尋 |
| `auto_save/auto_save_thread.py` | 116 | `CodeEditSaveThread`：定時存檔；`_TextFetcher` 確保在主執行緒取文字 |
| `auto_save/auto_save_manager.py` | 64 | 建立 / 取代分頁的自動儲存執行緒，維護兩個全域字典 |
| `variable_inspector/inspector_gui.py` | 184 | 變數檢視器：`QAbstractTableModel` + 過濾代理 + GUI |

### 5.7 `pyside_ui/main_ui/` — 主視窗與面板

#### 視窗骨架

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `main_editor.py` | 609 | `EditorMain(QMainWindow)`：分頁容器、輸出重導計時器、狀態列更新、設定定期儲存、工作階段還原 / 儲存、關閉時收尾；`EDITOR_EXTEND_TAB` 掛載點 |
| `editor/editor_widget.py` | 542 | `EditorWidget`：一個編輯分頁＝左側專案樹 + 上方 `CodeEditor` + 下方輸出分頁（執行結果 / 格式檢查 / 除錯 / 終端機 / 變數檢視 / Git），含拖放開檔、外部變更偵測、縮圖與分割檢視切換 |
| `editor/editor_widget_dock.py` | 71 | `FullEditorWidget`：可停駐的單檔編輯器 |
| `editor/process_input.py` | 104 | 對子程序（program / shell / debugger）送入標準輸入的視窗 |
| `dock/destroy_dock.py` | 52 | `DestroyDock`：關閉時會真的銷毀內容的 `QDockWidget` |
| `system_tray/extend_system_tray.py` | 88 | 系統匣圖示與隱藏 / 還原 / 關閉選項 |
| `toolbar/toolbar_builder.py` | 485 | 工具列：新增 / 開啟 / 儲存 / 執行 / 除錯 / 停止 / 搜尋 / 指令面板 / 快速開啟 / 前往符號，以及 Git 分支標籤與切換（`_GitBranchScan`、`_GitCheckout` 兩個 QThread，走 git CLI） |
| `retranslate.py` | 267 | 換語言後就地重新標示選單列、工具列、分頁標題與 dock（用 `retranslate_text` 反查鍵） |

#### 選單（`menu/`）

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `set_menu_bar.py` | 69 | 依序組裝 10 個子選單；extend 模式不建插件選單 |
| `file_menu/build_file_menu.py` | 282 | 檔案選單：開 / 存 / 另存、最近檔案（上限 10）、編碼、行尾、字型與大小 |
| `file_menu/encoding_actions.py` | 177 | 實際套用編碼 / 行尾、存檔前格式化、儲存所有分頁 |
| `run_menu/build_run_menu.py` | 155 | 執行選單骨架、停止程式、清除輸出、說明 |
| `run_menu/under_run_menu/build_program_menu.py` | 108 | 執行使用者程式（解析插件 run_config） |
| `run_menu/under_run_menu/build_shell_menu.py` | 98 | 執行 shell 指令 |
| `run_menu/under_run_menu/build_debug_menu.py` | 134 | 啟動 pdb、送出中斷點、除錯輸入視窗 |
| `run_menu/under_run_menu/utils.py` | 41 | 「請先關掉正在執行的程式」訊息框 |
| `text_menu/build_text_menu.py` | 420 | 文字選單：統計、去行尾空白、縮排轉換、自動換行、縮排大小、字型；大量動作轉呼叫 `CodeEditor` 的方法 |
| `check_style_menu/build_check_style_menu.py` | 127 | yapf 格式化、JSON 排版、PEP8 檢查、存檔時自動格式化開關 |
| `tab_menu/build_tab_menu.py` | 187 | 分頁選單：新增編輯 / 瀏覽器 / 終端機分頁、片段編輯器、縮圖與分割檢視切換 |
| `tab_menu/build_tab_git_menu.py` | 200 | Git 分頁：HEAD diff、staged diff、Git 用戶端、提交圖、diff 比對 |
| `tab_menu/build_tab_tools_menu.py` | 155 | 工具分頁：IPython、變數檢視器、FrontEngine、AI 對話、TODO 面板、大綱面板 |
| `dock_menu/build_dock_menu.py` | 230 | 各種 dock 視窗的建立（含 FrontEngine 元件） |
| `style_menu/build_style_menu.py` | 170 | qt-material 樣式切換、縮排參考線 / 尾端空白開關、開啟快捷鍵設定 |
| `language_menu/build_language_server.py` | 96 | 介面語言切換（含插件註冊的語言） |
| `python_env_menu/build_venv_menu.py` | 243 | 建立 venv、pip 安裝 / 升級、選擇直譯器 |
| `plugin_menu/build_plugin_menu.py` | 162 | 依已註冊插件建立「關於 / 執行」子選單，並開啟插件瀏覽器 |
| `help_menu/build_help_menu.py` | 100 | 說明連結（開內嵌瀏覽器分頁）與關於 |
| `submenu_map.py` | 42 | 建立「動作 → 子選單」對照表（避免用 `QAction.menu()`） |

#### 面板與對話框

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `problems_panel/problems_panel_widget.py` | 320 | 問題面板：列出診斷、依嚴重度篩選、跳到該行、整專案檢查、套用可自動修正項 |
| `problems_panel/project_lint_worker.py` | 46 | `ProjectLintWorker(QThread)`：背景對整個目錄跑 ruff |
| `todo_panel/todo_panel_widget.py` | 262 | TODO 面板：背景掃描（`TodoScanThread`）、依標籤篩選、雙擊開檔跳行 |
| `test_panel/test_panel_widget.py` | 413 | 測試面板：組 pytest 指令（可含覆蓋率）、`PytestRunThread` 背景執行（600 秒逾時）、結果表、traceback、只跑選取 / 只跑失敗 |
| `outline_panel/outline_panel_widget.py` | 215 | 大綱面板：Python 用 `ast`，其他語言問語言伺服器，點擊跳行 |
| `command_palette/command_palette_dialog.py` | 193 | 指令面板：模糊搜尋所有選單指令並執行 |
| `command_palette/menu_command_collector.py` | 104 | 走訪選單列蒐集可觸發動作（深度上限 8、數量上限 4000） |
| `command_palette/quick_open_dialog.py` | 205 | 快速開啟檔案（`FileIndexThread` 背景索引），輸入 `>` 切回指令模式 |
| `command_palette/go_to_symbol_dialog.py` | 108 | 在目前檔案中以模糊搜尋跳到符號 |
| `console_widget/console_gui.py` | 178 | 內嵌終端機 UI：指令歷史、切換工作目錄、輸出顯示 |
| `console_widget/qprocess_adapter.py` | 120 | `QProcess` 包裝：啟動互動 shell、Windows 切 UTF-8 code page、送指令、停止 |
| `ipython_widget/ipython_console.py` | 78 | qtconsole 的 IPython 分頁 |
| `ai_widget/chat_ui.py` | 149 | AI 對話 UI：載入設定、送出問題、輪詢回覆 |
| `ai_widget/langchain_interface.py` | 82 | LangChain + OpenAI 的呼叫封裝 |
| `ai_widget/ask_thread.py` | 36 | 在背景執行緒呼叫模型，避免卡 UI |
| `ai_widget/ai_config.py` | 34 | 模型設定與訊息佇列 |
| `plugin_browser/plugin_browser_widget.py` | 373 | 插件瀏覽器：列出遠端 repo 的插件、看中繼資料、下載到 `jeditor_plugins/` |
| `plugin_browser/github_api.py` | 185 | GitHub API 存取：遞迴取檔案樹、解析插件中繼資料、下載（限制 scheme、目的路徑防穿越） |

#### 設定持久化（`save_settings/`）

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `user_setting_file.py` | 66 | `user_setting_dict` 的定義與 `.jeditor/user_setting.json` 讀寫 |
| `user_color_setting_file.py` | 116 | 顏色設定讀寫、RGB → `QColor` 換算、依樣式套用深 / 淺色組 |
| `setting_utils.py` | 40 | 寫入前先備份（`.bak`）的 JSON 寫檔工具 |
| `shortcut_setting.py` | 76 | 取得指令目前生效的按鍵、把 `QAction` 綁上去、設定改動後重新套用 |

### 5.8 `pyside_ui/dialog/`

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `search_ui/search_replace_widget.py` | 602 | 搜尋與取代對話框：三種範圍（目前檔案 / 資料夾 / 整個專案），`_SearchWorker(QThread)` 背景搜尋、正規表示式、結果雙擊跳行、批次取代 |
| `search_ui/search_text_box.py` | 49 | 簡易搜尋框元件 |
| `search_ui/search_error_box.py` | 49 | 搜尋結果 / 錯誤提示框 |
| `shortcut_dialog/shortcut_settings_dialog.py` | 179 | 列出所有指令、改按鍵、即時衝突提示、還原預設 |
| `snippet_dialog/snippet_editor_dialog.py` | 148 | 使用者片段的新增 / 刪除 / 編輯，存檔後重載已開分頁 |
| `file_dialog/open_file_dialog.py` | 129 | 開檔流程：選檔、已開啟就切分頁、載入內容；另有選資料夾更新專案樹 |
| `file_dialog/save_file_dialog.py` | 132 | 另存新檔：依插件語言動態建立篩選器並依副檔名預選 |
| `file_dialog/create_file_dialog.py` | 77 | 建立新檔案 |
| `ai_dialog/set_ai_dialog.py` | 71 | 設定 AI 模型參數 |

### 5.9 `pyside_ui/git_ui/`

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `git_client/git_client_gui.py` | 1,072 | `GitGui`：完整 Git 面板——開 repo、分支清單與切換、變更清單（未暫存 / 已暫存）、各種 diff 呈現（新增 / 刪除 / 改名 / 已暫存 / 修改）、暫存與提交、stash、衝突解決、clone、push、未推送數量；`_GitWorker(QObject)` 背景執行；`GitDiffHighlighter` 為 diff 上色 |
| `git_client/git_branch_tree_widget.py` | 151 | `GitTreeViewGUI`：提交歷史圖檢視（走 `GitCLI`），含檔案監看自動刷新 |
| `git_client/graph_view.py` | 219 | `CommitGraphView(QGraphicsView)`：commit 圖繪製（lane 顏色、縮放、聚焦某列） |
| `git_client/commit_table.py` | 65 | commit 清單表格 |
| `code_diff_compare/side_by_side_diff_widget.py` | 272 | 並排 diff：捲動同步、逐行分類上色、深 / 淺色主題 |
| `code_diff_compare/multi_file_diff_viewer.py` | 88 | 多檔 diff，依檔案分頁顯示 |
| `code_diff_compare/line_number_code_viewer.py` | 141 | 帶行號的唯讀檢視器（diff 用） |
| `code_diff_compare/code_diff_viewer_widget.py` | 90 | diff 檢視分頁的容器與主題套用 |

### 5.10 `pyside_ui/browser/`

| 模組 | 行 | 功用 |
| --- | ---: | --- |
| `main_browser_widget.py` | 86 | 瀏覽器分頁容器，最右側固定一個「+」新分頁 |
| `browser_widget.py` | 103 | 單一瀏覽器分頁：網址列、搜尋前綴、頁內尋找 |
| `browser_view.py` | 105 | `QWebEngineView` 子類，處理下載 |
| `browser_serach_lineedit.py` | 52 | 網址 / 搜尋輸入列 |
| `browser_download_window.py` | 75 | 下載進度與狀態視窗 |

---

## 6. 橫切主題

### 6.1 執行緒模型

UI 執行緒不做 I/O 是硬性規則，重活分成三類：

| 方式 | 使用者 |
| --- | --- |
| `QThread` + Signal | `LintWorker`、`BaselineLoader`、`BlameLoader`、`ProjectLintWorker`、`TodoScanThread`、`PytestRunThread`、`FileIndexThread`、`_SearchWorker`、`_GitBranchScan`、`_GitCheckout` |
| `threading.Thread` | `CodeEditSaveThread`（自動儲存）、`RuffThread`、`WatchdogThread`、`AskThread`（AI）、插件瀏覽器的下載 worker |
| `QProcess` / `subprocess` | 執行使用者程式與 shell（`BaseProcessManager` 以讀取執行緒 + 佇列 + timer 拉取輸出）、終端機（`ConsoleProcessAdapter`）、ruff、pytest、git CLI |

搭配的節流機制：diff 標記 400ms、lint 900ms、jedi 補全 300ms、縮圖重畫 300ms、輸出拉取 50ms、設定儲存 60s。

已知地雷（`conftest.py` 與註解都有記錄）：`QThread` 若在執行中被銷毀，Qt 會 `qFatal` 直接中止行程。
因此每個 QThread 子類都會 `setObjectName(...)`，測試有 autouse fixture 等工具列的背景掃描結束。

### 6.2 設定與持久化

全部集中在工作目錄下的 `.jeditor/`：

| 檔案 | 內容 |
| --- | --- |
| `user_setting.json` | 字型、語言、樣式、編碼、縮排、最近檔案、開啟分頁與其游標 / 書籤 / 折疊狀態、快捷鍵覆寫 |
| `user_color_setting.json` | 編輯器自訂顏色 |
| `snippets.json` | 使用者程式碼片段 |
| `*.bak` | 每次寫入前的備份（`setting_utils.write_setting`） |

### 6.3 多語系

`language_wrapper` 持有目前語言字典，所有介面文字以鍵取值（如 `language_word_dict.get("application_name")`）。
換語言時 **不重建視窗**，而是由 `retranslate.py` 走訪選單 / 工具列 / 分頁 / dock，
用 `retranslate_text.key_for_text` 反查每段文字原本的鍵，再換成新語言的說法。
插件可用 `register_natural_language` 加入新語言。

### 6.4 快捷鍵

`utils/shortcuts/shortcut_registry.py` 是唯一事實來源：`WINDOW_SHORTCUTS`（視窗層）與
`EDITOR_SHORTCUTS`（編輯器層）合成 `DEFAULT_SHORTCUTS`，使用者覆寫存在設定裡且只記與預設不同的項目。
`ShortcutRegistry` 會偵測重複指派（Qt 遇到重複時兩個動作都不會執行，卻不報錯）。

**例外**：`Ctrl+D`、`Ctrl+/`、`Alt+Up/Down`、`Ctrl+B`、`Ctrl+Shift+\`、`Ctrl++`/`Ctrl+-`
目前寫死在 `code_edit_plaintext.py` 的 `_handle_ctrl_shortcuts` / `_handle_alt_shortcuts`，
不在 registry 中，因此設定對話框改不到（`PROGRESS.md` 有記此待辦）。

### 6.5 主題顏色

qt-material 負責視窗樣式；編輯器自身的顏色（語法高亮、diff 標記、診斷底線、輸出顏色）由
`utils/theme/theme_colors.py` 提供深 / 淺兩組預設，換樣式時 `apply_theme_colors` 會換掉預設色但保留使用者挑過的顏色，
換算結果放在 `actually_color_dict`。

`update_actually_color_dict` 的鍵與備用值直接取自 `DARK_COLORS`，所以調色盤加新顏色不必動它。
兩個高亮器都只認顏色鍵：`syntax_setting.py` 的內建規則存的是鍵名而非寫死的 `QColor`（插件仍可直接給 `QColor`），
`generic_syntax.py` 亦然。高亮器在建立時就把顏色取走，因此 `build_style_menu._repaint_editors` 換主題時會呼叫
`reset_highlighter()` 重建，否則語法顏色會停在上一個主題。

### 6.6 插件系統

四種註冊面向，全部經由 `je_editor` 的公開 API：

1. **程式語言** `register_programming_language(suffix, syntax_words, syntax_rules)` → 影響語法高亮與存檔篩選器
2. **自然語言** `register_natural_language(key, display_name, word_dict)` → 影響語言選單
3. **執行設定** `register_plugin_run_config(run_config)` → 影響執行選單與 `ExecManager`
4. **中繼資料** `register_plugin_metadata(metadata)` → 影響插件選單的「關於」

載入來源是各層級的 `jeditor_plugins/` 目錄（`plugin_loader` 會去重），
使用者也可從插件瀏覽器直接自 GitHub 下載。

### 6.7 擴充模式（extend mode）

`EditorMain(extend=True)` 讓下游專案（PyBreeze）沿用整個編輯器但自建插件選單與應用程式識別；
`EDITOR_EXTEND_TAB` 則讓下游在啟動時塞入自訂分頁。這是 JEditor 作為函式庫被重用的主要接口。

---

## 7. 測試與 CI

- `test/` 88 個測試檔、約 13,400 行，與模組大致一對一（`test_fold_regions.py`、`test_shortcut_registry.py`…）。
- `conftest.py` 提供 session 級 `qapp`、`tmp_dir`、`tmp_file`，以及 autouse 的「等工具列背景執行緒結束」fixture；
  `collect_ignore_glob` 排除會真的開視窗的 `start_qt_ui.py` / `extend_test.py`。
- `pyproject.toml` 設定 `testpaths = ["test"]`、`qt_api = "pyside6"`；bandit 排除測試目錄（pytest 慣用 `assert`）。
- CI（`.github/workflows/dev.yml`、`stable.yml`）跑 Python 3.10 / 3.11 / 3.12，不設 `QT_QPA_PLATFORM=offscreen`。

---

## 8. 架構觀察

### 做得好的地方

- **邏輯與 Qt 分離徹底**：`utils/` 59 個模組幾乎都是純函式，因此測試不必開視窗，也讓折疊、diff、模糊搜尋這類演算法可以獨立驗證。
- **背景化一致**：所有會 I/O 的操作都有對應的 worker，並配上 debounce；UI 卡頓的風險集中在少數幾處而非散落各地。
- **單一事實來源**：快捷鍵、顏色、語言字典、忽略規則各有唯一定義處，UI 只是消費端。
- **雙語註解與 docstring**：模組層級 docstring 幾乎全數存在，且說明「為什麼」而不只是「做什麼」。

### 值得注意的張力

1. **`code_edit_plaintext.py` 3,225 行、`CodeEditor` 有 190 個方法**，明顯與 CLAUDE.md 的「避免 god class」相衝。
   目前靠把狀態外包給十多個 manager 緩解，但方法本身（文字轉換、繪製、快捷鍵、LSP 回呼）仍集中在同一類別。
   若要拆，`_paint_*` 系列與 `*_selection` 系列是最自然的切分線。
2. **`git_client_gui.py` 1,072 行**，`GitGui` 一個類別同時負責 UI 佈局、diff 呈現、Git 操作與主題套用。
3. **Git 有兩條存取路徑**：`GitService` / `file_*`（GitPython）與 `GitCLI`（subprocess）。
   工具列的分支掃描與 checkout 在 QThread 中走 CLI，而 `BlameLoader` / `BaselineLoader` 在 QThread 中走 GitPython。
   考慮到 GitPython 在背景執行緒曾造成 Qt 中止的紀錄，這個分歧值得統一或至少明確記錄理由。
4. **四份語言字典各約 473 行**，鍵值必須手動保持同步；新增一個介面字串要改四個檔案（下游 PyBreeze 另有 parity 測試把關）。
5. **`utils/` 的兩個 Qt 依賴例外**（`session/editor_state.py` 以 duck typing 操作 widget、`multi_language/locale_match.py` 讀 `QLocale`）
   讓「純邏輯層」的界線稍微模糊。
6. **命名遺留**：`utils/logging/loggin_instance.py`、`browser/browser_serach_lineedit.py` 兩處拼字錯誤已成公開路徑，
   要改需同時處理下游 import。
