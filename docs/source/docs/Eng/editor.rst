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

Language Server Support
------------------------

Files that are not Python are served by a language server over stdio, so the editor
offers the same assistance for them as jedi gives Python:

- Completion, hover documentation and signature help while typing
- Go to definition, find references and rename across the project
- Whole-file formatting and quick fixes for reported problems
- Document symbols, which feed the outline panel

One server is shared by every tab that needs it, keyed by its command and the project
root, rather than one process per open file. Servers are configured per file suffix —
TypeScript, Rust, Go, C/C++, Lua and JSON are set up out of the box. A server that is
not installed simply means no completions for that language; it is never an error.

Diagnostics reported by the server appear in the same underlines and Problems panel as
ruff's.

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

Encoding and Line Endings
--------------------------

JEditor supports multiple file encodings:

- **UTF-8** (default)
- **GBK**
- **Latin-1**
- Automatic encoding detection when opening files
- Per-file encoding selection from the **File > Encoding** menu
- Encoding is preserved when saving files

Changing the encoding re-reads an unmodified file, so mojibake can be fixed in place.
Unsaved work is never discarded: if the tab has been edited, the file is not re-read.

A file's line-ending style (LF, CRLF or CR) is detected when it opens and written back
unchanged when it saves, so editing one line of a CRLF file no longer rewrites every
line. Both the encoding and the line ending of the current tab are shown in the status
bar, and the line ending can be changed from **File > Line Ending**.

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

Navigation
-----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Feature
     - Description
   * - **Command Palette** (``Ctrl+Shift+A``)
     - Fuzzy-search every menu command by name or menu path and run it. Matches are
       ranked by word boundaries, consecutive characters and prefixes, and each row
       shows the command's own shortcut.
   * - **Quick Open** (``Ctrl+P``)
     - Fuzzy-search the project tree by file name or folder path. Indexing runs in a
       background thread and skips VCS, cache, virtualenv and build directories.
       Typing ``>`` first switches the same picker into command mode.
   * - **Go to Symbol** (``Ctrl+Shift+O``)
     - Jump to any class, function, method or module-level variable in the current
       file. Python is parsed with the standard library ``ast`` module, so no code is
       executed; a file that does not parse simply yields no symbols.
   * - **Navigation History** (``Alt+Left`` / ``Alt+Right``)
     - Move back and forward through cursor jumps like a browser. A jump records both
       where you came from and where you went, so "back" returns to where you started.
   * - **Recent Locations** (``Ctrl+Alt+E``)
     - Pick from the places you have jumped to recently.

Document Outline
-----------------

A dockable tree of the current file's classes, methods, functions and module-level
variables. Python is parsed with ``ast``, so no code runs; other languages are asked of
their language server, so a TypeScript or Rust file gets an outline too. Double-click a
row to jump to the definition.

Multiple Carets
----------------

Edit in several places at once:

- ``Ctrl+Shift+L`` puts a caret at the end of every selected line
- ``Ctrl+Alt+N`` adds one at the next occurrence of the word under the caret
- ``Ctrl+Alt+Shift+Up`` / ``Ctrl+Alt+Shift+Down`` adds one on the line above or below
- ``Alt``-click adds or removes a caret anywhere
- ``Ctrl+Shift+Esc``, or a plain click, returns to a single caret

Every caret moves together with the arrow keys, ``Home`` and ``End``, and ``Shift``
with any of those extends a selection at each one. Typing, ``Backspace`` and ``Delete``
apply at all of them as a single undo step, replacing each selection where there is one.

Code Folding
-------------

Collapse and expand blocks from the gutter fold triangles or the keyboard
(``Ctrl+Shift+[`` for the fold at the caret, ``Ctrl+Alt+[`` / ``Ctrl+Alt+]`` for all).

- Python and other indented files fold on indentation
- The C-family languages (JavaScript, TypeScript, Rust, Go, C/C++, Java, JSON) fold on
  brace pairs instead, so a brace on its own line still opens a region
- Braces inside strings and comments are skipped — one in a string would otherwise throw
  every pair after it out of step
- Folding only toggles line visibility; it never modifies the text, so saving always
  writes the complete file
- Folds self-heal after edits: a fold whose header no longer exists reopens rather than
  hiding the wrong lines

Bookmarks
----------

Mark lines with ``Ctrl+Alt+K`` (or click the gutter) and jump between them with
``Ctrl+Alt+L`` and ``Ctrl+Alt+J``. Bookmarks are anchored to the text, so they follow
their code when lines are inserted or removed above them instead of drifting.

Snippets
---------

Type a trigger word and press ``Tab`` to expand it, then ``Tab`` through the
placeholders with each default value selected. A placeholder used more than once only
has to be typed once — the repeats follow as you type.

Snippets use the usual ``$1`` / ``${2:default}`` / ``$0`` notation, so existing snippets
drop straight into ``snippets.json``, and there are per-language sets on top of the
shared ones. Edit them from **Tab > Edit Snippets** rather than by hand; a missing or
broken file falls back to the built-in Python set.

Minimap
--------

``Ctrl+Alt+M`` toggles an overview of the whole file, drawn as bars following each
line's length and indentation, with a band marking what is on screen. Marks down the
sides show lint diagnostics, git changes, and whatever you are currently looking for —
the search box's hits while a search is open, and otherwise the other occurrences of the
word under the caret. Click or drag to jump. Large files are sampled rather than drawn
line by line.

Split View
-----------

``Ctrl+Alt+\`` opens a second view of the same file. Both views share one document, so
an edit in either side shows up in the other at once, while scrolling and the caret stay
independent.

Lint Diagnostics
-----------------

Findings from ``ruff`` are underlined in the editor and listed in a Problems dock panel
(rule, message, line); double-click a row to jump to it. The **buffer** is checked, not
the file on disk, so unsaved edits are covered. The run happens on a worker thread after
typing pauses, and a stale result from a superseded run is discarded. If ``ruff`` is not
installed, or a run fails, the editor simply shows no diagnostics rather than reporting
an error.

Occurrence Highlighting
------------------------

Placing the caret on an identifier highlights every other whole-word occurrence of it in
the file. Keywords and single characters are ignored, and the scan is skipped on very
large files to keep caret movement instant.

Customizing Shortcuts
----------------------

**Style > Keyboard Shortcuts** lists every command's keys in one editable table. Two
commands cannot be given the same keys — Qt runs neither of them when that happens — so
the dialog refuses to save a clash. A change takes effect immediately, and only what
differs from a default is stored. See :doc:`keyboard_shortcuts` for the full list.
