# JEDITOR

<p align="center">
  <img src="../docs/source/docs/Zh/image/JEditor.png" alt="JEDITOR Logo" width="200"/>
</p>

<p align="center">
  <strong>一款基於 Python 與 PySide6 打造的現代化、輕量級、可擴展程式碼編輯器。</strong>
</p>

<p align="center">
  <a href="https://github.com/JE-Chen/je_editor">
    <img src="https://img.shields.io/github/stars/JE-Chen/je_editor?style=social" alt="GitHub Stars"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/v/je_editor" alt="PyPI Version"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/pyversions/je_editor" alt="Python Versions"/>
  </a>
  <a href="https://github.com/JE-Chen/je_editor/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JE-Chen/je_editor" alt="License"/>
  </a>
  <a href="https://je-editor.readthedocs.io/en/latest/">
    <img src="https://img.shields.io/readthedocs/je-editor" alt="Read the Docs"/>
  </a>
</p>

<p align="center">
  <a href="../README.md">English</a> |
  <a href="README_zh-CN.md">简体中文</a>
</p>

---

## 目錄

- [簡介](#簡介)
- [主要特色](#主要特色)
- [截圖展示](#截圖展示)
- [系統需求](#系統需求)
- [安裝方式](#安裝方式)
- [快速開始](#快速開始)
- [功能詳情](#功能詳情)
  - [程式碼編輯](#程式碼編輯)
  - [程式執行與除錯](#程式執行與除錯)
  - [程式碼品質與格式化](#程式碼品質與格式化)
  - [檔案操作](#檔案操作)
  - [Git 整合](#git-整合)
  - [AI 助手](#ai-助手)
  - [主控台與 REPL](#主控台與-repl)
  - [內建瀏覽器](#內建瀏覽器)
  - [外掛系統](#外掛系統)
  - [主題與自訂](#主題與自訂)
  - [多語言介面](#多語言介面)
- [鍵盤快捷鍵](#鍵盤快捷鍵)
- [專案架構](#專案架構)
- [外掛開發](#外掛開發)
- [設定檔](#設定檔)
- [文件](#文件)
- [參與貢獻](#參與貢獻)
- [授權條款](#授權條款)

---

## 簡介

JEDITOR 是原始 JEditor 專案的完全重寫版本，從零開始重新打造，專注於**速度**、**易用性**與**可擴展性**。以 **PySide6**（Qt for Python）為基礎，提供現代化的桌面編輯體驗，內建語法高亮、自動補全、整合式 Git 用戶端、AI 助手、內嵌瀏覽器、IPython 主控台以及強大的外掛系統等豐富功能。

與原始 JEditor 相比，JEDITOR 效能提升高達 **1000%**，同時提供更加豐富的功能集。

---

## 主要特色

| 類別 | 功能 |
|---|---|
| **編輯器** | 多分頁編輯、語法高亮、自動補全（Jedi）、行號顯示、目前行高亮、搜尋與取代（支援正則表達式） |
| **執行** | 執行 Python 腳本（F5）、除錯模式（F9）、Shell 指令、虛擬環境偵測 |
| **程式碼品質** | YAPF 格式化、PEP8 檢查、Ruff 靜態分析、JSON 重新格式化 |
| **Git** | 分支管理、提交歷史、並排差異檢視器、暫存區操作、稽核日誌 |
| **AI** | 透過 LangChain 整合 OpenAI GPT、互動式聊天面板、可設定模型與提示詞 |
| **主控台** | 互動式 Shell、Jupyter/IPython 主控台、指令歷史、多 Shell 支援 |
| **瀏覽器** | 內嵌網頁瀏覽器、URL 導覽、頁面內搜尋 |
| **外掛** | 自訂語法高亮、UI 翻譯、執行設定、自動探索 |
| **介面** | 深色/淺色主題（Qt Material）、字型自訂、可停靠面板、系統匣、工具列 |
| **國際化** | 英文、繁體中文，可透過外掛擴展 |
| **檔案** | 自動儲存、多編碼支援（UTF-8、GBK、Latin-1 等）、最近開啟的檔案 |

---

## 截圖展示

<p align="center">
  <img src="../docs/source/docs/Zh/image/JEditor.png" alt="JEDITOR 截圖"/>
</p>

---

## 系統需求

| 平台 | 版本 |
|---|---|
| **Windows** | Windows 10 / 11 |
| **macOS** | 10.5 ~ 11 Big Sur |
| **Linux** | Ubuntu 20.04+ |
| **Raspberry Pi** | 3B+ |
| **Python** | 3.10+（已測試 3.10、3.11、3.12） |

---

## 安裝方式

### 從 PyPI 安裝（推薦）

```bash
pip install je_editor
```

### 從原始碼安裝

```bash
git clone https://github.com/JE-Chen/je_editor.git
cd je_editor
pip install .
```

### 相依套件

核心相依套件會自動安裝：

| 套件 | 用途 |
|---|---|
| PySide6 | GUI 框架（Qt for Python） |
| qt-material | 深色/淺色 Material 主題 |
| yapf | Python 程式碼格式化（Google 風格） |
| jedi | Python 自動補全與分析 |
| ruff | 快速 Python 靜態分析工具 |
| gitpython | Git 倉庫操作 |
| langchain + langchain_openai | AI/LLM 整合 |
| watchdog | 檔案系統監控 |
| pycodestyle | PEP8 風格檢查 |
| qtconsole | Jupyter/IPython 主控台元件 |

---

## 快速開始

### 啟動編輯器

```bash
python -m je_editor
```

### 作為 Python 函式庫使用

```python
from je_editor import start_editor

start_editor()
```

編輯器預設會以最大化視窗與深色琥珀色主題啟動。

---

## 功能詳情

### 程式碼編輯

- **多分頁編輯器** -- 同時處理多個檔案，支援關閉分頁。
- **語法高亮** -- 內建 Python 語法高亮，可透過外掛擴展支援更多語言。
- **自動補全** -- 由 Jedi 驅動的上下文感知程式碼建議。
- **行號顯示** -- 編輯器旁顯示行號，並高亮目前行。
- **搜尋與取代** -- 支援在目前檔案、資料夾或整個專案中搜尋，提供正則表達式與區分大小寫選項。大型專案使用背景執行緒處理。
- **變數檢查器** -- 在程式執行期間檢查與除錯變數。

### 程式執行與除錯

- **執行 Python 腳本**（F5）-- 執行目前檔案並即時串流輸出。
- **除錯模式**（F9）-- 啟動 Python 除錯器進行逐步除錯。
- **Shell 指令** -- 在編輯器內直接執行任意 Shell/終端機指令。
- **虛擬環境偵測** -- 自動偵測並啟用 Python 虛擬環境。
- **程序管理** -- 停止單一或所有執行中的程序。
- **錯誤高亮** -- 錯誤訊息在輸出面板中以紅色顯示。

### 程式碼品質與格式化

- **YAPF Python 格式化**（Ctrl+Shift+Y）-- 使用 Google 風格自動格式化 Python 程式碼。
- **PEP8 檢查**（Ctrl+Alt+P）-- 驗證程式碼是否符合 PEP8 風格指南。
- **Ruff 靜態分析** -- 在背景執行緒中執行快速且全面的 Python 靜態分析。
- **JSON 重新格式化**（Ctrl+J）-- 美化列印並驗證 JSON 內容。

### 檔案操作

- **建立、開啟、儲存**檔案，使用標準快捷鍵（Ctrl+N、Ctrl+O、Ctrl+S）。
- **開啟資料夾**（Ctrl+K）-- 瀏覽專案目錄結構。
- **自動儲存** -- 自動定期儲存檔案，防止資料遺失。
- **多編碼支援** -- 無縫處理 UTF-8、GBK、Latin-1 及其他編碼，具備自動偵測功能。
- **最近開啟的檔案** -- 快速存取先前開啟的檔案。

### Git 整合

JEDITOR 內建完整的 Git 用戶端：

- **分支管理** -- 從工具列列出、切換與檢出分支。
- **提交歷史** -- 以表格形式檢視提交的中繼資料（作者、日期、訊息）。
- **並排差異檢視器** -- 具有行號的彩色高亮程式碼比較。
- **多檔案差異** -- 比較多個檔案間的變更。
- **暫存區操作** -- 暫存或取消暫存個別檔案的變更。
- **稽核日誌** -- 記錄所有 Git 操作，方便追蹤與合規。

### AI 助手

整合 OpenAI 與 LangChain 的 AI 助手：

- **GPT-3.5 / GPT-4 支援** -- 連接 OpenAI 的語言模型。
- **互動式聊天面板** -- 編輯器內的對話式 AI 面板。
- **可設定模型** -- 設定自訂 API 金鑰、端點、模型名稱與系統提示詞。
- **非同步訊息** -- 使用訊息佇列實現非阻塞 AI 互動。

### 主控台與 REPL

- **互動式主控台** -- 執行 Shell 指令並支援歷史導覽（上/下方向鍵）。
- **Jupyter/IPython 主控台** -- 內建程序 IPython 核心，支援豐富輸出。
- **多 Shell 支援** -- 支援 cmd、PowerShell、bash 與 sh。
- **工作目錄控制** -- 獨立設定執行目錄。

### 內建瀏覽器

- **內嵌網頁瀏覽器** -- 不離開編輯器即可瀏覽網頁。
- **URL 導覽** -- 具有整合搜尋功能的網址列。
- **頁面內搜尋**（Ctrl+F）-- 在網頁中搜尋文字。
- **標準導覽** -- 上一頁、下一頁、重新整理與停止控制。

### 外掛系統

JEDITOR 支援模組化的外掛架構，提供四種外掛類型：

| 類型 | 用途 |
|---|---|
| 程式語言 | 為新語言新增語法高亮 |
| 自然語言 | 為新語系新增 UI 翻譯 |
| 執行設定 | 定義自訂執行環境 |
| 外掛中繼資料 | 提供外掛版本與作者資訊 |

外掛會自動從 `jeditor_plugins/` 目錄中探索載入。詳見[外掛開發](#外掛開發)章節。

### 主題與自訂

- **深色/淺色主題** -- Qt Material 主題，琥珀色配色方案。
- **字型自訂** -- 變更編輯器與 UI 的字型家族與大小。
- **可停靠面板** -- 透過停靠/取消停靠面板重新排列 UI 布局。
- **系統匣** -- 將編輯器最小化至系統匣。
- **工具列** -- JetBrains 風格的快速操作按鈕。

### 多語言介面

- **英文** -- 完整的英文介面（預設）。
- **繁體中文** -- 完整的繁體中文翻譯。
- **可擴展** -- 透過外掛系統新增更多語言。

---

## 鍵盤快捷鍵

| 快捷鍵 | 動作 |
|---|---|
| `Ctrl+N` | 新增檔案 |
| `Ctrl+O` | 開啟檔案 |
| `Ctrl+K` | 開啟資料夾 |
| `Ctrl+S` | 儲存檔案 |
| `Ctrl+J` | 重新格式化 JSON |
| `Ctrl+Shift+Y` | YAPF Python 格式化 |
| `Ctrl+Alt+P` | PEP8 格式檢查 |
| `Ctrl+F` | 搜尋文字（瀏覽器） |
| `F5` | 執行程式 |
| `F9` | 除錯 |
| `Shift+F5` | 停止程式 |
| `上/下方向鍵` | 指令歷史（主控台） |

---

## 專案架構

```
je_editor/
├── pyside_ui/                    # GUI 元件（PySide6）
│   ├── browser/                  # 內嵌網頁瀏覽器
│   ├── code/                     # 核心程式碼編輯
│   │   ├── auto_save/            # 自動儲存
│   │   ├── code_format/          # YAPF 與 PEP8 格式化
│   │   ├── code_process/         # 程式執行（ExecManager）
│   │   ├── shell_process/        # Shell 執行（ShellManager）
│   │   ├── syntax/               # 語法高亮引擎
│   │   ├── plaintext_code_edit/  # 純文字編輯器元件
│   │   ├── textedit_code_result/ # 輸出顯示元件
│   │   └── variable_inspector/   # 變數除錯
│   ├── dialog/                   # 對話框視窗
│   │   ├── ai_dialog/            # AI 設定對話框
│   │   ├── file_dialog/          # 檔案操作對話框
│   │   └── search_ui/            # 搜尋與取代對話框
│   ├── git_ui/                   # Git 介面
│   │   ├── code_diff_compare/    # 並排差異檢視器
│   │   └── git_client/           # 分支與提交 UI
│   └── main_ui/                  # 主編輯器視窗
│       ├── ai_widget/            # AI 聊天面板
│       ├── console_widget/       # 互動式主控台
│       ├── dock/                 # 可停靠元件管理
│       ├── editor/               # 分頁式編輯器
│       ├── ipython_widget/       # Jupyter/IPython 主控台
│       ├── menu/                 # 選單列系統
│       ├── plugin_browser/       # 外掛管理 UI
│       ├── save_settings/        # 設定持久化
│       ├── system_tray/          # 系統匣整合
│       └── toolbar/              # 工具列操作
├── code_scan/                    # 程式碼掃描
│   ├── ruff_thread.py            # Ruff 靜態分析（多執行緒）
│   ├── watchdog_implement.py     # 檔案系統監控
│   └── watchdog_thread.py        # Watchdog 多執行緒
├── git_client/                   # Git 後端
│   ├── git_action.py             # Git 操作（含稽核日誌）
│   ├── git_cli.py                # Git CLI 包裝器
│   └── commit_graph.py           # 提交圖形視覺化
├── plugins/                      # 外掛系統
│   └── plugin_loader.py          # 動態外掛載入
├── utils/                        # 工具程式
│   ├── encodings/                # 編碼偵測
│   ├── exception/                # 自訂例外
│   ├── file/                     # 檔案 I/O（開啟/儲存）
│   ├── json_format/              # JSON 格式化
│   ├── logging/                  # 日誌設定
│   ├── multi_language/           # 國際化（英文、繁體中文）
│   ├── redirect_manager/         # 輸出串流重導向
│   └── venv_check/               # 虛擬環境偵測
├── __init__.py                   # 公開 API
├── __main__.py                   # CLI 進入點
└── start_editor.py               # 應用程式啟動器
```

---

## 外掛開發

在工作目錄中建立 `jeditor_plugins/` 目錄來放置外掛。JEDITOR 支援三種外掛類型：

### 1. 程式語言外掛

為新語言新增語法高亮：

```python
from je_editor.plugins import register_programming_language

register_programming_language(
    suffix=".rs",
    syntax_words={"keywords": ["fn", "let", "mut", "struct", "impl", "enum"]},
    syntax_rules={"keyword_color": "#FF6600"}
)
```

### 2. 自然語言外掛

新增 UI 翻譯：

```python
from je_editor.plugins import register_natural_language

register_natural_language(
    language_key="ja",
    display_name="Japanese",
    word_dict={"file": "ファイル", "edit": "編集", "run": "実行"}
)
```

### 3. 執行設定外掛

定義自訂執行環境：

```python
from je_editor.plugins import register_plugin_run_config

register_plugin_run_config(
    name="Node.js",
    run_config={"command": "node", "suffix": ".js"}
)
```

完整指南請參閱 `PLUGIN_GUIDE.md`。

---

## 設定檔

JEDITOR 將使用者設定儲存在 `.jeditor/` 目錄中：

| 檔案 | 內容 |
|---|---|
| `user_setting.json` | 一般偏好設定（字型、主題、最近開啟的檔案） |
| `user_color_setting.json` | 語法高亮配色方案 |

---

## 文件

完整文件請參閱：
**[https://je-editor.readthedocs.io/en/latest/](https://je-editor.readthedocs.io/en/latest/)**

---

## 參與貢獻

歡迎貢獻！請在 [GitHub](https://github.com/JE-Chen/je_editor) 上提交 Issue 與 Pull Request。

---

## 授權條款

本專案採用 **MIT 授權條款**。詳見 [LICENSE](../LICENSE)。

Copyright (c) 2021 ~ Now JE-Chen
