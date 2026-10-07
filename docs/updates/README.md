# docs/updates: update log index

`progress.md` holds only work that is **not done yet**. Everything that *was* done (what changed, measured numbers, decisions, snapshots) is recorded here: **one batch file per month**, one entry per piece of work, each entry with a fixed-format ID and tags, and one row per entry in the index below.

> No TODOs here. If an entry mentions something still open, it only points to it (e.g. "open item: `progress.md` #3"); the item itself lives in `progress.md`.

## How to query

Run from the repository root:

| To find | Command |
|---|---|
| every entry, one line each | `rg -n "^## U-2" docs/updates` |
| entries of one type | `rg -n "^## U-2.*#done" docs/updates` |
| entries with a topic tag | `rg -n "^## U-2.*#<tag>" docs/updates` |
| one day or one month | `rg -n "^## U-202609" docs/updates` |
| the full text of one entry | `rg -n -A 60 "^## U-20260922-01" docs/updates` |
| any keyword | `rg -n "keyword" docs/updates` |

Without `rg`: `git grep -n "^## U-2" -- docs/updates`, or in PowerShell `Select-String -Path docs/updates/*.md -Pattern '^## U-2'`.

## Entry format

```markdown
## U-YYYYMMDD-NN · YYYY-MM-DD · one-line title · #type #topic

- **What**: ...
- **Result / numbers**: ...
- **Files**: `path` ...
- **Evidence**: commit, file:line, link ...
- **Open items**: none / see `progress.md` ...
```

- **ID**: `U-` + date + two-digit sequence for that day. IDs are never renumbered or reused, so code comments and other documents can cite them.
- **Type tag** (exactly one): `#done` finished `progress.md` item, `#snapshot` measurement or inventory, `#decision`, `#incident`, `#migration`, `#docs`, `#release`.
- Topic tags are free-form (`#mcp`, `#wayland`, ...).
- Keep conclusions, numbers, files and evidence; drop the reasoning trail and dead ends.

## Batch rules

1. One file per month: `docs/updates/YYYY-MM.md`. Append new entries at the end.
2. Over about 800 lines, continue in `YYYY-MM-b.md` (then `-c`) and list it in the batch table below.
3. **Claim the ID under a lock.** Several sessions may write this log at the same time (for example parallel autonomous runs), and without a lock two of them pick the same number:
   1. `mkdir docs/updates/.id-lock`. Creating a directory is atomic, so only one writer succeeds. If it already exists, someone else is claiming: wait a few seconds and retry. A lock older than 10 minutes is stale and may be removed.
   2. Find the day's last number with `rg -n "^## U-YYYYMMDD" docs/updates` and write the heading line and the index row.
   3. `rmdir docs/updates/.id-lock`, then fill in the body. Git never tracks the empty lock directory.
   4. Before committing, `rg -c "^## U-<your ID>" docs/updates` must report one match in total. If not, renumber your entry under the lock and fix its index row. Whoever merges a branch renumbers entries that reuse an ID.
4. **One line per index row**: title only (about 60 characters), no summary.
5. Never rewrite a recorded entry. Correct it with a new `#decision` or `#incident` entry and add "→ corrected in U-..." to the old one.

## When a `progress.md` item is done

In the same commit: delete the item from `progress.md`, add a `#done` entry here that names it, and add its index row.

---

## Index (newest first)

| ID | Date | Title | Tags | Batch |
|---|---|---|---|---|
| U-20261008-12 | 2026-10-08 | 藍圖 M4（下）：除錯面板改走 DAP；條件中斷點；接上執行中的程式 | #done #decision #roadmap #debug | [2026-10](2026-10.md) |
| U-20261008-11 | 2026-10-08 | 藍圖 M4（上）：DAP 除錯服務、本機工作執行器、debugpy 轉接器 | #decision #roadmap #debug | [2026-10](2026-10.md) |
| U-20261008-10 | 2026-10-08 | M2 的 CI 結果：SonarCloud 兩筆 S5863 改掉；Python 3.10 一次偶發失敗 | #ci #roadmap | [2026-10](2026-10.md) |
| U-20261008-09 | 2026-10-08 | 恢復 PyBreeze 釘住的 LspClient.start_for 參數清單；把 PyBreeze 的契約測試列為檢查 | #fix #decision #contract | [2026-10](2026-10.md) |
| U-20261008-08 | 2026-10-08 | 藍圖 M2：Tree-sitter 語法引擎與高亮；語言服務的發問形式；四個既有問題 | #done #decision #roadmap #syntax | [2026-10](2026-10.md) |
| U-20261008-07 | 2026-10-08 | 藍圖 M3：工作區與多根專案 | #done #roadmap #workspace | [2026-10](2026-10.md) |
| U-20261008-06 | 2026-10-08 | M2 診斷與 M5 的 CI 結果；Codacy 三筆：一筆改掉、兩筆是誤判 | #decision #ci #roadmap | [2026-10](2026-10.md) |
| U-20261008-05 | 2026-10-08 | 藍圖 M5：AI 對話面板改成可切換供應者，新增 Anthropic 後端 | #done #roadmap #ai #deps | [2026-10](2026-10.md) |
| U-20261008-04 | 2026-10-08 | 藍圖 M2（診斷）：ruff 與語言伺服器的診斷走同一個模型，問題面板依嚴重度與來源篩選 | #migration #roadmap #diagnostics | [2026-10](2026-10.md) |
| U-20261008-03 | 2026-10-08 | PROGRESS #18、#19、#20：寫明 ruff 規則、長路徑測試、fixture 寫法 | #done #decision #tests | [2026-10](2026-10.md) |
| U-20261008-02 | 2026-10-08 | M0 在 PR #270 的 CI 結果；Codacy 的動態匯入警告是誤判 | #decision #ci #roadmap | [2026-10](2026-10.md) |
| U-20261008-01 | 2026-10-08 | 藍圖 M0：不依賴 Qt 的核心服務層 je_editor/core | #migration #roadmap #core | [2026-10](2026-10.md) |
| U-20261001-08 | 2026-10-01 | 發佈鎖檔改用和其他鎖檔一樣的七天截止日解析 | #ci #security #X-13 | [2026-10](2026-10.md) |
| U-20261001-07 | 2026-10-01 | 發佈工作用鎖定的 setuptools 建置，不再下載當下最新的版本 | #done #ci #security #X-13 | [2026-10](2026-10.md) |
| U-20261001-06 | 2026-10-01 | 發佈工作的建置工具改照雜湊鎖定的清單安裝 | #done #ci #security #X-13 | [2026-10](2026-10.md) |
| U-20261001-05 | 2026-10-01 | sdist 不再帶測試 | #done #packaging #X-13 | [2026-10](2026-10.md) |
| U-20261001-04 | 2026-10-01 | wheel 不再把 test/ 當成頂層套件裝進去 | #fix #packaging | [2026-10](2026-10.md) |
| U-20261001-03 | 2026-10-01 | PROGRESS #4 結案：dev.toml 的版本改由 CI 決定 | #done #X-13 | [2026-10](2026-10.md) |
| U-20261001-02 | 2026-10-01 | CI 從 dev 分支發佈 je_editor_dev | #release #ci #X-13 | [2026-10](2026-10.md) |
| U-20261001-01 | 2026-10-01 | Every workflow job has a timeout | #ci #tests | [2026-10](2026-10.md) |
| U-20260925-05 | 2026-09-25 | CI 與分類器涵蓋 Python 3.13、3.14 | #ci #packaging #tests | [2026-09](2026-09.md) |
| U-20260925-04 | 2026-09-25 | 授權中繼資料改用 SPDX 運算式 | #packaging | [2026-09](2026-09.md) |
| U-20260925-03 | 2026-09-25 | dev_requirements.txt 的 PySide6、langchain_openai 對齊套件版本 | #deps #tests | [2026-09](2026-09.md) |
| U-20260925-02 | 2026-09-25 | Dependabot 新版本等 7 天才開 PR | #ci #security #deps | [2026-09](2026-09.md) |
| U-20260925-01 | 2026-09-25 | #8 結案：編輯快捷鍵已隨 PyBreeze 修正一起發版 | #done #release | [2026-09](2026-09.md) |
| U-20260924-02 | 2026-09-24 | checkout 只在要 push 的工作保留憑證 | #ci #security | [2026-09](2026-09.md) |
| U-20260924-01 | 2026-09-24 | CI 改用鎖 commit 的 Node 24 action | #ci #security #deps | [2026-09](2026-09.md) |
| U-20260923-09 | 2026-09-23 | gitpython 下限拉到 3.1.58 | #deps #security | [2026-09](2026-09.md) |
| U-20260923-08 | 2026-09-23 | A file that cannot be opened is reported, and can be opened later | #fix #files | [2026-09](2026-09.md) |
| U-20260923-07 | 2026-09-23 | Every save path reports a failed save; the editor dock keeps encoding and endings | #fix #files | [2026-09](2026-09.md) |
| U-20260923-06 | 2026-09-23 | A save that cannot be encoded no longer empties the file | #fix #files | [2026-09](2026-09.md) |
| U-20260923-05 | 2026-09-23 | Built-in editing keys are reassignable | #done #shortcuts | [2026-09](2026-09.md) |
| U-20260923-04 | 2026-09-23 | Released as 1.0.26; three items closed | #done #release | [2026-09](2026-09.md) |
| U-20260923-03 | 2026-09-23 | PySide6 6.11.2 across the three pin files | #done #deps | [2026-09](2026-09.md) |
| U-20260923-02 | 2026-09-23 | langchain_openai 1.6.2; Dependabot targets dev | #done #deps #ci | [2026-09](2026-09.md) |
| U-20260923-01 | 2026-09-23 | JEditor.log moves out of the working directory | #done #logging | [2026-09](2026-09.md) |
| U-20260922-04 | 2026-09-22 | PLUGIN_GUIDE.md becomes the single plugin guide | #done #docs | [2026-09](2026-09.md) |
| U-20260922-03 | 2026-09-22 | Point project URLs at the current repository | #done #metadata | [2026-09](2026-09.md) |
| U-20260922-02 | 2026-09-22 | Stop tracking .idea/ | #done #housekeeping | [2026-09](2026-09.md) |
| U-20260922-01 | 2026-09-22 | Adopt progress/architecture/docs-updates rules | #docs #migration | [2026-09](2026-09.md) |

## Batches

| File | Period | Entries |
|---|---|---:|
| [2026-10.md](2026-10.md) | 2026-10 | 20 |
| [2026-09.md](2026-09.md) | 2026-09 | 20 |
