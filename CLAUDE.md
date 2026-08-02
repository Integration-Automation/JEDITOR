# CLAUDE.md - JEditor Project Guidelines

## Session Start

1. **`PROGRESS.md`** (repo root, untracked, gitignored) — read it first for unfinished work; keep it
   updated as you go; **clear it to just the heading when everything is done**. Items may span the
   JEditor and PyBreeze repos, so each item names its repo. Create it when multi-step or
   cross-session work is worth tracking.
2. **`architecture_explore.md`** (repo root) — the module-by-module architecture record.

## Keeping `architecture_explore.md` Current (mandatory)

**Every change must leave `architecture_explore.md` accurate, in the same commit as the code.**
Update it whenever you add, remove, rename, split, or repurpose a module; change how packages depend
on each other; add or remove a global singleton, settings key, thread, or config file; or change the
startup flow. Keep the line counts and module tables in step with the code. Pure bug fixes inside an
existing module that change nothing structural need no update.

## Project Overview

JEditor is a Python code editor built with PySide6 (Qt), featuring syntax highlighting, code
formatting, a plugin system, Git integration, and LangChain-powered AI assistance.

- **Language**: Python 3.10+ · **UI**: PySide6 6.11.0 · **Packaging**: pip / setuptools
- **Testing**: pytest + pytest-qt · **Lint**: ruff, pycodestyle · **Format**: yapf

```
je_editor/
  pyside_ui/     UI layer (browser/, code/, dialog/, git_ui/, main_ui/)
  code_scan/     Ruff linting & watchdog file monitoring
  git_client/    Git operations (GitPython + git CLI)
  plugins/       Plugin registry and loader
  utils/         Shared pure-logic helpers
test/            pytest suites
docs/            Sphinx documentation
```

## Build & Test

```bash
pip install -r requirements.txt        # runtime deps
pip install -r dev_requirements.txt    # dev deps
pytest                                 # tests (Qt UI scripts excluded)
python -m build                        # build (swap pyproject.toml <-> dev.toml for the dev package)
```

## Design Principles

- **MVC separation**: widgets in `pyside_ui/`; logic in `code_scan/`, `git_client/`, `utils/`.
  Pair every feature as pure logic (`utils/`) + a thin Qt integration layer.
- **Patterns**: plugins extend via `plugins/plugin_loader.py` without touching core; Qt signals/slots
  for decoupling; interchangeable formatting/highlighting strategies; single responsibility, no god
  classes.
- **SOLID / DRY**: compose over inherit, depend on abstractions, share code through `utils/`.
- **Fail fast**: validate at boundaries and raise clear exceptions early.
- **Minimal API**: keep internals `_prefixed`; type-hint every signature.
- **Performance**: lazy imports and deferred widget setup; never block the UI thread — file I/O, Git,
  linting and subprocesses belong in `QThread` or a worker thread; batch bulk edits through
  `QTextCursor`; debounce anything driven by typing or resizing.
- **Cleanup**: release file handles, threads and subprocesses in `closeEvent` or via `deleteLater`.

## Code Style

- PEP 8, enforced by ruff. `snake_case` functions/variables, `PascalCase` classes.
- Functions under 50 lines (hard limit 80), max 7 parameters, max 4 nesting levels.
- Cognitive complexity < 15 (S3776); cyclomatic complexity < 10.
- No duplicated blocks of 3+ lines; extract any string literal used 3+ times (S1192).
- No magic numbers except `0`, `1`, `-1`, `2` (S109). Identifiers 3+ chars, except loop counters.
- No commented-out code, dead code, unused imports/variables/parameters, or untracked `# TODO` stubs.
- `is None` / `is not None`; `if x:` not `if x == True:`; consistent return types; no assignment in
  complex conditions.
- f-strings everywhere except `logging`, which uses lazy `%` formatting.

## Exceptions & Resources

- Never `except:` or `except Exception: pass` — name the type, and log or re-raise.
- Chain with `raise NewError(...) from original_error`.
- Use `logging` (not `print`) for diagnostics in production code.
- Always use context managers (`with open(...)`, `with QMutexLocker(...)`); pass `encoding='utf-8'`
  to every `open()`.
- Dispose Qt resources with `deleteLater()` or `Qt.WA_DeleteOnClose` for modal dialogs.

## Security (mandatory)

- **No shell injection**: `subprocess.run()` with an argument list; never `shell=True` or
  `os.system()` on user input.
- **No `eval`/`exec`/`compile`** on untrusted input; no `pickle`/`marshal` on untrusted data
  (B301/B302).
- **Path traversal**: validate user-supplied paths; reject `..` inside a project directory.
- **No hardcoded credentials** (S2068, B105/B106) — load from environment or gitignored config.
- **Crypto**: `secrets`, not `random`, for tokens and IDs (B311); MD5/SHA1 only for non-security uses
  with an explicit comment (S4790, B303).
- **Parsing**: `yaml.SafeLoader` only (B506); `defusedxml` for XML (B313-B320).
- **Files**: `NamedTemporaryFile`/`mkstemp`, never `tempfile.mktemp` (B306).
- **TLS**: never `verify=False`. **Asserts**: none in production logic (B101).
- Pin dependency versions and review before upgrading; sanitize all external input at boundaries.

## Testing & Documentation

- No empty (S1186) or duplicated (S4144) tests.
- Public classes and functions get docstrings covering purpose, args, returns and raises.

## Git & Commits

- English, imperative, one logical change per commit (e.g. "Add plugin hot-reload support").
- `main` = stable, `dev` = active development.
- **No AI attribution anywhere** — commit messages, trailers, branch names, PR titles/descriptions,
  issues, code comments and documentation must never mention an AI tool, assistant, agent, model or
  vendor. No `Co-Authored-By:` or "Generated with ..." footers. PRs describe *what changed and why*.
