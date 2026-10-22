# 程式審核：JEDITOR

## 審核者

工作區程式審核。日期：2026-10-22。對象：`JEDITOR`（`je_editor`）。結論：需修正。

## 審核規範

共通規範在工作區 repo [JE-Chen/Codes](https://github.com/JE-Chen/Codes) 的 `docs/code-review-standard.md`。下面留下 2026-10-22 這次審核所用的條款，讓審核紀錄的依據對得上那一次。之後的審核以工作區那份為準。本專案更嚴的條款仍以本節與本專案的 `CLAUDE.md` 為準。

本次用下列 10 條。專案準則比這裡更嚴的，從嚴；見〈本專案加嚴〉。

1. 設計：邏輯與介面分層，不阻塞 UI 執行緒，執行緒與子程序要收得掉。
2. 可讀性：認知複雜度 15、函式 80 行、巢狀 4 層、參數 7 個、行長 120。
3. 錯誤處理：禁止裸 `except`；要指名例外，記錄或再拋出，並以 `from` 串接。
4. 死碼：沒有呼叫點的函式、參數與分支。
5. 型別與 docstring：公開函式要有型別與用途說明。
6. 安全：禁止對使用者輸入使用 `shell=True`、`eval`／`exec`、`pickle`、不安全的 YAML、`verify=False`；寫檔要防路徑跳出。
7. 測試：熱點是否有契約或回歸測試可對上（本次不執行測試）。
8. 效能：子程序、檔案與網路不得佔住 UI 執行緒。
9. §6 契約：給 PyBreeze 用的名稱要寫在 `architecture.md` §6；沒寫下來只列建議，不當成已破壞。
10. 文件同步：`architecture.md`、`CLAUDE.md`、`PROGRESS.md` 與程式一致。

嚴重度只有三種：缺陷、建議、備註。通過＝沒有未關閉缺陷。有條件通過＝沒有立即損害。需修正＝有未關閉缺陷。

## 審核紀錄

### 方法

讀 `architecture.md`（含 §6）、`CLAUDE.md` 的長度與安全段落、`PROGRESS.md` 前 80 行。在 `je_editor/` 搜尋 `eval(`、`exec(`、`shell=True`、`pickle`、`yaml.load`、`verify=False`、裸 `except:`，排除 `test/`、`build/`、`dist/`、`__pycache__/`。每一則發現都對過原始檔。沒有執行測試、沒有啟動介面、沒有改其他檔。

### 總評

執行程式、Git、ruff、本機工作與遠端 ssh 都以引數清單呼叫，且 `shell=False`。存檔先編碼再以 `"wb"` 寫入，插件下載檔名有擋出路徑。點名要核對的八個 PyBreeze 名稱都已寫在 §6，不構成契約缺口。

未關閉的問題是：建立 venv 與 pip 安裝把套件名稱送進唯一的 `shell=True`。在 Windows 上這會進到 `cmd.exe /c`，`>=`、`&` 這類字元不會被當成套件名稱。這會讓「安裝套件」做出使用者沒打算做的事，所以結論是需修正，不是有條件通過。

### 發現

#### CR-01

- 嚴重度：缺陷
- 狀態：未關閉
- 位置：`je_editor/pyside_ui/code/shell_process/shell_exec.py` 第 81–100 行；呼叫點 `je_editor/pyside_ui/main_ui/menu/python_env_menu/build_venv_menu.py` 第 102、194–196、224–226 行。同檔第 122–152 行的 `shell_pip_install` 沒有呼叫點。
- 說明：`ShellManager.exec_shell` 一律 `shell=True`。Windows 保留 list，再由 `subprocess` 組成 `cmd.exe /c "..."`；其他平台用空白把 list 接成一字串。註解寫這只服務「使用者自己打的 shell 指令」，但建立 venv 與 pip 也走這裡，套件名稱來自輸入框，沒有加引號。`cmd.exe` 在 `/C` 字串含 `&`、`>` 時會拆掉外層引號，`requests>=2.28` 會變成重新導向，`name&其他指令` 會再跑一段指令。非 Windows 的 `" ".join` 連空白路徑都會拆開。`shell_pip_install` 是同一模式的死碼。另外第 77 行把整段指令寫進日誌；shell 選單傳入的是編輯器全文。
- 依據：`CLAUDE.md`〈Security (mandatory)〉禁止對使用者輸入使用 `shell=True`；〈Exceptions & Resources〉禁止只接住卻不記錄的籠統例外（第 107 行 `except Exception` 只顯示在輸出區）。規範 4、6。
- 建議：venv 與 pip 改成引數清單且 `shell=False`，套件名稱單獨一個引數。`shell=True` 只留在使用者明確要跑 shell 的入口，並改掉與呼叫點不符的註解。刪除或接上 `shell_pip_install`。日誌只記長度或動作名稱，不要記全文。

#### CR-02

- 嚴重度：建議
- 狀態：未關閉
- 位置：`je_editor/pyside_ui/code/code_process/code_exec.py` 第 127–220 行，其中第 161–167 行。選單從 `je_editor/pyside_ui/main_ui/menu/run_menu/under_run_menu/build_program_menu.py` 第 81 行直接呼叫。
- 說明：`compile_then_run` 在呼叫端（UI 執行緒）對編譯程序 `communicate(timeout=60)`。一般執行路徑有讀取執行緒，這條沒有。逾時丟出的 `TimeoutExpired` 被第 213 行 `except Exception` 接住，收拾的是 `self.process`，不是這個 `compile_process`，編譯程序不會被結束。函式本體約 94 行，超過 80 行硬上限。
- 依據：`CLAUDE.md`〈Design Principles〉子程序不得佔住 UI 執行緒；〈Code Style〉函式硬上限 80 行（建議 50）。規範 1、2、8。
- 建議：編譯改到工作執行緒；逾時時對該程序 `terminate`／`kill`。把編譯與執行拆開，使每個函式不超過硬上限。

#### CR-03

- 嚴重度：建議
- 狀態：未關閉
- 位置：`je_editor/pyside_ui/main_ui/plugin_browser/github_api.py` 第 23–29、79–84、171、184 行。寫入邊界在第 32–63 與 155–157 行，這一段沒有問題。
- 說明：下載目的地會拒絕 `..`、絕對路徑與兩種分隔符，寫入落在插件目錄內。缺口在網址：允許的 scheme 含 `http`，註解還把字面值拆開以避開檢查；`owner`／`repo` 直接插進網址（`branch` 才有編碼）；後續 `url` 與 `download_url` 只檢查 scheme 前綴，不限制主機，`urlopen` 會跟著重新導向。清單本身來自 `https://api.github.com`，目前預設倉庫不會自己改寫這些欄位，所以不當成已可利用的缺陷。下載的 `.py` 下次啟動會被 `plugin_loader` 匯入執行，這是插件功能，不是路徑跳出。
- 依據：`CLAUDE.md`〈Security (mandatory)〉外部輸入要在邊界檢查；TLS 不關閉驗證（此處沒有 `verify=False`，但放行 `http`）。規範 6。
- 建議：只允許 `https`，主機限 `api.github.com` 與 `raw.githubusercontent.com`，`owner`／`repo` 比照 `branch` 編碼，並拒絕跨主機重新導向。保留現有檔名檢查。

#### CR-04

- 嚴重度：建議
- 狀態：未關閉
- 位置：`je_editor/pyside_ui/dialog/search_ui/search_replace_widget.py` 第 422–430、539–602 行。對照第 495–522 與 608–630 行。
- 說明：單筆取代會先 `resolve`，不在工作區根目錄內就拒絕。目錄全部取代對使用者選的資料夾（有確認框）或工作區根目錄做 `os.walk`，再對走出的路徑 `write_text`。`os.walk` 預設不進入目錄符號連結，但檔案符號連結會被寫穿，目標可以在所選目錄之外。使用者已選定目錄，所以不是未授權寫入；與單筆路徑的檢查不一致。
- 依據：`CLAUDE.md`〈Security (mandatory)〉使用者提供的路徑要驗證，專案目錄內拒絕跳出。規範 6。
- 建議：寫入前對檔案做 `resolve`，父目錄必須仍在本次選定的根目錄之下；或與 `_locate_in_project` 共用同一判斷。

#### CR-05

- 嚴重度：建議
- 狀態：未關閉
- 位置：`architecture.md` §6（約第 184–206 行）沒有這兩個名稱；契約測試在 `test/test_public_api_contract.py` 第 117–120 行。實作在 `je_editor/pyside_ui/code/plaintext_code_edit/code_edit_plaintext.py` 第 422 與 2391 行。
- 說明：本次點名的 `PluginBrowserWidget`、`DestroyDock`、`check_and_choose_venv`、`choose_file_get_save_file_path`、`write_file`、`actually_color_dict`、`english_word_dict`、`traditional_chinese_word_dict` 都已寫在 §6，也存在於套件內，不列為缺陷或「契約未寫」。同份契約測試另外釘住 `CodeEditor.load_git_baseline` 與 `start_language_server`（參數只有 `self`），§6 只寫了 `reset_highlighter`。
- 依據：規範 9、10；`architecture.md` §8 要求跨倉庫契約變更時更新 §6。
- 建議：在 §6 補上這兩個方法與「參數只有 self」。不要改動已寫上的八個名稱。

沒有其他未關閉缺陷。裸 `except:`、`eval(`、`pickle`、`yaml.load`、`verify=False` 在套件原始碼中沒有出現，不另開項目。

### 已核對

- §6 已記載上述八個名稱，以及 `FullEditorWidget`、`user_setting_dict`、自動存檔三個名稱、`RedirectStdErr`、`DEFAULT_ENCODING`、`LINE_ENDING_LF`、`write_file_with_encoding`。`test/test_public_api_contract.py` 的模組路徑與這份清單一致。
- `exec(` 的符合點都是 Qt 的 `QDialog.exec`／`QMenu.exec`，不是 Python `exec`。`re.compile` 不是對不受信任程式做 `compile`。
- 除 CR-01 外，`subprocess` 都是引數清單且 `shell=False`（`code_exec.py` 一般執行、`git_cli.py`、`ruff_lint.py`、`local_task_runner.py`、工具列 git）。遠端操作經 `ssh` 引數清單；`shlex.join` 給遠端 shell 加 POSIX 引號。`forward_port` 會拒絕不符合主機字元規則的名稱。Windows 遠端引號已記在 `PROGRESS.md` #14，不另開。
- 「在 shell 執行編輯器文字」（`build_shell_menu.py` 第 81–83 行）是明示功能，不是本項缺陷；缺陷是 venv／pip 共用這個入口。
- `write_file`／`write_file_with_encoding` 先編碼再 `"wb"` 寫入，失敗轉成 `JEditorSaveFileException`。呼叫端是存檔對話框、自動存檔與編碼動作，路徑來自已開啟檔或使用者選的檔。`write_file` 本身是給下游的寫入原語，沒有再做根目錄限制。
- AI 設定自己寫檔，日誌只記路徑；`.gitignore` 含 `**/.jeditor`。`write_json` 仍把整份設定記進日誌（最近開啟的檔案路徑），目前字典沒有金鑰。備註，不單列。
- `check_and_choose_venv` 先在給定的 venv 目錄找直譯器，找不到才退回系統 `python`。`DestroyDock` 關閉時釋放內部 widget。
- 插件 `register()` 以 `importlib` 載入本機 `jeditor_plugins/`，不是 `eval`。中繼資料用逐行拆 `=`，不執行下載內容。

### 未涵蓋

沒有跑 ruff、pytest，也沒有量完全部函式的複雜度、行長與巢狀。`pyside_ui` 裡超過 50 行的 UI 函式沒有逐一列出。日誌大量使用 f-string，與「logging 用 lazy `%`」不符，本次不逐條開項目。沒有對照 PyBreeze 工作樹，§6 以外的下游屬性只以本倉庫的契約測試為準。`exe/`、`scripts/`、`docs/` 不在套件熱點內。

### 本專案加嚴

`CLAUDE.md`〈Code Style〉函式建議不滿 50 行，硬上限 80；認知複雜度小於 15，循環複雜度小於 10。本次缺陷線用 80 行，50 行只在 CR-02 提醒。同檔禁止裸 `except` 與 `except Exception` 後忽略；安全節禁止 `shell=True`、不可信輸入上的 `eval`／`exec`／`pickle`，並要求路徑檢查與不得 `verify=False`。〈Design Principles〉與 `architecture.md` §7 要求子程序離開 UI 執行緒。

### 結論

需修正。未關閉缺陷 1 則（CR-01），建議 4 則（CR-02 至 CR-05）。CR-01 關閉後，其餘不構成立即損害，可改判有條件通過。點名的八個 PyBreeze 名稱已在 §6，沒有當成契約破壞。
