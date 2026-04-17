# CLAUDE.md - JEditor Project Guidelines

## Project Overview

JEditor is a Python-based code editor built with PySide6 (Qt), featuring syntax highlighting, code formatting, plugin system, Git integration, and LangChain-powered AI assistance.

- **Language**: Python 3.10+
- **UI Framework**: PySide6 6.11.0
- **Package Manager**: pip / setuptools
- **Testing**: pytest + pytest-qt
- **Linting**: ruff, pycodestyle
- **Formatting**: yapf

## Project Structure

```
je_editor/           # Main package
  pyside_ui/         # UI layer (Qt widgets)
    browser/         # Built-in browser
    code/            # Code editor components (syntax, formatting, process management)
    dialog/          # Dialog windows
    git_ui/          # Git UI components
    main_ui/         # Main window and layout
  code_scan/         # Ruff linting & watchdog file monitoring
  git_client/        # Git operations (GitPython)
  plugins/           # Plugin loader system
  utils/             # Shared utilities
test/                # Unit tests (pytest)
docs/                # Sphinx documentation
```

## Build & Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r dev_requirements.txt

# Run tests (excludes Qt UI tests by default)
pytest

# Build package (stable)
python -m build

# Build dev package (rename pyproject.toml <-> dev.toml first)
python -m build
```

## Design Principles

### Design Patterns

- **MVC separation**: UI widgets (View) in `pyside_ui/`, business logic (Model/Controller) in `code_scan/`, `git_client/`, `utils/`
- **Plugin architecture**: Extend functionality via `plugins/plugin_loader.py` without modifying core code
- **Observer pattern**: Use Qt signals/slots for decoupled event communication between components
- **Strategy pattern**: Code formatting and syntax highlighting are interchangeable strategies
- **Single Responsibility**: Each module handles one concern; avoid god classes

### Software Engineering

- **DRY**: Extract shared logic into `utils/`; never duplicate code across modules
- **SOLID principles**: Favor composition over inheritance; depend on abstractions
- **Fail fast**: Validate inputs at boundaries; raise clear exceptions early
- **Minimal public API**: Keep internal methods private (`_prefix`); expose only what consumers need
- **Type hints**: All function signatures must include type annotations

### Performance

- **Lazy loading**: Defer heavy imports and widget initialization until needed
- **Thread safety**: Run file I/O, Git operations, linting, and process execution in `QThread` or background threads — never block the UI thread
- **Efficient string handling**: Use `QTextCursor` batch operations for bulk text edits; avoid repeated `setText()` calls
- **Resource cleanup**: Always release file handles, threads, and subprocesses in `closeEvent` or `deleteLater`
- **Debounce**: Throttle expensive operations triggered by rapid user input (typing, resizing)

### Security (Mandatory)

- **No shell injection**: Never pass unsanitized user input to `subprocess.Popen(shell=True)` or `os.system()`. Use `subprocess.run()` with argument lists
- **Path traversal prevention**: Validate and sanitize all file paths from user input; reject paths containing `..` when operating within a project directory
- **No eval/exec on user data**: Never use `eval()`, `exec()`, or `compile()` on untrusted input
- **Sensitive data**: Never hardcode API keys, tokens, or credentials. Load from environment variables or config files excluded via `.gitignore`
- **Dependency awareness**: Pin dependency versions; review before upgrading
- **Input validation**: Sanitize all external input (file content, plugin data, user dialog input) at system boundaries

## Code Style

- Follow PEP 8; enforced by ruff
- Use `snake_case` for functions/variables, `PascalCase` for classes
- Keep functions short and focused (< 50 lines preferred)
- Remove dead code — do not comment out unused blocks or leave `# TODO` stubs without tracking

## Git & Commit Rules

- **Commit messages**: Write in English, concise, imperative mood (e.g., "Add plugin hot-reload support")
- **No AI attribution**: Do not mention any AI tool, assistant, or model name in commit messages or code comments
- **Branch strategy**: `main` = stable release, `dev` = active development
- **Clean commits**: Each commit should be a single logical change; no unrelated changes bundled together
