使用 PySide6 擴充
===================

JEditor 基於 PySide6（Qt for Python）打造，您可以透過自訂的 Qt 元件
新增分頁或停靠面板來擴充編輯器。

新增自訂分頁
--------------

使用 ``EDITOR_EXTEND_TAB`` 字典將自訂元件註冊為編輯器中的新分頁。
鍵值為分頁名稱，值為元件類別（非實例）。

**範例：**

.. code-block:: python

   from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel
   from je_editor import start_editor, EDITOR_EXTEND_TAB


   class TestUI(QWidget):
       """一個簡單的自訂元件，包含文字輸入欄和提交按鈕。"""

       def __init__(self):
           super().__init__()
           self.grid_layout = QGridLayout(self)
           self.grid_layout.setContentsMargins(0, 0, 0, 0)

           self.label = QLabel("")
           self.line_edit = QLineEdit()
           self.submit_button = QPushButton("Submit")
           self.submit_button.clicked.connect(self.show_input_text)

           self.grid_layout.addWidget(self.label, 0, 0)
           self.grid_layout.addWidget(self.line_edit, 1, 0)
           self.grid_layout.addWidget(self.submit_button, 2, 0)

       def show_input_text(self):
           self.label.setText(self.line_edit.text())


   # 註冊自訂分頁：{"分頁名稱": 元件類別}
   EDITOR_EXTEND_TAB.update({"test": TestUI})

   # 啟動帶有自訂分頁的編輯器
   start_editor()

執行此腳本後，JEditor 將在預設分頁旁邊新增一個 "test" ���頁。

運作原理
^^^^^^^^^

1. ``EDITOR_EXTEND_TAB`` 是一個將分頁名稱對應到元件類別的字典
2. JEditor 在建構 UI 時會建立每個已註冊元件類別的實例
3. 元件會作為新分頁加入到分頁列
4. 您的元件可完整使用 PySide6/Qt 的功能

提示
^^^^^

- 您的元件類別必須繼承自 ``QWidget``\ （或其子類別）
- 使用佈局（``QGridLayout``、``QVBoxLayout`` 等）實現響應式設計
- 您可以透過公開 API 存取 JEditor 的內部元件
- 可以多次呼叫 ``update()`` 或傳入包含多個項目的字典來註冊多個自訂分頁

使用 JEditor 元件
-------------------

您也可以在自己的 PySide6 應用程式中使用 JEditor 的個別元件：

.. code-block:: python

   from je_editor import EditorWidget, MainBrowserWidget, FullEditorWidget

- ``EditorWidget`` — 獨立的程式碼編輯器元件
- ``FullEditorWidget`` — 完整的編輯器，包含行號和輸出面板
- ``MainBrowserWidget`` — 獨立的網頁瀏覽器元件

這些元件可以加入任何 PySide6 佈局，方便將程式碼編輯或瀏覽功能
整合到您自己的應用程式中。
