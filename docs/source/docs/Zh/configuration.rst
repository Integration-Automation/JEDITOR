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
   * - ``ui_font_family``
     - 主 UI 的字型系列（選單、面板、對話框）
   * - ``ui_font_size``
     - 主 UI 的字型大小
   * - ``editor_font_family``
     - 程式碼編輯器的字型系列
   * - ``editor_font_size``
     - 程式碼編輯器的字型大小
   * - ``language``
     - UI 語言（``English``、``Traditional Chinese`` 或插件提供的語言）
   * - ``theme``
     - UI 主題風格（深色或淺色 Material 主題）
   * - ``encoding``
     - 預設檔案編碼（``UTF-8``、``GBK``、``Latin-1``）
   * - ``last_open_file``
     - 上次開啟的檔案路徑（啟動時恢復）
   * - ``python_compiler``
     - 用於程式碼執行的 Python 直譯器路徑
   * - ``max_output_lines``
     - 輸出面板的最大行數（預設：200,000）
   * - ``recent_files``
     - 最近開啟的檔案清單
   * - ``indent_size``
     - 縮排大小（空格數，預設：4）

user_color_setting.json
^^^^^^^^^^^^^^^^^^^^^^^^

控制編輯器與輸出的色彩配置：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 設定項目
     - 說明
   * - ``line_number_color``
     - 行號文字的 RGB 顏色
   * - ``line_number_bg_color``
     - 行號區域背景的 RGB 顏色
   * - ``current_line_color``
     - 目前行高亮的 RGB 顏色
   * - ``normal_output_color``
     - 正常輸出文字的 RGB 顏色
   * - ``error_output_color``
     - 錯誤輸出文字的 RGB 顏色
   * - ``warning_output_color``
     - 警告輸出文字的 RGB 顏色

所有顏色以 RGB 陣列指定，例如 ``[255, 0, 0]`` 代表紅色。

ai_config.json
^^^^^^^^^^^^^^^

AI 助手設定（詳見 :doc:`ai_assistant`）：

- API Base URL
- API 金鑰
- 模型名稱
- 系統提示詞範本

主題
-----

JEditor 透過 `qt-material <https://github.com/UN-GCPCS/qt-material>`_ 支援深色和淺色主題：

- **預設：** Dark Amber 主題
- 從 **UI Style** 選單切換主題
- 主題變更可能需要重新啟動應用程式才能完全生效

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
- **Git** — Git 客戶端面板
- **瀏覽器** — 內建網頁瀏覽器
- **變數檢視器** — 執行期間的變數除錯

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

JEditor 支援多種 UI 語言：

**內建語言：**

- English（預設）
- 繁體中文

**透過插件新增語言：**

可透過插件系統新增額外語言（詳見 :doc:`plugins`）。
語言變更在重新啟動應用程式後生效。

從 **Language** 選單切換語言。
