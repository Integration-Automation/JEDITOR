# CLAUDE.md - JEditor Project Guidelines

## Session Start: Check the Progress Record

At the start of every session, check for `PROGRESS.md` in the repo root (a local,
untracked working-progress record — it is in `.gitignore`).

- If it exists and lists outstanding items, read it first to resume in-progress work.
- Keep it updated as work progresses; items may span both the JEditor and PyBreeze repos (each item names its repo).
- **When every item is done, clear it** — reset the file to just its heading and usage note, leaving no stale tasks.
- If it does not exist and there is multi-step or cross-session work worth tracking, create it.

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

## Static Analysis Compliance (SonarQube / Codacy)

All code must pass SonarQube and Codacy quality gates. Adhere to the following rules:

### Complexity & Maintainability

- **Cognitive complexity**: Keep functions below 15 (SonarQube S3776). Break deeply nested logic into helper functions
- **Cyclomatic complexity**: Functions should stay under 10 branches; extract conditionals into smaller functions
- **Function length**: Soft limit 50 lines, hard limit 80 lines of executable code
- **Parameter count**: Max 7 parameters per function (SonarQube S107); use dataclasses or `**kwargs` for larger sets
- **Nesting depth**: Max 4 levels of nested control flow (SonarQube S134)
- **No duplicate code**: Extract 3+ line repeated blocks into shared utilities (SonarQube copy-paste detector)
- **String literal duplication**: Extract any string literal used 3+ times into a module-level constant (SonarQube S1192)
- **No magic numbers**: Replace unnamed numeric literals with named constants (SonarQube S109); exceptions: `0`, `1`, `-1`, `2`

### Exception Handling

- **No bare `except:`**: Always specify exception types (SonarQube S5754, Codacy PyLint W0702)
- **No silent swallowing**: Never `except: pass` without logging or re-raising (SonarQube S2737)
- **No overly broad `except Exception`** unless logged and re-raised at boundaries
- **Chain exceptions**: Use `raise NewError(...) from original_error` to preserve context
- **Use `logging` over `print`** for diagnostics in library/production code (SonarQube S4792)

### Code Quality

- **No commented-out code**: Delete it — rely on git history (SonarQube S125)
- **No unused imports/variables/parameters**: Remove them (SonarQube S1128, S1854)
- **Explicit `None` checks**: Use `is None` / `is not None`, never `== None` (SonarQube S2197)
- **No redundant boolean**: `if x:` not `if x == True:`; `if not x:` not `if x == False:`
- **Consistent return types**: A function should always return the same type (or always `None`); avoid `return None` in numeric functions
- **No assignment in conditions**: Avoid `if (x := func()):` in complex expressions (SonarQube S1121)
- **Identifier naming**: Min 3 characters except loop counters (`i`, `j`, `k`); no single-letter names for non-trivial scope
- **String formatting**: Prefer f-strings over `%` or `.format()` unless logging (logging uses `%` lazy formatting)

### Security (SonarQube / Codacy Bandit rules)

- **No hardcoded credentials** (SonarQube S2068, Bandit B105/B106): passwords, tokens, keys
- **No weak hashing** for security contexts (SonarQube S4790, Bandit B303): MD5/SHA1 only allowed for non-security uses (e.g., cache keys) with explicit comment
- **No `random` for security** (Bandit B311): use `secrets` module for tokens, IDs, crypto
- **No `pickle`/`marshal` on untrusted data** (Bandit B301/B302)
- **No `yaml.load` without `SafeLoader`** (Bandit B506)
- **No `tempfile.mktemp`** (Bandit B306): use `NamedTemporaryFile` / `mkstemp`
- **No `assert` in production logic** (Bandit B101): asserts are stripped with `-O`; use explicit `raise`
- **No XML parsers vulnerable to XXE** (Bandit B313-B320): use `defusedxml`
- **TLS verification**: Never `verify=False` in `requests` or urllib calls

### Resource Management

- **Always use context managers**: `with open(...)`, `with lock`, `with QMutexLocker(...)` — never manual `.close()` without `try/finally`
- **Close Qt resources**: call `deleteLater()` or use `setAttribute(Qt.WA_DeleteOnClose)` for modal dialogs
- **Encoding explicit**: always pass `encoding='utf-8'` to `open()` (SonarQube S5122 / Ruff PLW1514)

### Testing & Documentation

- **No empty test functions** (SonarQube S1186)
- **No identical test cases** (SonarQube S4144)
- **Public API docstrings**: all public classes/functions should have docstrings describing purpose, args, returns, raises

## Git & Commit Rules

- **Commit messages**: Write in English, concise, imperative mood (e.g., "Add plugin hot-reload support")
- **No AI attribution (mandatory)**: Never mention any AI tool, assistant, agent, model name, or vendor in commit messages, commit trailers, branch names, PR titles, PR descriptions, issue text, code comments, or documentation
  - No `Co-Authored-By:` trailers referencing an AI tool or model
  - No "Generated with ...", "Created by ...", or similar footers in commits or PR bodies
  - PR titles and bodies describe **what changed and why** — nothing about how the change was authored
- **Branch strategy**: `main` = stable release, `dev` = active development
- **Clean commits**: Each commit should be a single logical change; no unrelated changes bundled together
