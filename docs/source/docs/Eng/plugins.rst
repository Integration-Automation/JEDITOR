Plugin System
==============

JEditor features a comprehensive plugin system that allows you to extend the editor with new
programming language support, UI translations, and custom run configurations.

Plugin Types
-------------

JEditor supports four types of plugins:

1. **Programming Language Plugins** — Add syntax highlighting for new languages
2. **Natural Language (Translation) Plugins** — Add UI translations
3. **Run Configuration Plugins** — Define how to execute files of specific types
4. **Plugin Metadata** — Version and author information for the Plugins menu

Plugin Directory
-----------------

Plugins are auto-discovered from the ``jeditor_plugins/`` directory under your working directory:

.. code-block:: text

   working_directory/
     jeditor_plugins/
       my_syntax.py            # Single-file plugin
       my_language.py
       my_package/             # Package plugin
         __init__.py

**Discovery Rules:**

- Files starting with ``_`` or ``.`` are ignored
- Each plugin **must** define a ``register()`` function
- Package plugins use ``__init__.py`` as the entry point
- Duplicate plugin names are handled by first-found-wins

Plugin Metadata
----------------

Each plugin can optionally define metadata that appears in the **Plugins** menu:

.. code-block:: python

   PLUGIN_NAME = "My Plugin"       # Display name
   PLUGIN_AUTHOR = "Your Name"     # Author
   PLUGIN_VERSION = "1.0.0"        # Version

If omitted, the filename is used as the plugin name.

Programming Language Plugin
----------------------------

Add syntax highlighting for any programming language.

**API:**

.. code-block:: python

   from je_editor.plugins import register_programming_language

   register_programming_language(
       suffix=".ext",              # File extension
       syntax_words={...},         # Keyword groups
       syntax_rules={...},         # Regex rules (optional)
   )

**syntax_words format:**

Define keyword groups with their highlight colors:

.. code-block:: python

   from PySide6.QtGui import QColor

   syntax_words = {
       "group_name": {
           "words": ("keyword1", "keyword2", ...),
           "color": QColor(r, g, b),
       },
       # More groups...
   }

**syntax_rules format:**

Define regex patterns for complex syntax elements (comments, strings, etc.):

.. code-block:: python

   syntax_rules = {
       "rule_name": {
           "rules": (r"regex_pattern", ...),
           "color": QColor(r, g, b),
       },
   }

**Full Example — Go Syntax Highlighting:**

.. code-block:: python

   """Go syntax highlighting plugin."""
   from PySide6.QtGui import QColor
   from je_editor.plugins import register_programming_language

   PLUGIN_NAME = "Go Syntax Highlighting"
   PLUGIN_AUTHOR = "Your Name"
   PLUGIN_VERSION = "1.0.0"

   go_syntax_words = {
       "keywords": {
           "words": (
               "break", "case", "chan", "const", "continue",
               "default", "defer", "else", "fallthrough", "for",
               "func", "go", "goto", "if", "import",
               "interface", "map", "package", "range", "return",
               "select", "struct", "switch", "type", "var",
           ),
           "color": QColor(86, 156, 214),
       },
       "types": {
           "words": (
               "bool", "byte", "complex64", "complex128",
               "float32", "float64", "int", "int8", "int16",
               "int32", "int64", "rune", "string", "uint",
               "uint8", "uint16", "uint32", "uint64", "uintptr",
               "error", "nil", "true", "false", "iota",
           ),
           "color": QColor(78, 201, 176),
       },
   }

   go_syntax_rules = {
       "single_line_comment": {
           "rules": (r"//[^\\n]*",),
           "color": QColor(106, 153, 85),
       },
   }


   def register() -> None:
       register_programming_language(
           suffix=".go",
           syntax_words=go_syntax_words,
           syntax_rules=go_syntax_rules,
       )

**Multiple File Extensions:**

If a language uses multiple extensions, register each one:

.. code-block:: python

   def register() -> None:
       for suffix in (".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"):
           register_programming_language(
               suffix=suffix,
               syntax_words=cpp_syntax_words,
               syntax_rules=cpp_syntax_rules,
           )

Natural Language (Translation) Plugin
---------------------------------------

Add UI translations for new languages.

**API:**

.. code-block:: python

   from je_editor.plugins import register_natural_language

   register_natural_language(
       language_key="French",          # Internal key
       display_name="Francais",        # Shown in Language menu
       word_dict={...},                # Translation dictionary
   )

The ``word_dict`` should contain the same keys as JEditor's built-in ``english_word_dict``.
Common keys include:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Key
     - Description
   * - ``application_name``
     - Window title
   * - ``file_menu_label``
     - File menu
   * - ``run_menu_label``
     - Run menu
   * - ``tab_name_editor``
     - Editor tab name
   * - ``language_menu_label``
     - Language menu
   * - ``help_menu_label``
     - Help menu

For a complete list, refer to ``je_editor.utils.multi_language.english.english_word_dict``
or the example plugin at ``exe/jeditor_plugins/french.py``.

**Full Example — Japanese Translation:**

.. code-block:: python

   """Japanese translation plugin."""
   from je_editor.plugins import register_natural_language

   PLUGIN_NAME = "Japanese Translation"
   PLUGIN_AUTHOR = "Your Name"
   PLUGIN_VERSION = "1.0.0"

   japanese_word_dict = {
       "application_name": "JEditor",
       "file_menu_label": "\u30d5\u30a1\u30a4\u30eb",
       "run_menu_label": "\u5b9f\u884c",
       "tab_name_editor": "\u30a8\u30c7\u30a3\u30bf",
       "language_menu_label": "\u8a00\u8a9e",
       # ... more keys
   }


   def register() -> None:
       register_natural_language(
           language_key="Japanese",
           display_name="\u65e5\u672c\u8a9e",
           word_dict=japanese_word_dict,
       )

Run Configuration Plugin
--------------------------

Define how to execute files of specific types.

**Interpreted Languages** (run directly):

.. code-block:: python

   PLUGIN_RUN_CONFIG = {
       "name": "Go",                   # Display name in menu
       "suffixes": (".go",),           # Supported file types
       "compiler": "go",               # Executable
       "args": ("run",),               # Args before file path
   }
   # Runs: go run file.go

**Compiled Languages** (compile then run):

.. code-block:: python

   PLUGIN_RUN_CONFIG = {
       "name": "C (GCC)",
       "suffixes": (".c",),
       "compiler": "gcc",
       "args": (),
       "compile_then_run": True,       # Compile first, then run
       "output_flag": "-o",            # Output binary flag
   }
   # Compiles: gcc file.c -o file
   # Then runs: ./file (Linux/Mac) or file.exe (Windows)

**Configuration Keys:**

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Key
     - Required
     - Description
   * - ``name``
     - Yes
     - Display name in the Run menu
   * - ``suffixes``
     - Yes
     - Tuple of file extensions
   * - ``compiler``
     - Yes
     - Compiler or interpreter executable
   * - ``args``
     - No
     - Extra arguments before the file path
   * - ``compile_then_run``
     - No
     - If ``True``, compile first then execute the binary
   * - ``output_flag``
     - No
     - Output file flag (default ``"-o"``)

Pre-built Plugins
------------------

JEditor ships with the following example plugins in ``exe/jeditor_plugins/``:

.. list-table::
   :header-rows: 1
   :widths: 30 20 25 25

   * - Plugin
     - Type
     - File Extensions
     - Run Support
   * - C Syntax Highlighting
     - Syntax
     - ``.c``
     - GCC compile & run
   * - C++ Syntax Highlighting
     - Syntax
     - ``.cpp``, ``.cxx``, ``.cc``, ``.h``, ``.hpp``, ``.hxx``
     - G++ compile & run
   * - Go Syntax Highlighting
     - Syntax
     - ``.go``
     - ``go run``
   * - Java Syntax Highlighting
     - Syntax
     - ``.java``
     - ``java``
   * - Rust Syntax Highlighting
     - Syntax
     - ``.rs``
     - rustc compile & run
   * - French Translation
     - Language
     - —
     - —

Plugin Browser
---------------

JEditor includes a Plugin Browser accessible from the **Plugin** menu:

- Browse available plugins
- GitHub API integration for discovering community plugins
- View plugin metadata (name, author, version)
