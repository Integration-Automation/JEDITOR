Configuration & Settings
=========================

JEditor stores all user configuration in the ``.jeditor/`` directory under the current
working directory. Settings are automatically created on first launch and persist between sessions.

Settings Files
---------------

user_setting.json
^^^^^^^^^^^^^^^^^^

The main settings file controls editor behavior and appearance:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Description
   * - ``ui_font``
     - Font family for the main UI (menus, panels, dialogs)
   * - ``ui_font_size``
     - Font size for the main UI
   * - ``font``
     - Font family for the code editor
   * - ``font_size``
     - Font size for the code editor
   * - ``language``
     - UI language (``English``, ``Traditional Chinese``, ``Simplified Chinese``,
       ``Japanese``, or plugin-provided). Taken from the system locale on a first run.
   * - ``ui_style``
     - UI theme style file, e.g. ``dark_amber.xml``
   * - ``encoding``
     - Default file encoding (``utf-8``, ``GBK``, ``latin-1``)
   * - ``last_file``
     - Path to the last opened file (restored on launch)
   * - ``python_compiler``
     - Path to the Python interpreter for code execution
   * - ``max_line_of_output``
     - Maximum lines in the output panel (default: 200,000)
   * - ``recent_files``
     - List of recently opened files
   * - ``indent_size``
     - Indentation size in spaces (default: 4)
   * - ``open_files``
     - The tabs that were open at the last shutdown
   * - ``restore_session``
     - Whether to reopen those tabs on launch (default: ``true``)
   * - ``shortcuts``
     - Keys the user reassigned; only what differs from a default is stored

user_color_setting.json
^^^^^^^^^^^^^^^^^^^^^^^^

Controls the color scheme for the editor and output:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Description
   * - ``line_number_color``
     - Line number text
   * - ``line_number_background_color``
     - Line number gutter background
   * - ``current_line_color``
     - Current line highlight
   * - ``normal_output_color`` / ``error_output_color`` / ``warning_output_color``
     - Output panel text
   * - ``syntax_keyword_color`` / ``syntax_string_color`` /
       ``syntax_comment_color`` / ``syntax_number_color``
     - Syntax highlighting
   * - ``diff_added_marker_color`` / ``diff_modified_marker_color`` /
       ``diff_removed_marker_color``
     - Git change markers in the gutter
   * - ``blame_annotation_color``
     - Inline blame text
   * - ``lint_underline_color``
     - Underline under a lint diagnostic
   * - ``bookmark_marker_color`` / ``fold_marker_color`` /
       ``breakpoint_marker_color``
     - Gutter markers
   * - ``occurrence_highlight_color``
     - Other occurrences of the word under the caret
   * - ``extra_cursor_color``
     - Additional carets
   * - ``indent_guide_color`` / ``trailing_whitespace_color``
     - Indent guides and trailing whitespace shading
   * - ``minimap_background_color`` / ``minimap_line_color`` /
       ``minimap_viewport_color``
     - Minimap

All colors are specified as RGB arrays, e.g., ``[255, 0, 0]`` for red. Any key left out
falls back to the current theme's value, so a partial file is fine.

ai_config.json
^^^^^^^^^^^^^^^

AI assistant configuration (see :doc:`ai_assistant` for details):

- API base URL
- API key
- Model name
- System prompt template

Unlike the two files above, this one is read but never written — create it yourself if
you want the settings loaded on every launch.

Theming
--------

JEditor supports dark and light themes via `qt-material <https://github.com/UN-GCPDS/qt-material>`_:

- **Default:** Dark Amber theme
- Switch themes from the **UI Style** menu
- The editor's own colors follow the window style: switching to a light theme moves the
  gutter, current-line and syntax colors to a light set. A color you picked yourself is
  left alone — only those still at a default follow the theme

Font Customization
-------------------

JEditor provides separate font settings for the UI and the code editor:

**UI Font:**
- Change from the **File** menu
- Affects menus, panels, dialogs, and buttons
- Font family and size are independently configurable

**Editor Font:**
- Change from the **Text** menu
- Affects the code editing area only
- Font family and size are independently configurable
- Changes take effect immediately

Dockable Panels
-----------------

JEditor's UI is built with Qt's dock widget system, making panels rearrangeable:

- **Editor** — The main code editing area
- **Output** — Code execution results
- **File Tree** — Project directory browser
- **Console** — Shell / IPython console
- **AI Chat** — AI assistant panel
- **Git** — Git client panel, branch tree and diff viewer
- **Browser** — Built-in web browser
- **Variable Inspector** — Runtime variable debugging
- **Problems** — Lint and language-server diagnostics
- **Outline** — Classes, functions and variables in the current file
- **Tests** — pytest results, failures and coverage
- **TODO** — ``TODO`` / ``FIXME`` / ``HACK`` comments found across the project

All panels can be:

- Dragged to different positions within the window
- Floated as independent windows
- Stacked as tabs in the same dock area
- Hidden or restored from the **Dock** menu

System Tray
------------

JEditor supports system tray integration:

- Minimize to the system tray instead of closing
- Tray icon with quick access to restore the window
- Continues running in the background when minimized

Multi-Language UI
------------------

**Built-in Languages:**

- English
- Traditional Chinese (繁體中文)
- Simplified Chinese (简体中文)
- Japanese (日本語)

Each is complete. Simplified Chinese is written in mainland vocabulary rather than
converted from the traditional text, where 檔案/文件, 資料夾/文件夹 and 程式/程序 all
differ.

**Following the System:**

On a first run the language is taken from the system locale rather than defaulting to
English. Chinese is resolved by script: ``zh-Hant`` and the Taiwan, Hong Kong and Macau
regions get traditional characters, anything else simplified. What was detected is
written to ``user_setting.json``, so from then on it is simply the chosen language.

**Switching:**

Pick a language from the **Language** menu. No restart is needed — the menus, toolbar,
panels, tabs and status bar are relabelled at once. File and branch names shown on tabs
are left alone.

**Fallback:**

A key a language has not translated shows the English text rather than a blank label, so
a language can be added before it is finished.

**Adding Languages via Plugins:**

Additional languages can be added through the plugin system (see :doc:`plugins`). Locale
rules for Korean, Spanish, French, German, Russian and Portuguese are already in place;
each needs only its dictionary.
