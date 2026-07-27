鍵盤快捷鍵
============

JEditor 提供常用操作的鍵盤快捷鍵，讓您的工作流程更快速、更有效率。

本頁大部分的快捷鍵都可以在 **UI 風格 → 鍵盤快捷鍵** 中重新指派。兩個指令不能共用
同一組按鍵：發生這種情況時 Qt 兩個都不會執行，因此設定對話框會拒絕儲存衝突的組合。
改動立即生效，而且只有與預設值不同的項目會被記錄下來。少數由編輯區直接處理的按鍵
（列在 `固定按鍵`_ 一節）不在該清單中，無法重新指派。

檔案操作
---------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+N``
     - 建立新檔案
   * - ``Ctrl+O``
     - 開啟現有檔案
   * - ``Ctrl+K``
     - 開啟資料夾（專案）
   * - ``Ctrl+S``
     - 儲存目前檔案
   * - ``Ctrl+Shift+S``
     - 儲存所有已修改的分頁

搜尋與導覽
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+F``
     - 在檔案中搜尋文字（也是瀏覽器的頁內搜尋）
   * - ``Ctrl+H``
     - 搜尋與取代
   * - ``Ctrl+Shift+F``
     - 跨檔案搜尋
   * - ``Ctrl+G``
     - 跳到指定行
   * - ``Ctrl+P``
     - 快速開啟（前往檔案）
   * - ``Ctrl+Shift+A``
     - 指令面板
   * - ``Ctrl+Shift+O``
     - 前往符號
   * - ``Alt+Left`` / ``Alt+Right``
     - 在游標跳轉歷史中往前／往後
   * - ``Ctrl+Alt+E``
     - 最近位置

程式碼編輯
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+D``
     - 刪除目前行或選取內容
   * - ``Ctrl+Shift+J``
     - 合併選取的行
   * - ``Ctrl+Alt+S``
     - 排序選取的行
   * - ``Ctrl+Alt+Right`` / ``Ctrl+Alt+Left``
     - 擴大／縮回選取範圍
   * - ``Ctrl+Alt+Up`` / ``Ctrl+Alt+Down``
     - 游標處的數字加一／減一
   * - ``F2``
     - 重新命名檔案內所有出現處

多重游標
---------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+L``
     - 在每個選取行的行尾放一個游標
   * - ``Ctrl+Alt+N``
     - 在下一個出現處加一個游標
   * - ``Ctrl+Alt+Shift+Up`` / ``Ctrl+Alt+Shift+Down``
     - 在上一行／下一行加一個游標
   * - ``Ctrl+Shift+Esc``
     - 回到單一游標

方向鍵、``Home`` 與 ``End`` 會讓所有游標一起移動；按住 ``Shift`` 再按這些鍵，
則會在每個游標各自擴大選取範圍。

折疊與書籤
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+[``
     - 切換游標所在的折疊
   * - ``Ctrl+Alt+[`` / ``Ctrl+Alt+]``
     - 全部折疊／全部展開
   * - ``Ctrl+Alt+K``
     - 切換書籤
   * - ``Ctrl+Alt+L`` / ``Ctrl+Alt+J``
     - 下一個／上一個書籤

Git
----

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``F7`` / ``Shift+F7``
     - 下一個／上一個變更
   * - ``Ctrl+Alt+Z``
     - 還原游標所在的變更
   * - ``Ctrl+Alt+B``
     - 切換行內 blame

程式碼執行與除錯
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``F5``
     - 執行目前的 Python 檔案
   * - ``F9``
     - 對目前的 Python 檔案執行除錯器
   * - ``Shift+F5``
     - 停止所有執行中的程式
   * - ``Ctrl+F9``
     - 切換中斷點
   * - ``Ctrl+F5``
     - 繼續執行
   * - ``F10`` / ``F11`` / ``Shift+F11``
     - 逐步跳過／逐步進入／跳出

程式碼品質
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+Y``
     - 以 YAPF 格式化 Python 程式碼
   * - ``Ctrl+Alt+P``
     - 檢查 PEP 8 相容性
   * - ``Ctrl+J``
     - 重新格式化／驗證 JSON

巨集與檢視
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+R``
     - 開始／結束錄製巨集
   * - ``Ctrl+Shift+G``
     - 重播巨集
   * - ``Ctrl+Alt+\``
     - 切換分割檢視
   * - ``Ctrl+Alt+M``
     - 切換縮圖
   * - ``Alt+W``
     - 切換自動換行

Python 環境
------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+Shift+P``
     - 以 pip 安裝套件
   * - ``Ctrl+Shift+U``
     - 升級與安裝套件
   * - ``Ctrl+Shift+V``
     - 切換 Python 直譯器

主控台
-------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Up``
     - 歷史中的上一個指令
   * - ``Down``
     - 歷史中的下一個指令

固定按鍵
---------

以下按鍵由編輯區本身處理，而不是透過指令，因此不會出現在快捷鍵設定中，也無法重新
指派：

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - 快捷鍵
     - 動作
   * - ``Ctrl+D``
     - 複製目前行或選取內容
   * - ``Ctrl+/``
     - 切換註解
   * - ``Alt+Up`` / ``Alt+Down``
     - 將該行上移／下移
   * - ``Ctrl+B``
     - 跳到游標處符號的定義
   * - ``Ctrl+Shift+\``
     - 跳到對應的括號
   * - ``Ctrl++`` / ``Ctrl+-``
     - 放大／縮小編輯器字型
   * - ``Tab`` / ``Shift+Tab``
     - 將該行或選取內容縮排／取消縮排

在有選取內容時輸入 ``(``、``[``、``{``、``"`` 或 ``'``，會以該組符號包住選取內容，
而不是取代它。
