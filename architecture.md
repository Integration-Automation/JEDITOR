# JEditor Architecture

> Short overview for people and agents. Per-module detail lives in [`architecture_explore.md`](architecture_explore.md).
> Last verified: 2026-09-22 against `509dbfd` on `dev`.

## 1. Purpose

JEditor is a PySide6 code editor published as `je_editor` (stable) and `je_editor_dev` (dev).
It provides syntax highlighting, folding, multi-cursor editing, an LSP client, ruff diagnostics,
a pytest panel, Git integration, an embedded browser, an IPython console and a LangChain/OpenAI
chat panel. It runs as a standalone app and also works as a library: PyBreeze subclasses its main
window, and plugins extend it through a small registry API.

## 2. Layers and directories

| Path | Responsibility |
| --- | --- |
| `je_editor/__init__.py` | Public API (`__all__`): `start_editor`, `EditorMain`, `EDITOR_EXTEND_TAB`, `EditorWidget`, exceptions, language dicts, plugin registry functions |
| `je_editor/__main__.py`, `je_editor/start_editor.py` | CLI entry and application bootstrap |
| `je_editor/pyside_ui/main_ui/` | Main window `EditorMain` (`main_editor.py`), editor tab `EditorWidget` (`editor/`), menus (`menu/`), toolbar, panels, command palette, console, IPython, chat panel (`ai_widget/`), plugin browser, settings persistence (`save_settings/`) |
| `je_editor/pyside_ui/code/` | `CodeEditor` (`plaintext_code_edit/`) plus its managers (folding, bookmarks, lint, LSP, diff/blame, snippets, multi-cursor), highlighters (`syntax/`), process runners (`code_process/`, `shell_process/`, `base_process_manager.py`) |
| `je_editor/pyside_ui/dialog/`, `git_ui/`, `browser/` | Search/replace, shortcut, snippet and file dialogs; Git panel, commit graph, diff viewers; embedded QtWebEngine browser |
| `je_editor/utils/` | Pure logic with no widgets (only `multi_language/locale_match.py` imports Qt): text operations, encodings, sessions, diffs, symbols, LSP protocol, shortcut registry, theme colors, translations (`multi_language/`), logging, stdout/stderr redirect |
| `je_editor/code_scan/` | ruff runner and watchdog file monitor, run on worker threads |
| `je_editor/git_client/` | Git access: `GitService` (GitPython) and `GitCLI` (subprocess), blame, HEAD baseline, hunk staging |
| `je_editor/plugins/` | Plugin registry (`__init__.py`) and `jeditor_plugins/` loader (`plugin_loader.py`) |
| `test/` | pytest suites; `test/qt_ui/unit_test/` holds the launch scripts CI runs (`start_qt_ui.py`, `extend_test.py`) |
| `docs/`, `exe/` | Sphinx docs; executable-build entry (`exe/start_editor.py`) and packaging configs |
| `pyproject.toml`, `dev.toml` | Stable and dev package definitions (swap them to build the dev package) |
| `.github/workflows/` | `dev.yml`, `stable.yml` (Windows, Python matrix) |

Dependencies point downwards: `pyside_ui/` → `code_scan/`, `git_client/`, `plugins/` → `utils/`.
Most features are split into a pure function in `utils/` plus a thin Qt layer in `pyside_ui/`.

## 3. Entry points and public interfaces

- **CLI**: `python -m je_editor -s` (`je_editor/__main__.py`). No console script is declared.
- **Programmatic**: `je_editor.start_editor(debug_mode=False)`. `debug_mode=True` skips the browser tab
  so headless CI can start it.
- **Embedding**: `EditorMain(debug_mode, show_system_tray_ray, extend)`. `extend=True` skips the
  Windows app ID, the icon and tray, and the Plugins menu, so a host app can supply its own.
- **Custom tabs**: `EDITOR_EXTEND_TAB: Dict[str, Type[QWidget]]` in `pyside_ui/main_ui/main_editor.py`.
- **Plugin API** (`je_editor/plugins/__init__.py`, re-exported from `je_editor`):
  `register_programming_language`, `register_natural_language`, `register_plugin_run_config`,
  `register_plugin_metadata`, their `get_*` counterparts, and `load_external_plugins`.
- **Other exports**: `EditorWidget`, `FullEditorWidget`, `ExecManager`, `ShellManager`,
  `MainBrowserWidget`, `PythonHighlighter`, `syntax_rule_setting_dict`, `syntax_extend_setting_dict`,
  `language_wrapper`, `english_word_dict`, `traditional_chinese_word_dict`, `user_setting_dict`,
  `user_setting_color_dict`, `jeditor_logger`, the `JEditorException` family.
- **Persisted state**: `.jeditor/` under the working directory (`user_setting.json`,
  `user_color_setting.json`, `snippets.json`, `.bak` backups).

## 4. Main flows

**Startup**

```
python -m je_editor -s → start_editor() → quiet_chromium_logging() → QApplication
  → load_external_plugins() → EditorMain(debug_mode)
      [read .jeditor settings → pick language → menus/toolbar → redirect stdout/stderr
       → EditorWidget tab + browser tab + EDITOR_EXTEND_TAB tabs → startup_setting()]
  → apply_stylesheet(dark_amber.xml) → showMaximized() → app.exec() → os._exit()
```

**Run code**

```
Run menu → run_program() (menu/run_menu/under_run_menu/build_program_menu.py) → save file
  → get_plugin_run_config_by_suffix(suffix)
  → ExecManager.exec_with_plugin_config() | ExecManager.exec_code()
  → BaseProcessManager reader threads → queues → QTimer pull_text() → CodeRecord output pane
```

**Plugin install and load**

```
Plugin browser (pyside_ui/main_ui/plugin_browser/) → github_api.fetch_repo_tree() lists .py files
  → download into ./jeditor_plugins/ → restart
  → load_external_plugins() scans jeditor_plugins/ (cwd and package parent; recurses into
    folders without __init__.py; skips _ and . names) → import module
  → register_plugin_metadata() + register_plugin_run_config(PLUGIN_RUN_CONFIG) → register()
```

## 5. Extension points

- **File plugins**: `jeditor_plugins/` loaded by `je_editor/plugins/plugin_loader.py`. A module
  provides `register()` and, optionally, `PLUGIN_NAME` / `PLUGIN_AUTHOR` / `PLUGIN_VERSION` /
  `PLUGIN_RUN_CONFIG`. See `PLUGIN_GUIDE.md` for the run-config keys.
- **Plugin browser source**: `_DEFAULT_REPO_URL` in
  `je_editor/pyside_ui/main_ui/plugin_browser/plugin_browser_widget.py`. Downloads go through
  `plugin_browser/github_api.py`, which restricts URL schemes and blocks path traversal.
- **Extra tabs**: `EDITOR_EXTEND_TAB` in `je_editor/pyside_ui/main_ui/main_editor.py`, read once
  during `EditorMain.__init__`.
- **Host-app mode**: `EditorMain(extend=True)`. In this mode `pyside_ui/main_ui/menu/set_menu_bar.py`
  skips the built-in Plugins menu (`menu/plugin_menu/build_plugin_menu.py`).
- **Python highlighting rules**: `pyside_ui/code/syntax/syntax_setting.py`
  (`syntax_rule_setting_dict`, `syntax_extend_setting_dict`).
- **Language servers**: `je_editor/utils/lsp/language_servers.py` maps a file suffix to a server
  command and merges in user settings.
- **Shortcuts / colors / UI strings**: single sources in `utils/shortcuts/shortcut_registry.py`,
  `utils/theme/theme_colors.py`, and the dictionaries in `utils/multi_language/`.

## 6. Cross-project boundaries

- **PyBreeze (downstream)**: `PyBreezeMainWindow` subclasses `EditorMain` with `extend=True`
  (`pybreeze/pybreeze_ui/editor_main/main_ui.py`). `pybreeze/__init__.py` re-exports
  `load_external_plugins`, `register_natural_language` and `register_programming_language`. PyBreeze
  also imports some non-exported internals: `PluginBrowserWidget`, `DestroyDock`,
  `check_and_choose_venv`, `choose_file_get_save_file_path`, `write_file` and `actually_color_dict`.
  Grep PyBreeze before you move or rename a module. It merges its UI strings by mutating the exported
  `english_word_dict` and `traditional_chinese_word_dict` in place. Treat these names, `EditorMain`'s
  constructor and the attributes PyBreeze uses (`tab_widget`, `menu`, `help_menu`) as a contract.
- **Translations**: a JEditor translation change must keep PyBreeze's
  `test/test_utils/test_language_parity.py` green. Run PyBreeze tests as `pytest test/test_utils`.
- **FrontEngine (upstream)**: `frontengine` is a runtime dependency. `FrontEngineMainUI` is embedded
  as a tab (`pyside_ui/main_ui/menu/tab_menu/build_tab_tools_menu.py`,
  `FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False)`) and as a dock
  (`pyside_ui/main_ui/menu/dock_menu/build_dock_menu.py`, `FrontEngineMainUI(redirect_output=False)`).
  That constructor is a contract with FrontEngine.
- **IDE_Plugins**: the plugin browser's default repo (`https://github.com/Jeffrey-Plugin-Repos/IDE_Plugins`).
  Its files depend only on the registry functions above and on the `PLUGIN_*` / `register()`
  convention, so keep those signatures stable.
- **PySide6 pin**: it must match across JEditor, PyBreeze and FrontEngine (`pyproject.toml`,
  `dev.toml`, `requirements.txt`). At last verification it did not match. JEditor's `pyproject.toml`
  and `requirements.txt` pin 6.11.1, as does FrontEngine. JEditor's `dev.toml` pins 6.11.0, as does PyBreeze.

## 7. Design constraints

- Keep `architecture_explore.md` accurate in the same commit as any structural change
  (CLAUDE.md § Keeping `architecture_explore.md` Current).
- Keep logic in `utils/` / `code_scan/` / `git_client/` and widgets in `pyside_ui/`, and extend
  through plugins rather than core edits (§ Design Principles).
- Never block the UI thread: file I/O, Git, linting and subprocesses go to `QThread` or worker
  threads. Every `QThread` gets `setObjectName(...)` (§ Design Principles, § Testing).
- Release threads, handles and subprocesses in `closeEvent` / `deleteLater` (§ Design Principles,
  § Exceptions & Resources).
- Size and complexity limits, no magic numbers, bilingual *why* comments (§ Code Style).
- Named exceptions chained with `from`, `logging` instead of `print`, `encoding='utf-8'` on every
  `open()` (§ Exceptions & Resources).
- No `shell=True`, no `eval`/`exec` on untrusted input, path-traversal checks, safe YAML/XML, no
  super-linear regexes (§ Security (mandatory)).
- A verification round means ruff clean, pytest green, PyBreeze parity for translation changes, and
  the Qt launch scripts before pushing Qt changes (§ Build, Test & Verify).
- Never hand a constructed `QKeyEvent` to a handler in tests. CI does not set
  `QT_QPA_PLATFORM=offscreen` (§ Testing, § CI).
- `main` is stable and `dev` is active. Merge PRs with merge commits (never squash), and follow the
  commit-message rules (§ Git & Commits).

## 8. When to update this file

Update it in the same commit when any of these changes:

- a top-level package or directory in §2;
- an entry point or an export in `je_editor/__init__.py`;
- the startup, run or plugin flow in §4;
- an extension point in §5;
- a cross-repo contract in §6 (`EditorMain` signature or extend mode, the exported language dicts,
  `FrontEngineMainUI` usage, plugin conventions, the default plugin repo, the PySide6 pin);
- a CLAUDE.md section that §7 points to is renamed.

Module-level changes belong in `architecture_explore.md` instead. Refresh the "Last verified" line
whenever you re-check this file.
