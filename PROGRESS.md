# PROGRESS：JEditor 待辦

只放還沒做的事。做完就在同一個 commit 裡刪掉這條，並在 `docs/updates/` 新增一筆 `#done` 紀錄（格式與查詢方式見 `docs/updates/README.md`）。不放已完成的項目、不寫流水帳、不寫規則（規則在 `CLAUDE.md`）。
本檔納入版控。PyBreeze 的待辦寫在 PyBreeze 自己的 `progress.md`。
編號 `#n` 不重用。標記：〔決定〕需擁有者拍板、〔阻塞〕在等別的事、〔未確認〕觀察到但還沒證實。
跨專案與工作區層級的待辦在 `D:\Codes\progress.md`（與本專案相關：X-1、X-10、X-16、X-17）。

## 待辦

- **#1** SonarCloud 的 S125 是誤判，需要在網站上標記：`extend_system_tray.py:27` 的
  `# 初始化並記錄日誌` 被當成「註解掉的程式碼」。這是本專案雙語註解的正常寫法，不該刪。
  要清掉這一項得在 SonarCloud 把 issue 轉成 False Positive（用 API 改狀態需要 Administer
  Issues 權限）。
- **#2** 讓編輯區自行處理的按鍵也能重新指派：`Ctrl+D`、`Ctrl+/`、`Alt+Up/Down`、
  `Ctrl+B`、`Ctrl+Shift+\`、`Ctrl++`/`Ctrl+-` 目前寫死在 `code_edit_plaintext.py` 的
  `_handle_ctrl_shortcuts` / `_handle_alt_shortcuts`，不在 `shortcut_registry` 裡，因此
  設定對話框改不到。文件（README 與 keyboard_shortcuts）已如實標為「固定按鍵」；若要
  改成可設定，需把它們搬進 registry 並改由 `_add_shortcut_action` 綁定。
- **#3** `dev` 上的 `509dbfd` 還沒發佈到 `main`。
- **#4** `dev.toml` 過期：版本 1.0.11、PySide6 6.11.0、langchain_openai 1.2.0（`dev.toml:9,17-18`）；`CLAUDE.md` 的 Project Overview 也還寫 PySide6 6.11.0，而 `pyproject.toml` 已是 6.11.1（工作區 X-1）。
- **#5** 〔未確認〕`pyproject.toml` 的 pytest addopts 沒有 `--ignore=test/qt_ui`（`dev.toml` 有），照 `CLAUDE.md` 跑 bare `pytest` 可能把 `extend_test.py` 收進來、開出整個 app。
- **#6** 兩個 dependabot 分支沒合併：`pyside6-6.11.2`、`langchain-openai-1.6.0`（工作區 X-16）。
- **#7** `PLUGIN_GUIDE.md`（≈:188、:191、:314）指向不存在的 `exe/jeditor_plugins/`，應改指 IDE_Plugins；PyBreeze 有一份逐字相同的副本（工作區 X-10）。
