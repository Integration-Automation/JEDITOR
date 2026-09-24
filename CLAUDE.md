# CLAUDE.md - JEditor Project Guidelines

## Session Start

1. **`PROGRESS.md`** (repo root, tracked) — the outstanding-work list, and *only* that.
   Read it first to resume unfinished work, keep it updated as you go, and **clear it to just the
   heading when everything is done**. PyBreeze items live in
   PyBreeze's own `progress.md`; finished items are deleted here and recorded in `docs/updates/`. Rules and
   standing knowledge belong in this file, never in `PROGRESS.md`, which gets emptied.
2. **`architecture_explore.md`** (repo root) — the module-by-module architecture record.

## Keeping `architecture_explore.md` Current (mandatory)

**Every change must leave `architecture_explore.md` accurate, in the same commit as the code.**
Update it whenever you add, remove, rename, split, or repurpose a module; change how packages depend
on each other; add or remove a global singleton, settings key, thread, or config file; or change the
startup flow. Keep the line counts and module tables in step with the code. Pure bug fixes inside an
existing module that change nothing structural need no update.

## Keeping the READMEs Current (mandatory)

**`README.md`, every translated README, and the docs must stay in sync with the code.** This repo
ships `README.md`, `README/README_zh-TW.md` and `README/README_zh-CN.md`, plus the Sphinx sources
under `docs/`. Any user-facing change — features, commands, CLI flags, install/setup, configuration
or requirements — updates `README.md`, **every language variant, and the affected `docs/` pages in
the same commit**, with section structure and content aligned across languages; the translations
must reflect the English content, not merely match its headings. Never update one language, or
`README.md` alone, and leave the other READMEs or the docs stale. There is no README-parity guard,
so this is a manual check against the files above.

## Project Overview

JEditor is a Python code editor built with PySide6 (Qt), featuring syntax highlighting, code
formatting, a plugin system, Git integration, and LangChain-powered AI assistance.

- **Language**: Python 3.10+ · **UI**: PySide6 6.11.2 · **Packaging**: pip / setuptools
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

## Build, Test & Verify

```bash
pip install -r requirements.txt        # runtime deps
pip install -r dev_requirements.txt    # dev deps
pytest                                 # tests (Qt UI scripts excluded)
python -m build                        # build (swap pyproject.toml <-> dev.toml for the dev package)
```

- **Run tooling through the project venv** (`.venv/Scripts/python.exe` on Windows). Git Bash here has
  no `python` on PATH, so drive ruff and pytest from PowerShell. Machine-specific interpreter paths
  are set as `$JEDITOR_VENV_PYTHON` and `$PYBREEZE_VENV_PYTHON` in the untracked
  `.claude/settings.local.json`, so they stay out of version control.
- **Every round of verification**: `ruff check` clean, `pytest` green, and — when the change touches
  translations — PyBreeze's language parity test (`test_language_parity.py`) green.
- Before pushing anything that touches Qt, also run what CI runs:
  `python ./test/qt_ui/unit_test/start_qt_ui.py` and `.../extend_test.py` with
  `QT_QPA_PLATFORM=offscreen`.

## Testing

- `QT_QPA_PLATFORM=offscreen` is needed to run GUI/Qt tests locally, **but CI's unit-test step does
  not set it** and uses the real Windows platform plugin. Do not set it when reproducing CI.
- **A Qt test crash (`0xC0000409`) is almost always Qt's `qFatal`**, typically
  `QThread: Destroyed while thread is still running`. pytest swallows the message — use `pytest -s`
  to see it, and give every `QThread` subclass a `setObjectName(...)` so the message names the
  culprit. The crash site drifts, so judge by the crash rate over three runs rather than one, and
  confirm the baseline (a clean worktree at HEAD) is stable first.
- **Never construct a `QKeyEvent` and hand it to a handler in a test.** Qt keeps the object while
  Python may collect it first, and the next turn of the event loop takes the whole interpreter down.
  Use `QTest.keyClick(s)`.
- No empty (S1186) or duplicated (S4144) tests.
- Public classes and functions get docstrings covering purpose, args, returns and raises.

## CI

- The matrix is **Python 3.10 / 3.11 / 3.12** on Windows. To reproduce a 3.10-only failure locally,
  use `uv python install 3.10` plus `uv venv`.
- Watch a run with `gh run watch <run-id> --exit-status`, or `gh pr checks <PR> --watch` for a PR.
- For analyser detail, the tokens live in the environment:
  - Codacy — header `project-token: $CODACY_PROJECT_TOKEN` against
    `https://app.codacy.com/api/v3/analysis/organizations/gh/Integration-Automation/repositories/<repo>/pull-requests/<PR>/issues`
    lists file:line and rule id directly.
  - SonarCloud — `$SonarCloudToken` against
    `https://sonarcloud.io/api/issues/search?componentKeys=<key>&pullRequest=<PR>`.
- Treat an analyser finding as a claim to verify, not an order. Where a finding is wrong (a
  bilingual comment read as commented-out code) or where following it would make the code more
  fragile, leave the code correct and record why.

## Design Principles

- **MVC separation**: widgets in `pyside_ui/`; logic in `code_scan/`, `git_client/`, `utils/`.
  Pair every feature as pure logic (`utils/`) + a thin Qt integration layer.
- **Patterns**: plugins extend via `plugins/plugin_loader.py` without touching core; Qt signals/slots
  for decoupling; interchangeable formatting/highlighting strategies; single responsibility, no god
  classes.
- **SOLID / DRY**: compose over inherit, depend on abstractions, share code through `utils/`. Never
  restate a table of keys and defaults that another module already owns — derive it.
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
- Union type expressions (`X | None`), not `typing.Union`.
- f-strings everywhere except `logging`, which uses lazy `%` formatting.
- Comments are bilingual (Chinese then English) and explain *why*, not *what*.

## Exceptions & Resources

- Never `except:` or `except Exception: pass` — name the type, and log or re-raise.
- Do not list an exception a sibling in the same clause already covers (`IndentationError` under
  `SyntaxError`, `UnicodeDecodeError` under `ValueError`).
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
- A dependency nothing imports is not worth patching — remove it.
- **Regular expressions** must not backtrack super-linearly (S8786): no two greedy quantifiers that
  can trade against each other, and no lazy quantifier driven across a whole line.

## Stage commits, `PROGRESS.md`, `docs/updates/` and `architecture.md`

Workspace rule shared by every repository under `D:\Codes` (full text: `D:\Codes\CLAUDE.md`).

- **Commit at every stage.** A stage is the smallest piece of work that leaves the repository consistent and passes this project's checks (definition of done, tests, lint): one finished `PROGRESS.md` item, or one self-contained step of a larger one. Commit it before starting the next stage, before switching to another repository, and before the session ends. Do not leave work uncommitted across sessions; if a stage cannot be finished, commit the consistent part and record the rest in `PROGRESS.md`.
  - Stage only the files that stage touched (`git add <path>`, never `git add -A`), follow this file's commit-message rules, and never add AI attribution.
  - Committing is not pushing: push or open a PR only as this project's branch flow says or when asked.
- **`PROGRESS.md`** (repository root, tracked) holds outstanding work only: no finished items, no history, no rules.
- **`docs/updates/`** records finished work: one batch file per month (`YYYY-MM.md`), one entry per piece of work headed `## U-YYYYMMDD-NN · date · title · #tags`, and an index with query commands in `docs/updates/README.md`. When a `PROGRESS.md` item is done, delete it and add a `#done` entry plus its index row in the same commit.
- **`architecture.md`** (repository root) is the short architecture overview: layers, entry points, main flows, extension points, cross-project boundaries. Update it in the same commit whenever a change alters any of those. `architecture_explore.md` stays the detailed per-module map under its own rule in this file.
- **Cross-project contracts** are listed in `architecture.md` §6: what other repositories rely on here (CLI flags, import paths, constructor arguments, file layouts) and what this repository relies on elsewhere. No test here protects them, so never rename or remove one without changing its consumers in the same round, and update §6 whenever a contract is added or changes.

## Git & Commits

- English, imperative, one logical change per commit (e.g. "Add plugin hot-reload support").
  Stage deliberately — `git add -u` bundles unrelated work into the wrong commit.
- `main` = stable, `dev` = active development.
- **Merge PRs with a merge commit** (`gh pr merge <PR> --merge`), never squash. This holds for both
  this repo and PyBreeze.
- After a merge, `dev`'s `pyproject.toml` version lags `main`. That is the existing flow, not a bug.
- **No AI attribution anywhere** — commit messages, trailers, branch names, PR titles/descriptions,
  issues, code comments and documentation must never mention an AI tool, assistant, agent, model or
  vendor. No `Co-Authored-By:` or "Generated with ..." footers. PRs describe *what changed and why*.

## Cross-repo (PyBreeze)

- Run PyBreeze's tests as `pytest test/test_utils`. A bare `pytest` or `pytest test` also collects
  `test/unit_test/start_automation`, which launches the app and ends in "no output, exit 0".
