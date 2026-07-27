Code Quality & Formatting
==========================

JEditor integrates multiple code quality tools to help you write clean, consistent code.

YAPF Python Formatting
-----------------------

`YAPF <https://github.com/google/yapf>`_ (Yet Another Python Formatter) reformats Python code
to conform to the Google style guide.

- **Shortcut:** ``Ctrl+Shift+Y``
- Formats the entire file
- Applies consistent indentation, spacing, and line breaks
- Available from the **Check Code Style** menu

**Format on Save:**

YAPF can also run every time a file is saved, keeping the caret on its line. Source that
cannot be parsed is left alone rather than blocking the save.

PEP 8 Checking
----------------

JEditor integrates `pycodestyle <https://pycodestyle.pycqa.org/>`_ for PEP 8 compliance checking.

- **Shortcut:** ``Ctrl+Alt+P``
- Reports violations with line number and offset
- Customizable checks (W191 tab warnings are filtered by default)
- Available from the **Check Code Style** menu

Ruff Linting
-------------

`Ruff <https://docs.astral.sh/ruff/>`_ is an extremely fast Python linter that runs automatically
in the background:

- File system monitoring via ``watchdog`` detects when files change
- Linting runs in a background thread to keep the UI responsive
- Debounced file checks prevent excessive runs during rapid editing
- Comprehensive Python linting rules covering hundreds of checks
- Results are reported without blocking your workflow

The **buffer** is checked, not the file on disk, so unsaved edits are covered, and a
stale result from a superseded run is discarded. If ``ruff`` is not installed, or a run
fails, the editor simply shows no diagnostics rather than reporting an error.

Problems Panel
---------------

Every diagnostic — from ruff for Python, and from the language server for other
languages — is underlined in the editor and listed in the Problems dock panel with its
rule, message and line. Double-click a row to jump to it.

Test Panel
-----------

Run pytest from a dock panel and read the results, failures first, with the summary as
the status line:

- Run everything, only the selection, or only what failed last time
- Selecting a failure shows its traceback in a pane below the list
- Double-click a row to open that test at the failing line
- A coverage box adds the total beside the summary, which needs ``pytest-cov`` installed
  in the project being tested
- The run happens in a background process, so the editor stays usable

JSON Reformatting
------------------

JEditor can format and validate JSON files:

- **Shortcut:** ``Ctrl+J``
- Pretty-prints JSON with proper indentation
- Validates JSON syntax and reports errors
- Available from the **Check Code Style** menu

Text Transforms
----------------

The **Text** menu applies whole-document or selection-wide edits, each as a single undo
step:

- **Trim Trailing Whitespace** — strip trailing whitespace from every line, preserving
  the caret position
- **Convert Indentation** — convert leading indentation between tabs and spaces, using
  the configured indent size. Only leading whitespace is touched, so tabs and spaces
  inside strings are never altered
- **Case conversion** — upper, lower, swap or title case
- **Naming style** — ``snake_case`` / ``camelCase`` / ``PascalCase`` / ``kebab-case``
- **Number base** — hex, decimal and binary
- **Encode / decode** — Base64, URL, HTML entities and JSON string escaping. A decoder
  that fails leaves the text untouched
- **Line operations** — natural sort, remove duplicate lines, remove blank lines, reverse
  line order, or align lines on a delimiter such as ``=``
- **Statistics** — line, word and character counts for the document or the selection

Indent Size
------------

Tab-indent, unindent and ``Enter`` auto-indent all honour the configured indent size
(**Text > Indent Size**), and the indent width is auto-detected from a file's own content
when it is opened.
