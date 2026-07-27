設定與配置
===========

JEditor 將所有使用者設定儲存在目前工作目錄下的 ``.jeditor/`` 資料夾中。
設定會在首次啟動時自動建立，並在不同工作階段之間持續保留。

設定檔案
---------

user_setting.json
^^^^^^^^^^^^^^^^^^

主要設定檔控制編輯器的行為與外觀：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 設定項目
     - 說明
   * - ``ui_font``
     - 主 UI 的字型系列（選單、面板、對話框）
   * - ``ui_font_size``
     - 主 UI 的字型大小
   * - ``font``
     - 程式碼編輯器的字型系列
   * - ``font_size``
     - 程式碼編輯器的字型大小
   * - ``language``
     - UI 語言（``English``、``Traditional Chinese``、``Simplified Chinese``、
       ``Japanese`` 或插件提供的語言）。首次啟動時取自系統地區設定。
   * - ``ui_style``
     - UI 主題樣式檔，例如 ``dark_amber.xml``
   * - ``encoding``
     - 預設檔案編碼（``utf-8``、``GBK``、``latin-1``）
   * - ``last_file``
     - 上次開啟的檔案路徑（啟動時恢復）
   * - ``python_compiler``
     - 用於程式碼執行的 Python 直譯器路徑
   * - ``max_line_of_output``
     - 輸出面板的最大行數（預設：200,000）
   * - ``recent_files``
     - 最近開啟的檔案清單
   * - ``indent_size``
     - 縮排大小（空格數，預設：4）
   * - ``open_files``
     - 上次關閉時開啟的分頁
   * - ``restore_session``
     - 啟動時是否重新開啟這些分頁（預設：``true``）
   * - ``shortcuts``
     - 使用者改過的快捷鍵；只記錄與預設值不同的項目

user_color_setting.json
^^^^^^^^^^^^^^^^^^^^^^^^

控制編輯器與輸出的色彩配置：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 設定項目
     - 說明
   * - ``line_number_color``
     - 行號文字
   * - ``line_number_background_color``
     - 行號區域背景
   * - ``current_line_color``
     - 目前行高亮
   * - ``normal_output_color`` / ``error_output_color`` / ``warning_output_color``
     - 輸出面板文字
   * - ``syntax_keyword_color`` / ``syntax_string_color`` /
       ``syntax_comment_color`` / ``syntax_number_color``
     - 語法高亮
   * - ``diff_added_marker_color`` / ``diff_modified_marker_color`` /
       ``diff_removed_marker_color``
     - 行號區的 Git 變更標記
   * - ``blame_annotation_color``
     - 行內 blame 文字
   * - ``lint_underline_color``
     - lint 診斷的底線
   * - ``bookmark_marker_color`` / ``fold_marker_color`` /
       ``breakpoint_marker_color``
     - 行號區的各種標記
   * - ``occurrence_highlight_color``
     - 游標所在字詞的其他出現處
   * - ``extra_cursor_color``
     - 額外的游標
   * - ``indent_guide_color`` / ``trailing_whitespace_color``
     - 縮排參考線與行尾空白的標示
   * - ``minimap_background_color`` / ``minimap_line_color`` /
       ``minimap_viewport_color``
     - 縮圖

所有顏色以 RGB 陣列指定，例如 ``[255, 0, 0]`` 代表紅色。未列出的項目會沿用目前主題的
數值，因此只寫部分設定也沒問題。

ai_config.json
^^^^^^^^^^^^^^^

AI 助手設定（詳見 :doc:`ai_assistant`）：

- API Base URL
- API 金鑰
- 模型名稱
- 系統提示詞範本

與上面兩個檔案不同，這個檔案只會被讀取、不會被寫入——若希望每次啟動都載入設定，請自行
建立它。

主題
-----

JEditor 透過 `qt-material <https://github.com/UN-GCPCS/qt-material>`_ 支援深色和淺色主題：

- **預設：** Dark Amber 主題
- 從 **UI Style** 選單切換主題
- 編輯器本身的顏色會跟隨視窗樣式：切換到淺色主題時，行號區、目前行與語法顏色也會換成
  淺色的一組。您自己挑過的顏色不會被蓋掉——只有仍是預設值的項目會跟著主題走

字型自訂
---------

JEditor 為 UI 和程式碼編輯器提供獨立的字型設定：

**UI 字型：**
- 從 **File** 選單變更
- 影響選單、面板、對話框和按鈕
- 字型系列和大小可獨立設定

**編輯器字型：**
- 從 **Text** 選單變更
- 僅影響程式碼編輯區域
- 字型系列和大小可獨立設定
- 變更立即生效

可停靠面板
-----------

JEditor 的 UI 採用 Qt 的停靠元件系統，面板可重新排列：

- **編輯器** — 主要的程式碼編輯區域
- **輸出** — 程式碼執行結果
- **檔案樹** — 專案目錄瀏覽器
- **主控台** — Shell / IPython 主控台
- **AI 聊天** — AI 助手面板
- **Git** — Git 客戶端面板、分支樹與差異檢視器
- **瀏覽器** — 內建網頁瀏覽器
- **變數檢視器** — 執行期間的變數除錯
- **問題** — lint 與語言伺服器的診斷
- **大綱** — 目前檔案的類別、函式與變數
- **測試** — pytest 的結果、失敗與覆蓋率
- **TODO** — 掃描整個專案找到的 ``TODO`` / ``FIXME`` / ``HACK`` 註解

所有面板都可以：

- 拖曳到視窗內的不同位置
- 浮動為獨立視窗
- 在同一停靠區域內堆疊為分頁
- 從 **Dock** 選單隱藏或恢復

系統匣
-------

JEditor 支援系統匣整合：

- 最小化到系統匣而非關閉
- 系統匣圖示可快速恢復視窗
- 最小化時繼續在背景運行

多語言 UI
----------

**內建語言：**

- English
- 繁體中文
- 简体中文
- 日本語

四種語言都是完整的。简体中文是以中國大陸的用詞直接撰寫，而非由繁體轉換——檔案/文件、
資料夾/文件夹、程式/程序 這些詞在兩地並不相同。

**跟隨系統：**

首次啟動時，語言取自系統的地區設定，而不是一律預設英文。中文依書寫系統判斷：
``zh-Hant`` 以及台灣、香港、澳門地區使用繁體，其餘使用簡體。偵測到的結果會寫入
``user_setting.json``，之後就單純是您所選的語言。

**切換語言：**

從 **Language** 選單選擇語言。不需要重新啟動——選單、工具列、面板、分頁與狀態列會立刻
換成新語言。分頁上的檔名與分支名稱則保持不變。

**回退機制：**

某個語言尚未翻譯的字串會顯示英文原文，而不是空白標籤，因此一種語言可以在尚未完成時就
先加入。

**透過插件新增語言：**

可透過插件系統新增額外語言（詳見 :doc:`plugins`）。韓文、西班牙文、法文、德文、俄文與
葡萄牙文的地區判斷規則都已就緒，各自只差一份字典。
