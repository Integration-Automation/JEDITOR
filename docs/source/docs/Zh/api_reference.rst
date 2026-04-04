API 參考
=========

JEditor 提供公開的 Python API，讓您可以將它作為函式庫使用、擴充功能，
或整合到您自己的應用程式中。

啟動編輯器
-----------

.. code-block:: python

   from je_editor import start_editor

   start_editor()

以程式方式啟動完整的 JEditor 應用程式。

核心類別
---------

EditorMain
^^^^^^^^^^^

主視窗類別，包含整個編輯器 UI。

.. code-block:: python

   from je_editor import EditorMain

EditorWidget
^^^^^^^^^^^^^

程式碼編輯器元件（單一編輯分頁）— 自訂的 ``QPlainTextEdit``。

.. code-block:: python

   from je_editor import EditorWidget

FullEditorWidget
^^^^^^^^^^^^^^^^^

完整的編輯器元件，包含行號、語法高亮和輸出顯示，
適合嵌入到停靠面板中。

.. code-block:: python

   from je_editor import FullEditorWidget

MainBrowserWidget
^^^^^^^^^^^^^^^^^^

嵌入式網頁瀏覽器元件。

.. code-block:: python

   from je_editor import MainBrowserWidget

使用自訂分頁擴充編輯器
------------------------

使用 ``EDITOR_EXTEND_TAB`` 為 JEditor 新增自訂分頁：

.. code-block:: python

   from je_editor import start_editor, EDITOR_EXTEND_TAB

   EDITOR_EXTEND_TAB.update({"My Tab": MyCustomWidget})

   start_editor()

詳見 :doc:`how_to_extend_using_pyside` 的完整範例。

程序管理器
-----------

ExecManager
^^^^^^^^^^^^

管理程式執行（執行 Python 腳本和編譯後的二進位檔）。

.. code-block:: python

   from je_editor import ExecManager

ShellManager
^^^^^^^^^^^^^

管理 Shell 命令執行。

.. code-block:: python

   from je_editor import ShellManager

語法高亮
---------

PythonHighlighter
^^^^^^^^^^^^^^^^^^

內建的 Python 語法高亮器。

.. code-block:: python

   from je_editor import PythonHighlighter

syntax_extend_setting_dict / syntax_rule_setting_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

定義高亮器語法關鍵字和規則的字典。

.. code-block:: python

   from je_editor import syntax_extend_setting_dict, syntax_rule_setting_dict

設定
-----

user_setting_dict
^^^^^^^^^^^^^^^^^^

包含所有使用者設定（字型、語言、主題等）的字典。

.. code-block:: python

   from je_editor import user_setting_dict

user_setting_color_dict
^^^^^^^^^^^^^^^^^^^^^^^^

包含所有色彩設定的字典。

.. code-block:: python

   from je_editor import user_setting_color_dict

多語言
-------

language_wrapper
^^^^^^^^^^^^^^^^^

根據目前語言返回指定鍵值的翻譯字串。

.. code-block:: python

   from je_editor import language_wrapper

   label = language_wrapper("file_menu_label")  # 返回 "File" 或對應的翻譯

english_word_dict / traditional_chinese_word_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

內建的翻譯字典。

.. code-block:: python

   from je_editor import english_word_dict, traditional_chinese_word_dict

插件 API
---------

程式語言插件
^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_programming_language,
       get_programming_language_plugin,
       get_all_programming_language_suffixes,
   )

- ``register_programming_language(suffix, syntax_words, syntax_rules=None)`` — 註冊新語言
- ``get_programming_language_plugin(suffix)`` — 取得特定副檔名的插件
- ``get_all_programming_language_suffixes()`` — 列出所有已註冊的副檔名

自然語言插件
^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_natural_language,
       get_natural_language_plugin,
       get_all_natural_languages,
   )

- ``register_natural_language(language_key, display_name, word_dict)`` — 註冊翻譯
- ``get_natural_language_plugin(language_key)`` — 取得翻譯字典
- ``get_all_natural_languages()`` — 列出所有已註冊的語言

執行設定插件
^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_plugin_run_config,
       get_all_plugin_run_configs,
       get_plugin_run_config_by_suffix,
   )

- ``register_plugin_run_config(config)`` — 註冊執行���定
- ``get_all_plugin_run_configs()`` — 列出所有執行設定
- ``get_plugin_run_config_by_suffix(suffix)`` — ��得特定副檔名的執行設定

插件元資料
^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_plugin_metadata,
       get_all_plugin_metadata,
   )

- ``register_plugin_metadata(name, author, version)`` — 註冊插件資訊
- ``get_all_plugin_metadata()`` — 列出所有已註冊的插件元資料

插件載入器
^^^^^^^^^^^

.. code-block:: python

   from je_editor import load_external_plugins

   load_external_plugins()

掃描 ``jeditor_plugins/`` 資料夾並載入所有發現的插件。

日誌
-----

.. code-block:: python

   from je_editor import jeditor_logger

   jeditor_logger.info("自訂日誌訊息")

``jeditor_logger`` 是標準的 Python 日誌器，寫入 ``JEditor.log``。

例外處理
---------

JEditor 定義了一套自訂例外類別階層：

.. code-block:: python

   from je_editor import (
       JEditorException,              # 基礎例外
       JEditorExecException,          # 執行錯誤
       JEditorRunOnShellException,    # Shell 執行錯誤
       JEditorSaveFileException,      # 檔案儲存錯誤
       JEditorOpenFileException,      # 檔案開啟錯誤
       JEditorContentFileException,   # 檔案��容錯誤
       JEditorCantFindLanguageException,  # 找不到語言
       JEditorJsonException,          # JSON 解析錯誤
   )
