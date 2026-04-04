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

JSON Reformatting
------------------

JEditor can format and validate JSON files:

- **Shortcut:** ``Ctrl+J``
- Pretty-prints JSON with proper indentation
- Validates JSON syntax and reports errors
- Available from the **Check Code Style** menu
