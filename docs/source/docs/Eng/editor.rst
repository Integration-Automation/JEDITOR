Code Editor
============

JEditor's core is a powerful multi-tab code editor built on top of Qt's ``QPlainTextEdit``, designed
for speed, flexibility, and a smooth development experience.

Multi-Tab Editing
------------------

Work on multiple files simultaneously using the tab-based interface:

- Open multiple files in separate tabs
- Switch between tabs by clicking
- Close tabs individually
- Drag and drop files from the file system into the editor
- The current file path and tab state are tracked automatically

File Operations
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Action
     - Description
   * - **New File** (``Ctrl+N``)
     - Create a new empty file
   * - **Open File** (``Ctrl+O``)
     - Open an existing file and load it into a tab
   * - **Open Folder** (``Ctrl+K``)
     - Open a project folder and display it in the file tree
   * - **Save File** (``Ctrl+S``)
     - Save the current tab's content to disk

Recent Files
^^^^^^^^^^^^^

JEditor keeps a list of recently opened files for quick access, available from the **File** menu.

Auto-Save
^^^^^^^^^^

JEditor includes an automatic save feature that periodically saves your work:

- Runs in a background thread per open file
- Configurable save interval
- Detects external file changes and handles conflicts
- Tracks file modification state

Syntax Highlighting
--------------------

JEditor provides built-in Python syntax highlighting and supports additional languages through plugins.

**Built-in Python Highlighting** includes:

- Keywords (``if``, ``else``, ``for``, ``while``, ``def``, ``class``, etc.)
- Built-in functions (``print``, ``len``, ``range``, etc.)
- Strings (single-line and multi-line)
- Comments
- Decorators
- Numbers
- Customizable colors via the color settings

**Plugin-based Language Support:**

Additional languages can be added through the plugin system. Pre-built plugins are available for:

- C (``.c``)
- C++ (``.cpp``, ``.cxx``, ``.cc``, ``.h``, ``.hpp``, ``.hxx``)
- Go (``.go``)
- Java (``.java``)
- Rust (``.rs``)

See :doc:`plugins` for details on creating language plugins.

Auto-Completion
----------------

JEditor integrates `Jedi <https://jedi.readthedocs.io/>`_ for intelligent Python code completion:

- Context-aware suggestions based on the current code
- Supports virtual environment (venv) for accurate package completions
- Runs in a background thread so the UI stays responsive
- Configurable case-sensitivity and completion behavior

Line Numbers
-------------

The editor displays line numbers in a dedicated gutter on the left side:

- Line numbers update dynamically as the document changes
- Customizable colors for line number text and background
- Current line number is highlighted for easy reference

Current Line Highlight
-----------------------

The line where the cursor is currently positioned is highlighted with a distinct background color,
making it easy to identify your editing position. The highlight color is customizable through the
color settings.

File Tree
----------

When you open a folder (``Ctrl+K``), JEditor displays a file tree on the left side:

- Browse the full directory structure of your project
- Click on any file to open it in a new editor tab
- Supports expanding and collapsing directories
- Scrollable navigation for large projects

Encoding Support
-----------------

JEditor supports multiple file encodings:

- **UTF-8** (default)
- **GBK**
- **Latin-1**
- Automatic encoding detection when opening files
- Per-file encoding selection from the **File > Encoding** menu
- Encoding is preserved when saving files

Search & Replace
-----------------

JEditor provides powerful search and replace functionality:

**File Search:**

- Search within the current file
- Case-sensitive and case-insensitive options
- Regular expression (regex) support

**Project-Wide Search:**

- Search across all files in an opened folder
- Results displayed in a table with file path and line number
- Click on a result to navigate directly to the match
- Runs in a background thread for large codebases

**Replace:**

- Replace single occurrences or all matches at once
- Supports the same options as search (case, regex)
