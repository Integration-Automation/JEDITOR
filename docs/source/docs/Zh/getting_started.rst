快速入門
=========

系統需求
---------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 平台
     - 版本
   * - Windows
     - Windows 10 / 11
   * - macOS
     - 10.5 ~ 11 Big Sur
   * - Linux
     - Ubuntu 20.04+
   * - Raspberry Pi
     - 3B+
   * - Python
     - 3.10、3.11、3.12

安裝方式
---------

**從 PyPI 安裝：**

.. code-block:: bash

   pip install je_editor

**從原始碼安裝：**

.. code-block:: bash

   git clone https://github.com/JE-Chen/je_editor.git
   cd je_editor
   pip install .

依賴套件
^^^^^^^^^

JEditor 會自動安裝以下依賴套件：

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - 套件
     - 用途
   * - PySide6
     - GUI 框架（Qt for Python）
   * - qt-material
     - 深色 / 淺色 Material 主題
   * - yapf
     - Python 程式碼格式化
   * - jedi
     - Python 自動補全
   * - ruff
     - 快速 Python 靜態分析工具
   * - gitpython
     - Git 操作
   * - langchain / langchain_openai
     - AI 助手（LLM 整合）
   * - watchdog
     - 檔案系統監控
   * - pycodestyle
     - PEP 8 檢查
   * - qtconsole
     - Jupyter / IPython 主控台元件
   * - frontengine
     - 額外 UI 元件

啟動 JEditor
--------------

**從命令列啟動：**

.. code-block:: bash

   python -m je_editor

**作為 Python 函式庫使用：**

.. code-block:: python

   from je_editor import start_editor

   start_editor()

啟動後，JEditor 預設以深色主題開啟。您可以隨時從 **UI Style** 選單更換主題。

專案結構
---------

JEditor 啟動時會在目前工作目錄下建立 ``.jeditor/`` 資料夾，用於儲存：

- ``user_setting.json`` — UI 偏好設定、字型、語言、最近開啟的檔案
- ``user_color_setting.json`` — 編輯器與輸出的色彩配置
- ``ai_config.json`` — AI 助手設定（如有啟用）

這些檔案會在首次啟動時自動建立。
