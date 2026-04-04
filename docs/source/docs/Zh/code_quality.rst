程式碼品質與格式化
====================

JEditor 整合了多種程式碼品質工具，幫助您撰寫乾淨、一致的程式碼。

YAPF Python 格式化
--------------------

`YAPF <https://github.com/google/yapf>`_（Yet Another Python Formatter）將 Python 程式碼
重新格式化為符合 Google 風格指南的格式。

- **快捷鍵：** ``Ctrl+Shift+Y``
- 格式化整個檔案
- 套用一致的縮排、間距和換行
- 可從 **Check Code Style** 選單使用

PEP 8 檢查
------------

JEditor 整合了 `pycodestyle <https://pycodestyle.pycqa.org/>`_ 進行 PEP 8 合規檢查。

- **快捷鍵：** ``Ctrl+Alt+P``
- 報告違規項目，包含行號與偏移量
- 可自訂檢查項目（預設過濾 W191 Tab 警告）
- 可從 **Check Code Style** 選單使用

Ruff 靜態分析
---------------

`Ruff <https://docs.astral.sh/ruff/>`_ 是速度極快的 Python 靜態分析工具，
在背景自動執行：

- 透過 ``watchdog`` 監控檔案系統變更
- 在背景執行緒中進行分析，保持 UI 流暢
- 防抖機制避免快速編輯時過度執行
- 涵蓋數百條 Python 檢查規則
- 結果回報不會阻塞您的工作流程

JSON 格式化
-------------

JEditor 可以格式化與驗證 JSON 檔案：

- **快捷鍵：** ``Ctrl+J``
- 以適當的縮排美化顯示 JSON
- 驗證 JSON 語法並回報錯誤
- 可從 **Check Code Style** 選單使用
