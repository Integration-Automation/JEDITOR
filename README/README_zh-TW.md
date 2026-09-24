# JEDITOR

<p align="center">
  <img src="../image/JEditor.png" alt="JEDITOR Logo" width="180"/>
</p>

<p align="center">
  <strong>一款基於 Python 與 PySide6 打造的現代化、輕量級、可擴展程式碼編輯器。</strong>
</p>

<p align="center">
  <a href="https://github.com/Integration-Automation/JEDITOR">
    <img src="https://img.shields.io/github/stars/Integration-Automation/JEDITOR?style=social" alt="GitHub Stars"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/v/je_editor" alt="PyPI Version"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/pyversions/je_editor" alt="Python Versions"/>
  </a>
  <a href="https://github.com/Integration-Automation/JEDITOR/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Integration-Automation/JEDITOR" alt="License"/>
  </a>
  <a href="https://je-editor.readthedocs.io/en/latest/">
    <img src="https://img.shields.io/readthedocs/je-editor" alt="Read the Docs"/>
  </a>
</p>

<p align="center">
  <a href="../README.md">English</a> |
  <strong>繁體中文</strong> |
  <a href="README_zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="../image/screenshot-main-window.png" alt="JEDITOR 主視窗"/>
</p>

---

## 目錄

- [簡介](#簡介)
- [功能導覽](#功能導覽)
  - [執行程式碼並檢視輸出](#執行程式碼並檢視輸出)
  - [不需離開鍵盤即可尋找任何內容](#不需離開鍵盤即可尋找任何內容)
  - [隨打隨查的靜態分析](#隨打隨查的靜態分析)
  - [在目前檔案中導覽](#在目前檔案中導覽)
  - [執行測試並直達失敗處](#執行測試並直達失敗處)
  - [Git，從行號區到整個儲存庫](#git從行號區到整個儲存庫)
  - [跨專案搜尋與取代](#跨專案搜尋與取代)
  - [一次讀到檔案的更多內容](#一次讀到檔案的更多內容)
  - [同一視窗內的終端機與瀏覽器](#同一視窗內的終端機與瀏覽器)
  - [打造專屬於您的編輯器](#打造專屬於您的編輯器)
- [主要特色](#主要特色)
- [系統需求](#系統需求)
- [安裝方式](#安裝方式)
- [快速開始](#快速開始)
- [功能詳情](#功能詳情)
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

> 下方每一張截圖都是執行中的應用程式的真實畫面，而非示意圖。

---

## 功能導覽

### 執行程式碼並檢視輸出

按下 `F5`，目前的檔案便會以您選擇的直譯器執行；stdout 與 stderr 會隨到隨現地串流回傳到 **Code Result** 窗格，錯誤以紅色顯示。`Shift+F5` 可停止執行，除錯器、終端機、變數檢查器與 Git 窗格則以分頁的形式並列在旁邊。

<p align="center">
  <img src="../image/screenshot-run-output.png" alt="以即時輸出執行 Python 檔案"/>
</p>

### 不需離開鍵盤即可尋找任何內容

`Ctrl+Shift+A` 會以名稱或選單路徑模糊搜尋每一個選單指令，依字詞邊界、連續字元與前綴排序，並在右側顯示每個指令自己的快捷鍵。

<p align="center">
  <img src="../image/screenshot-command-palette.png" alt="指令面板" width="760"/>
</p>

`Ctrl+P` 對檔案做同樣的事。索引在背景執行緒建立，會略過版本控制、快取、虛擬環境與建置目錄以及二進位檔案類型；開頭輸入 `>` 可將同一個選擇器切換回指令模式。

<p align="center">
  <img src="../image/screenshot-quick-open.png" alt="快速開啟檔案選擇器" width="760"/>
</p>

### 隨打隨查的靜態分析

`ruff` 檢查的是 **緩衝區** 而非磁碟上的檔案，在停止輸入後於工作執行緒執行，因此未儲存的編輯也會被涵蓋，而被取代的過時結果會被丟棄。檢查結果會就地以底線標示，並列在問題（Problems）面板中，其中的 **Apply Fixes** 會套用 ruff 自己能修的全部內容。

<p align="center">
  <img src="../image/screenshot-problems-panel.png" alt="列出 ruff 診斷的問題面板"/>
</p>

<p align="center">
  <img src="../image/screenshot-lint-inline.png" alt="編輯器中以底線標示的診斷"/>
</p>

### 在目前檔案中導覽

大綱面板會列出目前檔案的類別、方法、函式與模組變數。Python 以 `ast` 解析，不會執行任何程式碼；其他語言則向其語言伺服器詢問，也就是說 TypeScript 或 Rust 檔案同樣能得到大綱。

<p align="center">
  <img src="../image/screenshot-outline-panel.png" alt="文件大綱面板" width="520"/>
</p>

TODO 面板會掃描整個專案中的 `TODO`、`FIXME`、`HACK`、`XXX`、`BUG`、`NOTE` 與 `OPTIMIZE` 註解，涵蓋 Python、C 系、HTML、SQL 等註解樣式。標籤只有出現在註解符號之後才會被回報，因此一般字串絕不會被誤判。

<p align="center">
  <img src="../image/screenshot-todo-panel.png" alt="TODO 面板"/>
</p>

### 執行測試並直達失敗處

從面板執行 pytest，並以失敗優先的方式檢視結果。選取一筆失敗的測試會在清單下方顯示其 traceback，雙擊可在失敗的那一行開啟該測試，您還可以重跑全部、僅重跑選取項，或只重跑上次失敗的項。勾選 **With coverage** 會在摘要旁加上總覆蓋率。

<p align="center">
  <img src="../image/screenshot-test-panel.png" alt="顯示失敗測試及其 traceback 的測試面板"/>
</p>

### Git，從行號區到整個儲存庫

行號區會顯示檔案與最後一次提交的差異——綠色表示新增的行，橘色表示修改，細紅線表示該處有行被刪除。`F7` / `Shift+F7` 在變更之間跳轉，`Ctrl+Alt+Z` 以單一步復原將游標所在的變更還原，右鍵選單則只暫存那一個變更。`Ctrl+Alt+B` 切換行內 blame。已提交的版本在背景執行緒讀取，比對本身是純記憶體中的 diff，因此編輯永遠不必等待 git。

完整的用戶端可處理分支、暫存、提交、擱置、衝突、複製（clone）與推送：

<p align="center">
  <img src="../image/screenshot-git-panel.png" alt="Git 用戶端面板"/>
</p>

任何變更都能以並排比較的形式開啟，與 `HEAD` 或與已暫存的內容比較：

<p align="center">
  <img src="../image/screenshot-diff-side-by-side.png" alt="並排差異檢視器"/>
</p>

### 跨專案搜尋與取代

在目前檔案、某個資料夾或整個專案中搜尋，支援正則表達式與大小寫選項。較長的搜尋會在工作執行緒執行，因此視窗保持流暢，雙擊某個命中處即可在該行開啟對應檔案。

<p align="center">
  <img src="../image/screenshot-search-replace.png" alt="搜尋與取代對話框" width="900"/>
</p>

### 一次讀到檔案的更多內容

`Ctrl+Alt+M` 會開啟整份檔案的縮圖，以長條依每一行的長度與縮排繪製，並標示 lint 診斷、git 變更與搜尋命中處。`Ctrl+Alt+\` 會分割檢視：兩側共用同一份文件，因此任一側的編輯會立刻反映到另一側，而捲動位置與游標各自獨立。

<p align="center">
  <img src="../image/screenshot-minimap-split-view.png" alt="縮圖與分割檢視"/>
</p>

### 同一視窗內的終端機與瀏覽器

終端機分頁是一個真正的互動式 Shell（cmd、PowerShell、bash 或 sh），具備指令歷史與自己的工作目錄。

<p align="center">
  <img src="../image/screenshot-terminal.png" alt="內嵌終端機"/>
</p>

瀏覽器分頁讓文件與 Stack Overflow 觸手可及，具備分頁、網址列與頁面內搜尋。

<p align="center">
  <img src="../image/screenshot-browser.png" alt="內嵌網頁瀏覽器"/>
</p>

### 打造專屬於您的編輯器

每個指令的按鍵都列在一份可編輯的表格中。兩個指令不能共用同一組按鍵，因為發生這種情況時 Qt 兩個都不會執行；改動立即生效，而且只有與預設值不同的項目會被記錄。

<p align="center">
  <img src="../image/screenshot-shortcut-settings.png" alt="鍵盤快捷鍵設定" width="760"/>
</p>

程式碼片段採用常見的 `$1` / `${2:default}` / `$0` 記法，各語言專屬的片段集疊加在共用片段之上，從 **Tab > Edit Snippets** 編輯，而不必手動改檔。

<p align="center">
  <img src="../image/screenshot-snippet-editor.png" alt="程式碼片段編輯器" width="760"/>
</p>

主題來自 Qt Material，編輯器本身的顏色會跟隨您所選的主題——淺色視窗絕不會讓您對著深色主題的語法配色。

<p align="center">
  <img src="../image/screenshot-light-theme.png" alt="使用淺色主題的 JEDITOR"/>
</p>

---

## 主要特色

| 類別 | 功能 |
|---|---|
| **編輯器** | 多分頁編輯、十二種語言的語法高亮、自動補全（Jedi 與語言伺服器）、可選取的多重游標、支援連動佔位符的程式碼片段、分割檢視、縮圖、程式碼折疊（縮排與大括號）、書籤、出現處高亮、行操作 |
| **導覽** | 指令面板、快速開啟（前往檔案）、前往符號、文件大綱、導覽歷史（往前／往後）、TODO/FIXME 任務面板 |
| **執行** | 執行 Python 腳本（F5）、除錯模式（F9）、Shell 指令、虛擬環境偵測 |
| **程式碼品質** | YAPF 格式化、儲存時格式化、PEP8 檢查、Ruff 靜態分析與問題面板、語言伺服器診斷與快速修正、含 traceback 與覆蓋率的 pytest 面板、JSON 重新格式化 |
| **Git** | 分支管理、提交歷史、並排差異檢視器、行號區變更標記、逐個變更暫存與還原、行內 blame、擱置（stash）、衝突解決、稽核日誌 |
| **AI** | 透過 LangChain 整合 OpenAI GPT、互動式聊天面板、可設定模型與提示詞 |
| **主控台** | 互動式 Shell、Jupyter/IPython 主控台、指令歷史、多 Shell 支援 |
| **瀏覽器** | 內嵌網頁瀏覽器、URL 導覽、頁面內搜尋 |
| **外掛** | 自訂語法高亮、UI 翻譯、執行設定、自動探索 |
| **介面** | 深色/淺色主題（Qt Material）與配套的編輯器配色、可設定的鍵盤快捷鍵、字型自訂、可停靠面板、系統匣、工具列、狀態列 |
| **國際化** | 英文、繁體中文、简体中文、日本語；跟隨系統語言、不需重啟即可切換、可透過外掛擴展 |
| **檔案** | 自動儲存、多編碼支援（UTF-8、GBK、Latin-1 等）、最近開啟的檔案、多檔案工作階段還原 |

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
git clone https://github.com/Integration-Automation/JEDITOR.git
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
| langchain_openai + langchain_core | AI/LLM 整合 |
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
- **程式碼折疊** -- 從行號區的折疊三角形或鍵盤展開與收合區塊。Python 等以縮排表達區塊的檔案依縮排折疊；C 家族語言（JavaScript、TypeScript、Rust、Go、C/C++、Java、JSON）則以大括號配對折疊，因此單獨一行的大括號一樣能開啟一個區塊。位於字串與註解中的大括號會被略過——字串裡的一個括號會讓後面每一組配對全部錯位。折疊只切換行的顯示與否，完全不修改文字，因此儲存時一定寫入完整檔案。折疊也能自我修復：標頭已不存在的折疊會直接展開，而不是藏錯行。
- **書籤** -- 標記行並以鍵盤在書籤之間跳轉，也可點擊行號區切換。書籤錨定在文字上（透過 `QTextCursor`），因此在其上方插入或刪除行時會跟著程式碼移動，而不會飄掉。
- **多重游標** -- `Ctrl+Shift+L` 在每個選取行的行尾放一個游標，`Ctrl+Alt+N` 在游標所在字詞的下一個出現處加一個，`Ctrl+Alt+Shift+Up` / `Down` 在上一行或下一行加一個，`Alt` + 點擊則可在任意位置新增或移除。所有游標會隨方向鍵、Home 與 End 一起移動，按住 `Shift` 搭配這些鍵則在每個游標各自擴大選取。輸入、Backspace 與 Delete 會在所有游標上生效並算作單一步復原，有選取範圍的位置則以輸入內容取代；`Ctrl+Shift+Esc` 或直接點擊即可回到單一游標。
- **分割檢視**（`Ctrl+Alt+\`）-- 同一份檔案的第二個檢視，兩者共用同一份文件：任一側的編輯會立刻反映到另一側，而捲動位置與游標各自獨立。
- **縮圖**（`Ctrl+Alt+M`）-- 以長條呈現每一行長度與縮排的整檔總覽，並用色帶標示目前螢幕上的範圍。兩側的標記顯示 lint 診斷、git 變更，以及您目前正在尋找的內容——搜尋框開啟時是搜尋命中處，否則是游標所在字詞的其他出現處。點擊或拖曳即可跳轉。大型檔案採取樣繪製，而非逐行繪製。
- **程式碼片段** -- 輸入觸發字後按 Tab 展開，再以 Tab 在佔位符之間移動，每個預設值都會自動選取。重複出現的佔位符只需輸入一次，其餘位置會隨著輸入同步更新。採用常見的 `$1` / `${2:default}` / `$0` 記法，因此既有片段可直接放進 `snippets.json`，並支援各語言專屬的片段集。請從 Tab > 編輯程式碼片段 編輯，而不要手動改檔；檔案缺失或損壞時會退回內建的 Python 片段集。
- **測試面板** -- 從停靠面板執行 pytest 並檢視結果，失敗的項目排在最前面，摘要作為狀態列。選取一筆失敗會在清單下方的窗格顯示其 traceback，覆蓋率方塊則在摘要旁顯示總覆蓋率（需要受測專案安裝 `pytest-cov`）。可執行全部、僅執行選取的項目，或只重跑上次失敗的項目；雙擊一列可在失敗的那一行開啟該測試。
- **語言伺服器支援** -- 非 Python 的檔案可透過 stdio 從語言伺服器取得補全、hover、前往定義、重新命名、格式化、函式簽章提示、尋找參考處、快速修正與文件符號（TypeScript、Rust、Go、C/C++、Lua、JSON 等，可依副檔名設定），Python 則繼續使用 jedi。每個需要伺服器的分頁共用同一個伺服器實例，以「指令 + 專案根目錄」為鍵，而不是每開一個檔案就啟一個行程。診斷會與 ruff 的診斷顯示在同樣的底線與問題面板中。未安裝的伺服器只代表沒有補全，不會產生錯誤。
- **編碼與換行字元** -- 檔案的編碼與換行字元會在開啟時偵測、儲存時原樣寫回，因此修改 CRLF 檔案的一行不會再重寫整份檔案。兩者都可從 File 選單變更；變更編碼會重新讀取未修改的檔案，讓亂碼可以就地修正，且永遠不會丟棄未儲存的內容。
- **儲存時格式化** -- 可選擇在儲存檔案時執行 yapf，並讓游標停留在原本的行上。無法解析的程式碼會原樣保留，而不會阻擋儲存。
- **縮排參考線與行尾空白** -- 每個縮排層級的垂直參考線，以及行尾多餘空白的標示，兩者都可從 UI 風格選單切換。
- **Lint 診斷** -- `ruff` 的檢查結果會在編輯器中以底線標示，並列在問題（Problems）停靠面板中（規則、訊息、行號），雙擊即可跳轉。檢查的是 **緩衝區** 而非磁碟上的檔案，因此未儲存的編輯同樣會被檢查；檢查在停止輸入後於工作執行緒執行，被取代的過時結果會被丟棄。若未安裝 `ruff` 或執行失敗，編輯器只會不顯示診斷，而不會報錯。
- **Git 變更標記** -- 行號區顯示檔案與最後一次提交的差異：綠色長條表示新增、橘色表示修改、細紅線表示該處有行被刪除。以 `F7` / `Shift+F7` 在變更之間跳轉，以 `Ctrl+Alt+Z` 將游標所在的變更還原成已提交的內容（單一步復原），也可從右鍵選單只暫存那一個變更。`Ctrl+Alt+B` 切換行內 blame，顯示最後更動每一行的提交、作者與摘要。Git 選單可開啟整份檔案與 `HEAD` 的並排差異，或與暫存區內容的差異——在逐個變更暫存之後，後者正好顯示哪些部分真的進了索引。右鍵選單同時提供取消整個檔案的暫存與提交已暫存的內容。已提交的版本在檔案開啟時於背景執行緒讀取，比對本身則是純記憶體內的 diff，只在停止輸入後重新計算，因此編輯永遠不必等待 git。不在儲存庫中或尚未提交的檔案就單純不顯示標記。
- **出現處高亮** -- 將游標放在識別字上時，檔案中該識別字的其他完整字詞出現處都會被高亮。關鍵字與單一字元會被忽略，超大檔案則略過掃描，以維持游標移動的即時性。
- **行操作** -- 刪除目前行或選取內容（`Ctrl+Shift+D`）、排序選取的行（`Ctrl+Alt+S`）、將選取的行合併成一行（`Ctrl+Shift+J`），以及（在 Text 選單中）自然排序、移除重複行、移除空白行、反轉行順序，或依分隔符（例如 `=`）對齊。每一項都算作單一步復原。
- **複製行**（`Ctrl+D`）-- 有選取範圍時複製選取內容並選取新的副本，沒有時則複製整行。
- **智慧選取** -- 由字詞 → 行 → 外層縮排區塊 → 整份檔案逐步向外擴大選取（`Ctrl+Alt+Right`），並可逐步縮回（`Ctrl+Alt+Left`）。縮回只會回溯先前的擴大，手動改變選取則會重置歷史。
- **數字加減** -- 將游標處的整數加一或減一（`Ctrl+Alt+Up` / `Ctrl+Alt+Down`），並正確處理負號與位數變化。
- **檔案內重新命名**（`F2`）-- 將游標所在識別字在整份檔案中的每個完整字詞出現處一次改名，算作單一步復原。字詞邊界可保護部分符合的情況（改 `val` 絕不會動到 `value`）。
- **導覽歷史** -- 像瀏覽器一樣在游標跳轉歷史中往前往後（`Alt+Left` / `Alt+Right`）。一次跳轉會同時記錄來源與目的地，因此「返回」會回到您原本所在的位置。
- **文件大綱** -- 可停靠的樹狀面板，列出目前檔案的類別、方法、函式與模組層級變數。Python 以 `ast` 解析，不會執行任何程式碼；其他語言則向其語言伺服器詢問，因此 TypeScript 或 Rust 檔案同樣有大綱。雙擊即可跳到定義。
- **鍵盤快捷鍵**（UI 風格 > 鍵盤快捷鍵）-- 所有指令的按鍵集中在一份可編輯的清單中。兩個指令不能共用同一組按鍵，因為發生這種情況時 Qt 兩個都不會執行；改動立即生效，而且只有與預設值不同的項目會被記錄。
- **變數檢查器** -- 在程式執行期間檢查與除錯變數。

### 導覽

- **指令面板**（Ctrl+Shift+A）-- 以名稱或選單路徑模糊搜尋任何選單指令並直接執行，不必在選單中翻找。結果依照字詞邊界、連續字元與前綴排序，每一列也會顯示該指令自己的快捷鍵。
- **快速開啟／前往檔案**（Ctrl+P）-- 以檔名 *或* 資料夾路徑模糊搜尋專案樹。索引在背景執行緒建立，並略過版本控制、快取、虛擬環境與建置目錄以及二進位檔案類型。開頭輸入 `>` 可將同一個選擇器切換成指令模式。
- **前往符號**（Ctrl+Shift+O）-- 跳到目前 Python 檔案中的任何類別、函式、方法或模組層級變數。符號以標準函式庫的 `ast` 模組解析，因此絕不會執行使用者程式碼；無法解析的檔案在您輸入時只會沒有符號，而不會報錯。
- **TODO 面板**（Tab > 工具，或作為停靠面板）-- 掃描專案中的 `TODO`、`FIXME`、`HACK`、`XXX`、`BUG`、`NOTE` 與 `OPTIMIZE` 註解，涵蓋 Python、C 系、HTML、SQL 等註解樣式。可依標籤篩選，雙擊一列即可在該行開啟檔案。標籤只有出現在註解符號之後才會被回報，因此一般字串不會被誤判。

### 程式執行與除錯

- **執行 Python 腳本**（F5）-- 執行目前檔案並即時串流輸出。
- **除錯模式**（F9）-- 啟動 Python 除錯器進行逐步除錯，可從行號區切換中斷點（`Ctrl+F9`）。
- **Shell 指令** -- 在編輯器內直接執行任意 Shell/終端機指令。
- **虛擬環境偵測** -- 自動偵測並啟用 Python 虛擬環境。
- **程序管理** -- 停止單一或所有執行中的程序。
- **錯誤高亮** -- 錯誤訊息在輸出面板中以紅色顯示。

### 程式碼品質與格式化

- **YAPF Python 格式化**（Ctrl+Shift+Y）-- 使用 Google 風格自動格式化 Python 程式碼。
- **PEP8 檢查**（Ctrl+Alt+P）-- 驗證程式碼是否符合 PEP8 風格指南。
- **Ruff 靜態分析** -- 在背景執行緒中執行快速且全面的 Python 靜態分析。
- **JSON 重新格式化**（Ctrl+J）-- 美化列印並驗證 JSON 內容。
- **移除行尾空白**（Text 選單）-- 去除每一行結尾的空白，算作單一步復原，並保留游標位置。
- **轉換縮排**（Text 選單）-- 在 Tab 與空格之間轉換前導縮排（依您設定的縮排大小）。只處理前導空白，因此字串內的 Tab 與空格永遠不會被更動。
- **可設定的縮排寬度** -- Tab 縮排、取消縮排與 Enter 自動縮排都依照設定的縮排大小（`Text > Indent Size`），而開啟檔案時也會從檔案本身的內容自動偵測縮排寬度。
- **文字轉換**（Text 選單）-- 大小寫轉換（大寫／小寫／互換／標題式）、命名風格轉換（`snake_case` / `camelCase` / `PascalCase` / `kebab-case`）、進位制轉換（十六進位／十進位／二進位），以及編碼解碼工具（Base64、URL、HTML 實體、JSON 字串跳脫）。解碼失敗時原文保持不變。
- **統計**（Text 選單）-- 整份文件或目前選取範圍的行數、字數與字元數。

### 檔案操作

- **建立、開啟、儲存**檔案，使用標準快捷鍵（Ctrl+N、Ctrl+O、Ctrl+S）。
- **開啟資料夾**（Ctrl+K）-- 瀏覽專案目錄結構。
- **自動儲存** -- 自動定期儲存檔案，防止資料遺失。
- **工作階段還原** -- 重新開啟上次關閉時所有開著的檔案，而不只是最後一個。不存在、重複與已開啟的檔案會被略過，清單有上限，損壞或手動改過的設定檔也絕不會擋住啟動。可在 `.jeditor/user_setting.json` 中將 `restore_session` 設為 `false` 停用。
- **多編碼支援** -- 無縫處理 UTF-8、GBK、Latin-1 及其他編碼，具備自動偵測功能。
- **最近開啟的檔案** -- 快速存取先前開啟的檔案。

### Git 整合

- **分支管理** -- 從工具列列出、切換與檢出分支。
- **提交歷史** -- 以表格形式檢視提交的中繼資料（作者、日期、訊息），並附有依泳道著色的提交圖。
- **並排差異檢視器** -- 具有行號的彩色高亮比較，可比對 `HEAD` 或索引。
- **多檔案差異** -- 比較多個檔案間的變更，每個檔案一個分頁。
- **暫存區操作** -- 暫存或取消暫存整個檔案，也可從編輯器的行號區逐個變更暫存。
- **擱置（Stash）** -- 把目前的變更先收起來、列出擱置的內容，並可取回其中一筆。
- **衝突解決** -- 列出合併後仍處於衝突的檔案，並可選擇保留其中一方來解決。
- **稽核日誌** -- 記錄所有 Git 操作，方便追蹤與合規。

### AI 助手

- **透過 LangChain 連接 OpenAI 模型** -- 連接 OpenAI 的語言模型。
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

| 類型 | 用途 |
|---|---|
| 程式語言 | 為新語言新增語法高亮 |
| 自然語言 | 為新語系新增 UI 翻譯 |
| 執行設定 | 定義自訂執行環境 |
| 外掛中繼資料 | 提供外掛版本與作者資訊 |

外掛會自動從 `jeditor_plugins/` 目錄中探索，也可以在編輯器內瀏覽並安裝。詳見[外掛開發](#外掛開發)。

### 主題與自訂

- **深色/淺色主題** -- Qt Material 主題；編輯器本身的顏色會跟隨視窗樣式。
- **字型自訂** -- 分別變更編輯器與 UI 的字型家族與大小。
- **可停靠面板** -- 透過停靠/取消停靠面板重新排列 UI 布局。
- **系統匣** -- 將編輯器最小化至系統匣。
- **工具列** -- JetBrains 風格的快速操作按鈕，包含目前的 Git 分支。

### 多語言介面

- **英文**、**繁體中文**、**简体中文** 與 **日本語** -- 四種都是完整的。简体中文以中國大陸的用詞直接撰寫，而非由繁體轉換——檔案/文件、資料夾/文件夹、程式/程序 這些詞在兩地並不相同。
- **首次啟動跟隨系統** -- 語言取自系統的地區設定，而不是一律預設英文；中文依書寫系統判斷：`zh-Hant` 以及台灣、香港、澳門地區使用繁體，其餘使用簡體。偵測到的結果會被記錄下來，之後就單純是您所選的語言。
- **不需重啟即可切換** -- 選擇語言後，選單、工具列、面板、分頁與狀態列會立刻換成新語言。分頁上的檔名與分支名稱保持不變。
- **回退英文** -- 某個語言尚未翻譯的字串會顯示英文原文，而不是空白標籤，因此一種語言可以在尚未完成時就先加入。
- **可擴展** -- 透過外掛系統新增更多語言。韓文、西班牙文、法文、德文、俄文與葡萄牙文的地區判斷規則都已就緒，各自只差一份字典。

---

## 鍵盤快捷鍵

| 快捷鍵 | 動作 |
|---|---|
| `Ctrl+N` | 新增檔案 |
| `Ctrl+O` | 開啟檔案 |
| `Ctrl+K` | 開啟資料夾 |
| `Ctrl+S` | 儲存檔案 |
| `Ctrl+Shift+S` | 儲存所有已修改的分頁 |
| `Ctrl+Shift+A` | 指令面板 |
| `Ctrl+P` | 快速開啟（前往檔案） |
| `Ctrl+Shift+O` | 前往符號 |
| `Ctrl+Shift+[` | 切換游標所在的折疊 |
| `Ctrl+Alt+[` | 全部折疊 |
| `Ctrl+Alt+]` | 全部展開 |
| `Ctrl+Alt+K` | 切換書籤 |
| `Ctrl+Alt+L` | 下一個書籤 |
| `Ctrl+Alt+J` | 上一個書籤 |
| `Alt+Left` | 往前導覽 |
| `Alt+Right` | 往後導覽 |
| `Ctrl+Shift+D` | 刪除目前行／選取內容 |
| `Ctrl+Alt+S` | 排序選取的行 |
| `Ctrl+Shift+J` | 合併選取的行 |
| `Ctrl+Alt+Right` | 擴大選取範圍 |
| `Ctrl+Alt+Left` | 縮回選取範圍 |
| `Ctrl+Alt+Up` | 游標處的數字加一 |
| `Ctrl+Alt+Down` | 游標處的數字減一 |
| `F2` | 檔案內重新命名所有出現處 |
| `Ctrl+Shift+L` | 在每個選取行的行尾放一個游標 |
| `Ctrl+Alt+N` | 在下一個出現處加一個游標 |
| `Ctrl+Alt+Shift+Up` / `Ctrl+Alt+Shift+Down` | 在上一行／下一行加一個游標 |
| `Ctrl+Shift+Esc` | 回到單一游標 |
| `Ctrl+Shift+R` | 開始／結束錄製巨集 |
| `Ctrl+Shift+G` | 重播巨集 |
| `Ctrl+Alt+E` | 最近位置 |
| `Ctrl+Alt+\` | 切換分割檢視 |
| `Ctrl+Alt+M` | 切換縮圖 |
| `F7` / `Shift+F7` | 下一個／上一個變更 |
| `Ctrl+Alt+Z` | 還原游標所在的變更 |
| `Ctrl+Alt+B` | 切換行內 blame |
| `Ctrl+J` | 重新格式化 JSON |
| `Ctrl+Shift+Y` | YAPF Python 格式化 |
| `Ctrl+Alt+P` | PEP8 格式檢查 |
| `Ctrl+F` | 搜尋文字（編輯器、瀏覽器） |
| `Ctrl+Shift+F` | 跨檔案搜尋 |
| `Alt+W` | 自動換行 |
| `Ctrl+Shift+P` | 以 pip 安裝套件 |
| `Ctrl+Shift+U` | 升級與安裝套件 |
| `Ctrl+Shift+V` | 切換 Python 直譯器 |
| `Ctrl+H` | 搜尋與取代 |
| `Ctrl+G` | 跳到指定行 |
| `F5` | 執行程式 |
| `F9` | 除錯 |
| `Shift+F5` | 停止程式 |
| `Ctrl+F9` | 切換中斷點 |
| `Ctrl+F5` | 除錯器：繼續執行 |
| `F10` / `F11` / `Shift+F11` | 除錯器：逐步跳過／進入／跳出 |
| `Ctrl+D` | 複製行／選取內容 |
| `Ctrl+/` | 切換註解 |
| `Alt+Up` / `Alt+Down` | 將該行上移／下移 |
| `Ctrl+B` | 跳到游標處符號的定義 |
| `Ctrl+Shift+\` | 跳到對應的括號 |
| `Ctrl++` 或 `Ctrl+=` / `Ctrl+-` | 放大／縮小編輯器字型 |

上表所有快捷鍵都可從 **UI 風格 > 鍵盤快捷鍵** 重新指派；`Ctrl++` 與 `Ctrl+=` 是兩個各自獨立的
放大指令，可以分別修改。以下按鍵由編輯區或主控台本身處理，因此是固定的：

| 快捷鍵 | 動作 |
|---|---|
| `Tab` / `Shift+Tab` | 將該行或選取內容縮排／取消縮排 |
| `上/下方向鍵` | 指令歷史（主控台） |

---

## 專案架構

```
je_editor/
├── pyside_ui/          GUI 層（PySide6）
│   ├── browser/        內嵌網頁瀏覽器
│   ├── code/           編輯器本體：語法、折疊、lint、LSP、git 標記、
│   │                   多重游標、程式碼片段、縮圖、行程執行
│   ├── dialog/         搜尋與取代、快捷鍵、程式碼片段、檔案對話框
│   ├── git_ui/         Git 用戶端、提交圖、差異檢視器
│   └── main_ui/        主視窗、選單、工具列、面板、設定、AI、主控台
├── code_scan/          Ruff 執行與 watchdog 檔案監控
├── git_client/         Git 操作（GitPython + git CLI）
├── plugins/            外掛註冊表與載入器
└── utils/              純邏輯，不依賴 Qt：diff、折疊、模糊比對、符號、
                        LSP 協定、編碼、快捷鍵、翻譯
```

功能都拆成兩半來建構：演算法放在 `utils/` 中且不 import Qt，`pyside_ui/` 中的一層輕薄管理器再把它接到元件上。以折疊為例，就是 `utils/code_folding/` 加上 `pyside_ui/code/folding/`。這正是上面大部分行為都能不開視窗就測試的原因。

逐模組的參考——每個檔案做什麼、執行緒模型、全域單例與設定布局——記錄在 **[`architecture_explore.md`](../architecture_explore.md)** 中。

---

## 外掛開發

在工作目錄中的 `jeditor_plugins/` 目錄裡建立外掛。每個外掛都是一個 Python 模組，會在被 import 時註冊它所提供的內容。

### 1. 程式語言外掛

為新語言新增語法高亮：

```python
from je_editor.plugins import register_programming_language

register_programming_language(
    suffix=".rs",
    syntax_words={"keywords": ["fn", "let", "mut", "struct", "impl", "enum"]},
    syntax_rules={"keyword_color": "#FF6600"},
)
```

### 2. 自然語言外掛

新增 UI 翻譯：

```python
from je_editor.plugins import register_natural_language

register_natural_language(
    language_key="ja",
    display_name="Japanese",
    word_dict={"file": "ファイル", "edit": "編集", "run": "実行"},
)
```

### 3. 執行設定外掛

教會 **Run with...** 選單如何執行另一種語言。直譯型語言只需要一個編譯器與它的參數：

```python
from je_editor.plugins import register_plugin_run_config

register_plugin_run_config({
    "name": "Go",             # shown in the menu
    "suffixes": (".go",),     # file types this applies to
    "compiler": "go",         # executable
    "args": ("run",),         # arguments before the file path
})
# runs: go run file.go
```

編譯型語言則加上 `compile_then_run` 以及指定輸出二進位檔名的旗標：

```python
register_plugin_run_config({
    "name": "C (GCC)",
    "suffixes": (".c",),
    "compiler": "gcc",
    "args": (),
    "compile_then_run": True,
    "output_flag": "-o",
})
# compiles: gcc file.c -o file    then runs the result
```

完整指南，包含外掛中繼資料與打包，請參閱 [`PLUGIN_GUIDE.md`](../PLUGIN_GUIDE.md)。

---

## 設定檔

JEDITOR 將使用者設定儲存在工作目錄中的 `.jeditor/` 目錄裡：

| 檔案 | 內容 |
|---|---|
| `user_setting.json` | 一般偏好設定（字型、主題、語言、最近開啟的檔案、開啟中的分頁、重新指派過的快捷鍵） |
| `user_color_setting.json` | 編輯器與輸出的配色，含語法高亮 |
| `snippets.json` | 您自己的程式碼片段，疊加合併在內建片段集之上 |
| `ai_config.json` | AI 助手設定——啟動時讀取、從不寫入，需自行建立 |

每個檔案在被重寫前都會備份到 `<name>.bak`。

---

## 文件

完整文件請參閱：
**[https://je-editor.readthedocs.io/en/latest/](https://je-editor.readthedocs.io/en/latest/)**

---

## 參與貢獻

歡迎貢獻！請在 [GitHub](https://github.com/Integration-Automation/JEDITOR) 上提交 Issue 與 Pull Request。

---

## 授權條款

本專案採用 **MIT 授權條款**。詳見 [LICENSE](../LICENSE)。

Copyright (c) 2021 ~ Now JE-Chen
