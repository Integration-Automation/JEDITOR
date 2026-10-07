# JEditor Architecture

> Short overview for people and agents. Per-module detail lives in [`architecture_explore.md`](architecture_explore.md).
> Last verified: 2026-09-22 against `509dbfd` on `dev`. §2, §3, §5 and §6 re-checked 2026-10-08 on
> `roadmap/editor-next` when the core service layer was added; §6 against PyBreeze `16214a5`.

## 1. Purpose

JEditor is a PySide6 code editor published as `je_editor` (stable) and `je_editor_dev` (dev).
It provides syntax highlighting, folding, multi-cursor editing, an LSP client, ruff diagnostics,
a pytest panel, Git integration, an embedded browser, an IPython console and an AI chat panel
with interchangeable providers (OpenAI-compatible and Anthropic). It runs as a standalone app and also works as a library: PyBreeze subclasses its main
window, and plugins extend it through a small registry API.

## 2. Layers and directories

| Path | Responsibility |
| --- | --- |
| `je_editor/__init__.py` | Public API (`__all__`): `start_editor`, `EditorMain`, `EDITOR_EXTEND_TAB`, `EditorWidget`, exceptions, language dicts, plugin registry functions |
| `je_editor/__main__.py`, `je_editor/start_editor.py` | CLI entry and application bootstrap |
| `je_editor/pyside_ui/main_ui/` | Main window `EditorMain` (`main_editor.py`), editor tab `EditorWidget` (`editor/`), menus (`menu/`), toolbar, panels, command palette, console, IPython, chat panel (`ai_widget/`), plugin browser, settings persistence (`save_settings/`) |
| `je_editor/pyside_ui/code/` | `CodeEditor` (`plaintext_code_edit/`) plus its managers (folding, bookmarks, lint, LSP, diff/blame, snippets, multi-cursor), highlighters (`syntax/`), process runners (`code_process/`, `shell_process/`, `base_process_manager.py`) |
| `je_editor/pyside_ui/dialog/`, `git_ui/`, `browser/` | Search/replace, shortcut, snippet and file dialogs; Git panel, commit graph, diff viewers; embedded QtWebEngine browser |
| `je_editor/core/` | Service layer with no Qt import: `EditorServices` (`services/`) bundles the workspace model (`workspace/`), open documents (`document/`), the unified diagnostic model and store (`diagnostics/`), the language service registry (`language/`), and the interfaces for debug sessions (`debug/`), task execution (`process/`), remote sessions (`remote/`) and AI providers (`ai/`). `events/` and `registry/` replace Qt signals and per-feature registries. The window consumes the diagnostics part so far: the editor's `LintManager` and the Problems panel hold their findings in the unified model (roadmap `docs/roadmap/2026-editor-next.md`) |
| `je_editor/adapters/` | Implementations of the `core/` interfaces, also Qt-free; third-party SDKs are imported at the point of use. `ai/`: `OpenAIProvider` (LangChain `ChatOpenAI`), `AnthropicProvider` (official `anthropic` SDK, streamed), the built-in registration and the `.jeditor/ai_config.json` reader/writer (which never logs the content). `default_services.py` builds an `EditorServices` with these registered `syntax/`: the Tree-sitter `SyntaxEngine` (`tree_sitter_engine.py`), its grammar table and query files (`grammar_table.py`, `queries/<language>/*.scm`), and `SyntaxLanguageService` `process/`: `LocalTaskRunner`, child processes started from an argument list. `debug/`: `DapSession`, a `DebugSession` that talks the Debug Adapter Protocol to an adapter process or a TCP port (`socket_channel.py`), and the debugpy adapter for Python |
| `je_editor/utils/` | Pure logic with no widgets (only `multi_language/locale_match.py` imports Qt): text operations, encodings, sessions, diffs, symbols, LSP protocol, shortcut registry, theme colors, translations (`multi_language/`), logging, stdout/stderr redirect |
| `je_editor/code_scan/` | ruff runner and watchdog file monitor, run on worker threads |
| `je_editor/git_client/` | Git access: `GitService` (GitPython) and `GitCLI` (subprocess), blame, HEAD baseline, hunk staging |
| `je_editor/plugins/` | Plugin registry (`__init__.py`) and `jeditor_plugins/` loader (`plugin_loader.py`) |
| `test/` | pytest suites; `test/qt_ui/unit_test/` holds the launch scripts CI runs (`start_qt_ui.py`, `extend_test.py`) |
| `docs/`, `exe/` | Sphinx docs; executable-build entry (`exe/start_editor.py`) and packaging configs |
| `pyproject.toml`, `dev.toml`, `MANIFEST.in` | Stable and dev package definitions. CI writes `dev.toml` to `pyproject.toml` to build the dev package, so their dependencies, Python floor, entry points and `[tool.setuptools]` must agree. Neither distribution carries `test/`: package discovery includes `je_editor` only (wheel) and `MANIFEST.in` prunes `test` (sdist). `test/test_dev_toml_parity.py` holds all of it. Both files also name the ruff rule set (`[tool.ruff.lint]`, `E4`/`E7`/`E9`/`F`): ruff's defaults change between releases, so "ruff check clean" is defined here and not by whichever ruff is installed |
| `scripts/` | `dev_release.py`: release helper the `publish-dev` job runs (next dev version, wheel comparison); standard library only, not part of the package |
| `.github/workflows/` | `dev.yml`, `stable.yml`: tests on a Windows Python matrix, then one publish job each on `ubuntu-latest` (§3 PyPI packages) |
| `.github/requirements/` | `publish.in` and the `publish.txt` generated from it: the build tooling of the two publish jobs, build backend (`setuptools`) included, pinned by version and hash. The jobs install nothing else and build with `python -m build --no-isolation`, so the backend is the locked one; the lock has to satisfy `build-system.requires` of `pyproject.toml` and `dev.toml` (`test/test_workflow_actions.py`). Dependabot keeps it current |

Dependencies point downwards: `pyside_ui/` → `adapters/` → `core/` → `code_scan/`, `git_client/`,
`plugins/` → `utils/`. Most features are split into a pure function in `utils/` plus a thin Qt layer in
`pyside_ui/`. `test/test_core_architecture.py` enforces the direction: nothing `core/` imports,
directly or indirectly, may be Qt or `pyside_ui/`; the packages below the UI may not import Qt or
`pyside_ui/` except two listed modules (`utils/multi_language/locale_match.py` for `QLocale`,
`plugins/__init__.py` for the highlighting tables); and the services are built in a process where
Qt cannot be imported.

## 3. Entry points and public interfaces

- **CLI**: `python -m je_editor -s` (`je_editor/__main__.py`). No console script is declared.
- **Programmatic**: `je_editor.start_editor(debug_mode=False)`. `debug_mode=True` skips the browser tab
  so headless CI can start it.
- **Embedding**: `EditorMain(debug_mode, show_system_tray_ray, extend)`. `extend=True` skips the
  Windows app ID, the icon and tray, and the Plugins menu, so a host app can supply its own.
- **Window services**: `EditorMain.services` is the window's `EditorServices`, built by
  `adapters/default_services.build_default_services()` and shut down in `closeEvent`. Panels read
  it with `getattr(window, "services", None)` and build their own when a host window has none.
- **Custom tabs**: `EDITOR_EXTEND_TAB: Dict[str, Type[QWidget]]` in `pyside_ui/main_ui/main_editor.py`.
- **Plugin API** (`je_editor/plugins/__init__.py`, re-exported from `je_editor`):
  `register_programming_language`, `register_natural_language`, `register_plugin_run_config`,
  `register_plugin_metadata`, their `get_*` counterparts, and `load_external_plugins`.
- **Other exports**: `EditorWidget`, `FullEditorWidget`, `ExecManager`, `ShellManager`,
  `MainBrowserWidget`, `PythonHighlighter`, `syntax_rule_setting_dict`, `syntax_extend_setting_dict`,
  `language_wrapper`, `english_word_dict`, `traditional_chinese_word_dict`, `user_setting_dict`,
  `user_setting_color_dict`, `jeditor_logger`, the `JEditorException` family (including
  `JEditorServiceException`, raised by the core services).
- **Core services**: `je_editor.core` (`__all__` in `je_editor/core/__init__.py`). A host builds
  `EditorServices(workspace)` and calls `shutdown()` when it closes; there is no module-level
  instance. `Document`, `LanguageService`, `DebugSession`, `TaskRunner`/`TaskHandle`,
  `RemoteSession` and `AIProvider` are `typing.Protocol`s, so a `QObject` can satisfy them without
  a metaclass clash. Changes are announced through `EventHook`, on the thread that caused them.
  `import je_editor.core` still runs `je_editor/__init__.py`, which imports Qt.
- **Workspace**: `EditorMain.services.workspace` lists the window's roots. The working directory is
  the primary root; File → Add Folder to Workspace appends others, recorded per project in
  `workspace_roots` of `user_setting.json`. Panels read the roots through
  `pyside_ui/main_ui/workspace/workspace_roots.py`, never from `working_dir` or the current
  directory themselves. Open Folder still changes the working directory and replaces every root.
- **Persisted state**: `.jeditor/` under the working directory (`user_setting.json`,
  `user_color_setting.json`, `snippets.json`, `.bak` backups).
- **PyPI packages**: `je_editor` (stable) and `je_editor_dev` (dev channel), both published by CI.
  Stable: a push to `main` or a manual run of `stable.yml` runs its `publish_to_pypi` job, which
  bumps `pyproject.toml`, tags and uploads. Dev: the `publish-dev` job of `dev.yml` runs after the
  test matrix on a push to `dev`, builds from `dev.toml` and uploads when the commit is still the
  tip of `dev` and the wheel differs from the newest published one. `scripts/dev_release.py` takes
  the version from PyPI (newest release plus one patch), so nothing is committed back and the
  version in `dev.toml` is only a floor.

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

**Syntax highlighting**

```
CodeEditor.reset_highlighter() → dispose_highlighter(old) → build_highlighter(document, file, engine)
  (pyside_ui/code/syntax/highlighter_factory.py; engine = EditorMain.services.syntax)
  → engine.language_for(file) → engine.open_session(language) → TreeSitterHighlighter
    | no session (unknown language, grammar missing, "syntax_engine": "classic")
      → GenericHighlighter (keyword table) | PythonHighlighter
edit → document.contentsChange → TreeSitterHighlighter._analyse_again()
  → session.update(text) [smallest changed span → tree.edit → reparse → changed lines]
  → Qt repaints the edited lines → highlightBlock() → session.spans(line) → theme colours
  → lines after the edit: block state toggled so Qt carries on; lines before it: next event-loop turn
```

**Debugging**

```
F9 / Run → Debug → run_debugger() (menu/run_menu/under_run_menu/build_debug_menu.py)
  → controller_of(window) [EditorMain.debug_controller, when the debugpy adapter is registered]
      → start_debugging() (main_ui/debug_panel/debug_actions.py): breakpoints of every open editor
        → DebugController.launch() → services.debug_adapters["debugpy"]() → DapSession
          → LocalTaskRunner starts `python -m debugpy.adapter` → DAP handshake → program runs
      | no adapter → ExecManager runs `python -m pdb` with ProcessInput (the earlier console)
session thread: stopped / output / replies → DebugController Qt signals → DebugPanelWidget
  → frame chosen → show_execution_line() → go_to_new_tab(path) → CodeEditor.set_execution_line()
editor shortcuts (continue, step) → CodeEditor.send_debugger_command() → controller, else pdb
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
  (`syntax_rule_setting_dict`, `syntax_extend_setting_dict`). They drive the pattern-based
  highlighters; keywords registered for a suffix are also laid over the Tree-sitter highlighter.
- **Parsed languages**: one `GrammarSpec` row in `adapters/syntax/grammar_table.py` (language ID,
  suffixes, a function importing the grammar package) plus `queries/<language>/highlights.scm` and
  `regions.scm`. The grammar package becomes a pinned dependency in `pyproject.toml`, `dev.toml`
  and both requirements files.
- **Language servers**: `je_editor/utils/lsp/language_servers.py` maps a file suffix to a server
  command and merges in user settings.
- **Shortcuts / colors / UI strings**: single sources in `utils/shortcuts/shortcut_registry.py`,
  `utils/theme/theme_colors.py`, and the dictionaries in `utils/multi_language/`.
- **Core service providers**: an `EditorServices` instance takes implementations by name through
  its `NamedRegistry` attributes — `ai_providers`, `debug_adapters` (session factories),
  `task_runners`, `remote_transports` (by URI scheme) — and language services through
  `languages.register()`. Any source reports findings with `diagnostics.publish(source, uri, ...)`.
  Implementations live in `adapters/`: the AI providers `openai` and `anthropic`, the local task
  runner (`task_runners["local"]`), the `debugpy` debug adapter (`debug_adapters["debugpy"]`,
  a factory returning a new `DebugSession`, which `EditorMain.debug_controller` drives), and the
  Tree-sitter syntax engine, which `build_default_services()` sets as `services.syntax` and
  registers as the `syntax` language service. Questions to language services go through
  `languages.request(LanguageRequest, on_reply)`, which returns a cancel function. A plugin
  adds another AI provider with `window.services.ai_providers.register(name, provider)`, and the
  chat panel lists it with no change to the panel.

## 6. Cross-project boundaries

- **PyBreeze (downstream)**: `PyBreezeMainWindow` subclasses `EditorMain` with `extend=True`
  (`pybreeze/pybreeze_ui/editor_main/main_ui.py`). `pybreeze/__init__.py` re-exports
  `load_external_plugins`, `register_natural_language` and `register_programming_language`. PyBreeze
  also imports some internals by module path: `PluginBrowserWidget`, `DestroyDock`,
  `FullEditorWidget`, `user_setting_dict`, `actually_color_dict`, `choose_file_get_save_file_path`,
  `auto_save_manager_dict` / `file_is_open_manager_dict` / `init_new_auto_save_thread`,
  `check_and_choose_venv`, `RedirectStdErr`, `DEFAULT_ENCODING` / `LINE_ENDING_LF` and
  `write_file_with_encoding` (`write_file`, listed here before, is pinned too). Grep PyBreeze
  before you move or rename a module. It merges its UI strings by mutating the exported
  `english_word_dict` and `traditional_chinese_word_dict` in place. Treat these names,
  `EditorMain`'s constructor and the attributes PyBreeze uses (`tab_widget`, `menu`, `help_menu`)
  as a contract. PyBreeze calls `CodeEditor.reset_highlighter()` after changing a tab's file and
  after `register_programming_language()`; the keywords it registers for `.json` and YAML suffixes
  are laid over whichever highlighter colours those files. `EditorMain` also sets `services`;
  PyBreeze does not use that name today. **PyBreeze keeps contract tests of its own**,
  `test/test_utils/test_jeditor_contract.py` in its repository: they pin parameter lists
  (`LspClient.start_for(file_path, servers)`, `EditorMain.close_tab(index)`,
  `FullEditorWidget.__init__`, `server_command(suffix, servers)`), private names
  (`PythonHighlighter._make_format`) and even fragments of source. An optional parameter added
  here fails them, so run that file against this tree after any change PyBreeze could see:
  `PYTHONPATH=<this repository> pytest test/test_utils/test_jeditor_contract.py` from PyBreeze. `test/test_public_api_contract.py` pins the exported names, those module paths
  and the constructor's arguments; it cannot see behaviour or attributes, and its list is a copy
  that has to be updated when PyBreeze starts importing something new.
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
  `dev.toml`, `requirements.txt`). On 2026-10-01 all three pinned 6.11.2. Within JEditor,
  `pyproject.toml` is the truth: `test/test_requirement_pins.py` holds the requirements files to it
  and `test/test_dev_toml_parity.py` holds `dev.toml` to it. Nothing checks across repositories.

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
- an entry point or an export in `je_editor/__init__.py` or `je_editor/core/__init__.py`;
- the dependency direction in §2, or the list of modules allowed to break it;
- the startup, run or plugin flow in §4;
- an extension point in §5;
- a cross-repo contract in §6 (`EditorMain` signature or extend mode, the exported language dicts,
  `FrontEngineMainUI` usage, plugin conventions, the default plugin repo, the PySide6 pin);
- a CLAUDE.md section that §7 points to is renamed.

Module-level changes belong in `architecture_explore.md` instead. Refresh the "Last verified" line
whenever you re-check this file.
