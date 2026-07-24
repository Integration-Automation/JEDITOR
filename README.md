# JEDITOR

<p align="center">
  <img src="docs/source/docs/Eng/image/JEditor.png" alt="JEDITOR Logo" width="200"/>
</p>

<p align="center">
  <strong>A modern, lightweight, and extensible code editor built with Python and PySide6.</strong>
</p>

<p align="center">
  <a href="https://github.com/JE-Chen/je_editor">
    <img src="https://img.shields.io/github/stars/JE-Chen/je_editor?style=social" alt="GitHub Stars"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/v/je_editor" alt="PyPI Version"/>
  </a>
  <a href="https://pypi.org/project/je_editor/">
    <img src="https://img.shields.io/pypi/pyversions/je_editor" alt="Python Versions"/>
  </a>
  <a href="https://github.com/JE-Chen/je_editor/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JE-Chen/je_editor" alt="License"/>
  </a>
  <a href="https://je-editor.readthedocs.io/en/latest/">
    <img src="https://img.shields.io/readthedocs/je-editor" alt="Read the Docs"/>
  </a>
</p>

<p align="center">
  <a href="README/README_zh-TW.md">繁體中文</a> |
  <a href="README/README_zh-CN.md">简体中文</a>
</p>

---

## Table of Contents

- [Introduction](#introduction)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Feature Details](#feature-details)
  - [Code Editing](#code-editing)
  - [Code Execution & Debugging](#code-execution--debugging)
  - [Code Quality & Formatting](#code-quality--formatting)
  - [File Operations](#file-operations)
  - [Git Integration](#git-integration)
  - [AI Assistant](#ai-assistant)
  - [Console & REPL](#console--repl)
  - [Embedded Browser](#embedded-browser)
  - [Plugin System](#plugin-system)
  - [Theming & Customization](#theming--customization)
  - [Multi-Language UI](#multi-language-ui)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Project Architecture](#project-architecture)
- [Plugin Development](#plugin-development)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

JEDITOR is a complete rewrite of the original JEditor project, rebuilt from the ground up with a focus on **speed**, **usability**, and **extensibility**. Powered by **PySide6** (Qt for Python), it delivers a modern desktop editing experience with rich features including syntax highlighting, auto-completion, integrated Git client, AI assistant, embedded browser, IPython console, and a powerful plugin system.

JEDITOR achieves up to **1000% faster performance** compared to the original JEditor while providing a significantly richer feature set.

---

## Key Features

| Category | Features |
|---|---|
| **Editor** | Multi-tab editing, syntax highlighting, auto-completion (Jedi), line numbers, current line highlighting, search & replace (regex), code folding, bookmarks, occurrence highlighting, line operations |
| **Navigation** | Command palette, quick open (go to file), go to symbol, document outline, navigation history (back/forward), TODO/FIXME task panel |
| **Execution** | Run Python scripts (F5), debug mode (F9), shell commands, virtual environment detection |
| **Code Quality** | YAPF formatting, PEP8 checking, Ruff linting, JSON reformatting |
| **Git** | Branch management, commit history, side-by-side diff viewer, staging, audit logging |
| **AI** | OpenAI GPT integration via LangChain, interactive chat widget, configurable models & prompts |
| **Console** | Interactive shell, Jupyter/IPython console, command history, multi-shell support |
| **Browser** | Embedded web browser, URL navigation, in-page search |
| **Plugins** | Custom syntax highlighting, UI translations, run configurations, auto-discovery |
| **UI** | Dark/light themes (Qt Material), font customization, dockable panels, system tray, toolbar |
| **i18n** | English, Traditional Chinese, extensible via plugins |
| **Files** | Auto-save, multi-encoding support (UTF-8, GBK, Latin-1, etc.), recent files, multi-file session restore |

---

## Screenshots

<p align="center">
  <img src="docs/source/docs/Eng/image/JEditor.png" alt="JEDITOR Screenshot"/>
</p>

---

## System Requirements

| Platform | Version |
|---|---|
| **Windows** | Windows 10 / 11 |
| **macOS** | 10.5 ~ 11 Big Sur |
| **Linux** | Ubuntu 20.04+ |
| **Raspberry Pi** | 3B+ |
| **Python** | 3.10+ (tested on 3.10, 3.11, 3.12) |

---

## Installation

### From PyPI (Recommended)

```bash
pip install je_editor
```

### From Source

```bash
git clone https://github.com/JE-Chen/je_editor.git
cd je_editor
pip install .
```

### Dependencies

Core dependencies are automatically installed:

| Package | Purpose |
|---|---|
| PySide6 | GUI framework (Qt for Python) |
| qt-material | Dark/light material themes |
| yapf | Python code formatting (Google style) |
| jedi | Python auto-completion & analysis |
| ruff | Fast Python linter |
| gitpython | Git repository operations |
| langchain + langchain_openai | AI/LLM integration |
| watchdog | File system monitoring |
| pycodestyle | PEP8 style checking |
| qtconsole | Jupyter/IPython console widget |

---

## Quick Start

### Launch the Editor

```bash
python -m je_editor
```

### Use as a Python Library

```python
from je_editor import start_editor

start_editor()
```

The editor launches in a maximized window with a dark amber theme by default.

---

## Feature Details

### Code Editing

- **Multi-tab editor** -- Work on multiple files simultaneously with closable tabs.
- **Syntax highlighting** -- Built-in Python highlighting with extensible plugin support for additional languages.
- **Auto-completion** -- Context-aware code suggestions powered by Jedi.
- **Line numbers** -- Displayed alongside the editor with current line highlighting.
- **Search & Replace** -- Search within the current file, across folders, or project-wide with regex and case-sensitive options. Runs in background threads for large projects.
- **Code Folding** -- Collapse and expand indented blocks (functions, classes, loops) from the gutter fold triangles or the keyboard. Folding is indentation-based and only toggles line visibility -- it never modifies the text, so saving always writes the complete file. Folds self-heal after edits: a fold whose header no longer exists simply reopens instead of hiding the wrong lines.
- **Bookmarks** -- Mark lines and jump between them with the keyboard, or click the gutter to toggle. Bookmarks are anchored to the text (via `QTextCursor`), so they follow their code when lines are inserted or removed above them instead of drifting.
- **Occurrence Highlighting** -- Placing the caret on an identifier highlights every other whole-word occurrence of it in the file. Keywords and single characters are ignored, and the scan is skipped on very large files to keep caret movement instant.
- **Line Operations** -- Delete the current line or selection (`Ctrl+Shift+D`), sort selected lines (`Ctrl+Alt+S`), join selected lines into one (`Ctrl+Shift+J`), and (from the Text menu) natural sort, remove duplicate lines, remove blank lines, reverse line order, or align lines on a delimiter (e.g. `=`). Each is a single undo step.
- **Duplicate** (`Ctrl+D`) -- Duplicates the selection when there is one (selecting the new copy), or the whole line when there isn't.
- **Case Conversion** (Text menu) -- Uppercase or lowercase the current selection, keeping it selected.
- **Smart Selection** -- Expand the selection outward through word → line → enclosing indented blocks → whole file (`Ctrl+Alt+Right`), and shrink it back (`Ctrl+Alt+Left`). Shrinking only retraces expansions, and a manual selection change resets the history.
- **Increment / Decrement Number** -- Bump the integer under the caret up or down (`Ctrl+Alt+Up` / `Ctrl+Alt+Down`), handling negative signs and growing widths.
- **Rename in File** (`F2`) -- Rename every whole-word occurrence of the identifier under the caret across the file as a single undo step. Word boundaries protect partial matches (renaming `val` never touches `value`).
- **Navigation History** -- Jump back and forward through your cursor-jump history like a browser (`Alt+Left` / `Alt+Right`). A jump records both where you came from and where you went, so "back" returns to where you started.
- **Document Outline** -- A dockable tree of the current file's classes, methods, functions and module variables (parsed with `ast`, so no code runs). Double-click to jump to a definition.
- **Variable Inspector** -- Inspect and debug variables during code execution.

### Navigation

- **Command Palette** (Ctrl+Shift+A) -- Fuzzy-search every menu command by name or menu path and run it without hunting through menus. Matches are ranked by word boundaries, consecutive characters and prefixes, and each row shows the command's own keyboard shortcut.
- **Quick Open / Go to File** (Ctrl+P) -- Fuzzy-search the project tree by file name *or* folder path. Indexing runs in a background thread, skipping VCS, cache, virtualenv and build directories along with binary file types. Typing `>` at the start switches the same picker into command mode.
- **Go to Symbol** (Ctrl+Shift+O) -- Jump to any class, function, method or module-level variable in the current Python file. Symbols are parsed with the standard library `ast` module, so no user code is ever executed, and a file that does not parse simply yields no symbols instead of erroring while you type.
- **TODO Panel** (Tab > Tools, or as a dock) -- Scans the project for `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE` and `OPTIMIZE` comments across Python, C-like, HTML, SQL and other comment styles. Filter by tag and double-click a row to open that file at that line. Tags are only reported when they follow a comment marker, so ordinary strings are not misreported.

### Code Execution & Debugging

- **Run Python scripts** (F5) -- Execute the current file with real-time output streaming.
- **Debug mode** (F9) -- Launch the Python debugger for step-through debugging.
- **Shell commands** -- Execute arbitrary shell/terminal commands from within the editor.
- **Virtual environment detection** -- Automatically detects and activates Python virtual environments.
- **Process management** -- Stop individual or all running processes.
- **Error highlighting** -- Errors displayed in red in the output panel.

### Code Quality & Formatting

- **YAPF Python formatting** (Ctrl+Shift+Y) -- Automatically format Python code using Google style.
- **PEP8 checking** (Ctrl+Alt+P) -- Validate code against PEP8 style guidelines.
- **Ruff linting** -- Fast, comprehensive Python linting in a background thread.
- **JSON reformatting** (Ctrl+J) -- Pretty-print and validate JSON content.
- **Trim Trailing Whitespace** (Text menu) -- Strip trailing whitespace from every line as one undo step, preserving the caret position.
- **Convert Indentation** (Text menu) -- Convert leading indentation between tabs and spaces (using your indent size). Only leading whitespace is touched, so tabs and spaces inside strings are never altered.
- **Configurable indent width** -- Tab-indent, unindent and Enter auto-indent all honour the configured indent size (`Text > Indent Size`), and the indent width is auto-detected from a file's own content when it is opened.
- **Text transforms** (Text menu) -- Case conversion (upper / lower / swap / title), naming-style conversion (`snake_case` / `camelCase` / `PascalCase` / `kebab-case`), number-base conversion (hex / decimal / binary), and encode/decode helpers (Base64, URL, HTML entities, JSON string escaping). Decoders that fail leave the text untouched.
- **Statistics** (Text menu) -- Line, word and character counts for the whole document or the current selection.

### File Operations

- **Create, open, save** files with standard shortcuts (Ctrl+N, Ctrl+O, Ctrl+S).
- **Open folders** (Ctrl+K) -- Navigate project directory structures.
- **Auto-save** -- Automatic periodic file saving to prevent data loss.
- **Session restore** -- Reopens every file that was open at the last shutdown, not just the last one. Missing, duplicate and already-open files are skipped, the list is capped, and a corrupt or hand-edited settings file can never block startup. Disable by setting `restore_session` to `false` in `.jeditor/user_setting.json`.
- **Multi-encoding** -- Seamlessly handle UTF-8, GBK, Latin-1, and other encodings with automatic detection.
- **Recent files** -- Quick access to previously opened files.

### Git Integration

JEDITOR includes a full-featured Git client:

- **Branch management** -- List, switch, and checkout branches from the toolbar.
- **Commit history** -- View commit metadata (author, date, message) in a table view.
- **Side-by-side diff viewer** -- Color-highlighted code comparison with line numbers.
- **Multi-file diff** -- Compare changes across multiple files.
- **Staging** -- Stage and unstage individual file changes.
- **Audit logging** -- All Git operations are logged for tracking and compliance.

### AI Assistant

Integrated AI assistant powered by OpenAI and LangChain:

- **GPT-3.5 / GPT-4 support** -- Connect to OpenAI's language models.
- **Interactive chat widget** -- Conversational AI panel within the editor.
- **Configurable models** -- Set custom API keys, endpoints, model names, and system prompts.
- **Async messaging** -- Non-blocking AI interaction using a message queue.

### Console & REPL

- **Interactive console** -- Execute shell commands with history navigation (Up/Down arrows).
- **Jupyter/IPython console** -- In-process IPython kernel with rich output support.
- **Multi-shell support** -- Works with cmd, PowerShell, bash, and sh.
- **Working directory control** -- Set the execution directory independently.

### Embedded Browser

- **Built-in web browser** -- Browse the web without leaving the editor.
- **URL navigation** -- Address bar with integrated search.
- **In-page search** (Ctrl+F) -- Find text within web pages.
- **Standard navigation** -- Back, forward, reload, and stop controls.

### Plugin System

JEDITOR supports a modular plugin architecture with four plugin types:

| Type | Purpose |
|---|---|
| Programming Language | Add syntax highlighting for new languages |
| Natural Language | Add UI translations for new locales |
| Run Configuration | Define custom execution environments |
| Plugin Metadata | Provide plugin version and author info |

Plugins are automatically discovered from the `jeditor_plugins/` directory. See the [Plugin Development](#plugin-development) section for details.

### Theming & Customization

- **Dark/Light themes** -- Qt Material themes with amber color scheme.
- **Font customization** -- Change font family and size for the editor and UI.
- **Dockable panels** -- Rearrange the UI layout by docking/undocking panels.
- **System tray** -- Minimize the editor to the system tray.
- **Toolbar** -- JetBrains-style quick action buttons for common operations.

### Multi-Language UI

- **English** -- Full English interface (default).
- **Traditional Chinese** (繁體中文) -- Complete Traditional Chinese translation.
- **Extensible** -- Add new languages via the plugin system.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New file |
| `Ctrl+O` | Open file |
| `Ctrl+K` | Open folder |
| `Ctrl+S` | Save file |
| `Ctrl+Shift+A` | Command palette |
| `Ctrl+P` | Quick open (go to file) |
| `Ctrl+Shift+O` | Go to symbol |
| `Ctrl+Shift+[` | Toggle fold at cursor |
| `Ctrl+Alt+[` | Fold all |
| `Ctrl+Alt+]` | Unfold all |
| `Ctrl+Alt+K` | Toggle bookmark |
| `Ctrl+Alt+L` | Next bookmark |
| `Ctrl+Alt+J` | Previous bookmark |
| `Alt+Left` | Navigate back |
| `Alt+Right` | Navigate forward |
| `Ctrl+Shift+D` | Delete current line / selection |
| `Ctrl+Alt+S` | Sort selected lines |
| `Ctrl+Shift+J` | Join selected lines |
| `Ctrl+Alt+Right` | Expand selection |
| `Ctrl+Alt+Left` | Shrink selection |
| `Ctrl+Alt+Up` | Increment number under caret |
| `Ctrl+Alt+Down` | Decrement number under caret |
| `F2` | Rename occurrences in file |
| `Ctrl+J` | Reformat JSON |
| `Ctrl+Shift+Y` | YAPF Python format |
| `Ctrl+Alt+P` | PEP8 format checker |
| `Ctrl+F` | Find text (browser) |
| `F5` | Run program |
| `F9` | Debug |
| `Shift+F5` | Stop program |
| `Up/Down` | Command history (console) |

---

## Project Architecture

```
je_editor/
├── pyside_ui/                    # GUI components (PySide6)
│   ├── browser/                  # Embedded web browser
│   ├── code/                     # Core code editing
│   │   ├── auto_save/            # Automatic file saving
│   │   ├── bookmark/            # Bookmark manager (QTextCursor-anchored)
│   │   ├── code_format/          # YAPF & PEP8 formatting
│   │   ├── code_process/         # Program execution (ExecManager)
│   │   ├── folding/             # Code folding manager
│   │   ├── shell_process/        # Shell execution (ShellManager)
│   │   ├── syntax/               # Syntax highlighting engine
│   │   ├── plaintext_code_edit/  # Plain text editor widget
│   │   ├── textedit_code_result/ # Output display widget
│   │   └── variable_inspector/   # Variable debugging
│   ├── dialog/                   # Dialog windows
│   │   ├── ai_dialog/            # AI configuration dialog
│   │   ├── file_dialog/          # File operation dialogs
│   │   └── search_ui/            # Search & replace dialogs
│   ├── git_ui/                   # Git interface
│   │   ├── code_diff_compare/    # Side-by-side diff viewer
│   │   └── git_client/           # Branch & commit UI
│   └── main_ui/                  # Main editor window
│       ├── ai_widget/            # AI chat panel
│       ├── command_palette/      # Command palette, quick open, go to symbol
│       ├── console_widget/       # Interactive console
│       ├── dock/                 # Dockable widget management
│       ├── editor/               # Tab-based editor
│       ├── ipython_widget/       # Jupyter/IPython console
│       ├── menu/                 # Menu bar system
│       ├── outline_panel/       # Document outline (symbol tree)
│       ├── plugin_browser/       # Plugin management UI
│       ├── save_settings/        # Settings persistence
│       ├── system_tray/          # System tray integration
│       ├── todo_panel/           # TODO/FIXME task panel
│       └── toolbar/              # Toolbar actions
├── code_scan/                    # Code scanning
│   ├── ruff_thread.py            # Ruff linter (threaded)
│   ├── watchdog_implement.py     # File system monitoring
│   └── watchdog_thread.py        # Watchdog threading
├── git_client/                   # Git backend
│   ├── git_action.py             # Git operations with audit logging
│   ├── git_cli.py                # Git CLI wrapper
│   └── commit_graph.py           # Commit graph visualization
├── plugins/                      # Plugin system
│   └── plugin_loader.py          # Dynamic plugin loading
├── utils/                        # Utilities
│   ├── align/                   # Align lines on a delimiter (Qt-free)
│   ├── bookmark/                # Bookmark navigation logic (Qt-free)
│   ├── case_convert/            # Naming-style conversion (Qt-free)
│   ├── code_folding/            # Fold region computation (Qt-free)
│   ├── command_palette/          # Fuzzy matching & ranking (Qt-free)
│   ├── encode_decode/           # Base64/URL/HTML/JSON transforms (Qt-free)
│   ├── encodings/                # Encoding detection
│   ├── exception/                # Custom exceptions
│   ├── file/                     # File I/O (open/save)
│   ├── file_scan/                # Shared ignore rules, file indexer, TODO scanner
│   ├── indentation/             # Tab/space conversion + indent detection (Qt-free)
│   ├── json_format/              # JSON formatting
│   ├── line_ops/                # Line operation transforms (Qt-free)
│   ├── logging/                  # Logging setup
│   ├── multi_language/           # i18n (English, Traditional Chinese)
│   ├── navigation/              # Cursor jump history (Qt-free)
│   ├── number_ops/              # Number-under-caret adjustment (Qt-free)
│   ├── occurrence/              # Word occurrence finding + whole-word rename (Qt-free)
│   ├── redirect_manager/         # Output stream redirection
│   ├── selection/               # Smart selection ranges (Qt-free)
│   ├── session/                 # Multi-file session restore (Qt-free)
│   ├── symbols/                  # Python symbol extraction + outline tree (ast-based)
│   ├── text_cleanup/            # Trailing whitespace / newline cleanup (Qt-free)
│   ├── text_stats/              # Line/word/char statistics (Qt-free)
│   └── venv_check/               # Virtual environment detection
├── __init__.py                   # Public API
├── __main__.py                   # CLI entry point
└── start_editor.py               # Application launcher
```

---

## Plugin Development

Create plugins in the `jeditor_plugins/` directory within your working directory. JEDITOR supports three types of plugins:

### 1. Programming Language Plugin

Add syntax highlighting for a new language:

```python
from je_editor.plugins import register_programming_language

register_programming_language(
    suffix=".rs",
    syntax_words={"keywords": ["fn", "let", "mut", "struct", "impl", "enum"]},
    syntax_rules={"keyword_color": "#FF6600"}
)
```

### 2. Natural Language Plugin

Add a new UI translation:

```python
from je_editor.plugins import register_natural_language

register_natural_language(
    language_key="ja",
    display_name="Japanese",
    word_dict={"file": "ファイル", "edit": "編集", "run": "実行"}
)
```

### 3. Run Configuration Plugin

Define custom execution environments:

```python
from je_editor.plugins import register_plugin_run_config

register_plugin_run_config(
    name="Node.js",
    run_config={"command": "node", "suffix": ".js"}
)
```

For a comprehensive guide, see `PLUGIN_GUIDE.md`.

---

## Configuration

JEDITOR stores user settings in the `.jeditor/` directory:

| File | Content |
|---|---|
| `user_setting.json` | General preferences (font, theme, recent files) |
| `user_color_setting.json` | Syntax highlighting color scheme |

---

## Documentation

Full documentation is available at:
**[https://je-editor.readthedocs.io/en/latest/](https://je-editor.readthedocs.io/en/latest/)**

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests on [GitHub](https://github.com/JE-Chen/je_editor).

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

Copyright (c) 2021 ~ Now JE-Chen
