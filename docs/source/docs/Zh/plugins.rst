插件系統
=========

JEditor 擁有完整的插件系統，讓您可以擴充編輯器，新增程式語言支援、
UI 翻譯和自訂執行設定。

插件類型
---------

JEditor 支援四種類型的插件：

1. **程式語言插件** — 為新語言新增語法高亮
2. **自然語言（翻譯）插件** — 新增 UI 翻譯
3. **執行設定插件** — 定義如何執行特定類型的檔案
4. **插件元資料** — 顯示在插件選單中的版本與作者資訊

插件目錄
---------

插件會從工作目錄下的 ``jeditor_plugins/`` 資料夾自動發現：

.. code-block:: text

   working_directory/
     jeditor_plugins/
       my_syntax.py            # 單檔插件
       my_language.py
       my_package/             # 套件插件
         __init__.py

**發現規則：**

- 以 ``_`` 或 ``.`` 開頭的檔案會被忽略
- 每個插件 **必須** 定義一個 ``register()`` 函式
- 套件插件使用 ``__init__.py`` 作為進入點
- 重複的插件名稱以先找到的為準

插件元資料
-----------

每個插件可選擇性地定義元資料，顯示在 **Plugins** 選單中：

.. code-block:: python

   PLUGIN_NAME = "My Plugin"       # 顯示名稱
   PLUGIN_AUTHOR = "Your Name"     # 作者
   PLUGIN_VERSION = "1.0.0"        # 版本號

如未定義，則以檔名作為插件名稱。

程式語言插件
-------------

為任何程式語言新增語法高亮。

**API：**

.. code-block:: python

   from je_editor.plugins import register_programming_language

   register_programming_language(
       suffix=".ext",              # 副檔名
       syntax_words={...},         # 關鍵字群組
       syntax_rules={...},         # 正規表達式規則（可選）
   )

**syntax_words 格式：**

定義關鍵字群組及其高亮顏色：

.. code-block:: python

   from PySide6.QtGui import QColor

   syntax_words = {
       "group_name": {
           "words": ("keyword1", "keyword2", ...),
           "color": QColor(r, g, b),
       },
       # 更多群組...
   }

**syntax_rules 格式：**

定義正規表達式模式，用於複雜的語法元素（註解、字串等）：

.. code-block:: python

   syntax_rules = {
       "rule_name": {
           "rules": (r"regex_pattern", ...),
           "color": QColor(r, g, b),
       },
   }

**完整範例 — Go 語法高亮：**

.. code-block:: python

   """Go 語法高亮插件。"""
   from PySide6.QtGui import QColor
   from je_editor.plugins import register_programming_language

   PLUGIN_NAME = "Go Syntax Highlighting"
   PLUGIN_AUTHOR = "Your Name"
   PLUGIN_VERSION = "1.0.0"

   go_syntax_words = {
       "keywords": {
           "words": (
               "break", "case", "chan", "const", "continue",
               "default", "defer", "else", "fallthrough", "for",
               "func", "go", "goto", "if", "import",
               "interface", "map", "package", "range", "return",
               "select", "struct", "switch", "type", "var",
           ),
           "color": QColor(86, 156, 214),
       },
       "types": {
           "words": (
               "bool", "byte", "complex64", "complex128",
               "float32", "float64", "int", "int8", "int16",
               "int32", "int64", "rune", "string", "uint",
               "uint8", "uint16", "uint32", "uint64", "uintptr",
               "error", "nil", "true", "false", "iota",
           ),
           "color": QColor(78, 201, 176),
       },
   }

   go_syntax_rules = {
       "single_line_comment": {
           "rules": (r"//[^\\n]*",),
           "color": QColor(106, 153, 85),
       },
   }


   def register() -> None:
       register_programming_language(
           suffix=".go",
           syntax_words=go_syntax_words,
           syntax_rules=go_syntax_rules,
       )

**多個副檔名：**

如果一個語言使用多個副檔名，分別註冊每一個：

.. code-block:: python

   def register() -> None:
       for suffix in (".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"):
           register_programming_language(
               suffix=suffix,
               syntax_words=cpp_syntax_words,
               syntax_rules=cpp_syntax_rules,
           )

自然語言（翻譯）插件
----------------------

新增 UI 翻譯語言。

**API：**

.. code-block:: python

   from je_editor.plugins import register_natural_language

   register_natural_language(
       language_key="French",          # 內部鍵值
       display_name="Francais",        # 語言選單顯示名稱
       word_dict={...},                # 翻譯字典
   )

``word_dict`` 應包含與 JEditor 內建 ``english_word_dict`` 相同的鍵值。
常用鍵值包括：

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - 鍵值
     - 說明
   * - ``application_name``
     - 視窗標題
   * - ``file_menu_label``
     - 檔案選單
   * - ``run_menu_label``
     - 執行選單
   * - ``tab_name_editor``
     - 編輯器分頁名稱
   * - ``language_menu_label``
     - 語言選單
   * - ``help_menu_label``
     - 幫助選單

完整鍵值列表請參考 ``je_editor.utils.multi_language.english.english_word_dict``
或範例插件 ``exe/jeditor_plugins/french.py``。

**完整範例 — 日語翻譯：**

.. code-block:: python

   """日語翻譯插件。"""
   from je_editor.plugins import register_natural_language

   PLUGIN_NAME = "Japanese Translation"
   PLUGIN_AUTHOR = "Your Name"
   PLUGIN_VERSION = "1.0.0"

   japanese_word_dict = {
       "application_name": "JEditor",
       "file_menu_label": "\u30d5\u30a1\u30a4\u30eb",
       "run_menu_label": "\u5b9f\u884c",
       "tab_name_editor": "\u30a8\u30c7\u30a3\u30bf",
       "language_menu_label": "\u8a00\u8a9e",
       # ... 更多鍵值
   }


   def register() -> None:
       register_natural_language(
           language_key="Japanese",
           display_name="\u65e5\u672c\u8a9e",
           word_dict=japanese_word_dict,
       )

執行設定插件
-------------

定義如何執行特定類型的檔案。

**直譯式語言**\ （直接執行）：

.. code-block:: python

   PLUGIN_RUN_CONFIG = {
       "name": "Go",                   # 選單顯示名稱
       "suffixes": (".go",),           # 支援的副檔名
       "compiler": "go",               # 執行檔
       "args": ("run",),               # 檔案路徑前的參數
   }
   # 執行：go run file.go

**編譯式語言**\ （先編譯再執行）：

.. code-block:: python

   PLUGIN_RUN_CONFIG = {
       "name": "C (GCC)",
       "suffixes": (".c",),
       "compiler": "gcc",
       "args": (),
       "compile_then_run": True,       # 先編譯再執行
       "output_flag": "-o",            # 輸出檔案旗標
   }
   # 編譯：gcc file.c -o file
   # 執行：./file（Linux/Mac）或 file.exe（Windows）

**設定鍵值：**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - 鍵值
     - 必要
     - 說明
   * - ``name``
     - 是
     - 執行選單中的顯示名稱
   * - ``suffixes``
     - 是
     - 副檔名元組
   * - ``compiler``
     - 是
     - 編譯器或直譯器的執行檔
   * - ``args``
     - 否
     - 檔案路徑前的額外參數
   * - ``compile_then_run``
     - 否
     - 若為 ``True``，先編譯再執行產出的二進位檔
   * - ``output_flag``
     - 否
     - 輸出檔案旗標（預設 ``"-o"``）

預建插件
---------

JEditor 在 ``exe/jeditor_plugins/`` 中提供以下範例插件：

.. list-table::
   :header-rows: 1
   :widths: 30 20 25 25

   * - 插件
     - 類型
     - 副檔名
     - 執行支援
   * - C 語法高亮
     - 語法
     - ``.c``
     - GCC 編譯與執行
   * - C++ 語法高亮
     - 語法
     - ``.cpp``、``.cxx``、``.cc``、``.h``、``.hpp``、``.hxx``
     - G++ 編譯與執行
   * - Go 語法高亮
     - 語法
     - ``.go``
     - ``go run``
   * - Java 語法高亮
     - 語法
     - ``.java``
     - ``java``
   * - Rust 語法高亮
     - 語法
     - ``.rs``
     - rustc 編譯與執行
   * - 法語翻譯
     - 語言
     - —
     - —

插件瀏覽器
-----------

JEditor 包含可從 **Plugin** 選單存取的插件瀏覽器：

- 瀏覽可用的插件
- 透過 GitHub API 整合發現社群插件
- 檢視插件元資料（名稱、作者、版本）
