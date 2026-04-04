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
   * - ``ui_font_family``
     - Font family for the main UI (menus, panels, dialogs)
   * - ``ui_font_size``
     - Font size for the main UI
   * - ``editor_font_family``
     - Font family for the code editor
   * - ``editor_font_size``
     - Font size for the code editor
   * - ``language``
     - UI language (``English``, ``Traditional Chinese``, or plugin-provided)
   * - ``theme``
     - UI theme style (dark or light material themes)
   * - ``encoding``
     - Default file encoding (``UTF-8``, ``GBK``, ``Latin-1``)
   * - ``last_open_file``
     - Path to the last opened file (restored on launch)
   * - ``python_compiler``
     - Path to the Python interpreter for code execution
   * - ``max_output_lines``
     - Maximum lines in the output panel (default: 200,000)
   * - ``recent_files``
     - List of recently opened files
   * - ``indent_size``
     - Indentation size in spaces (default: 4)

user_color_setting.json
^^^^^^^^^^^^^^^^^^^^^^^^

Controls the color scheme for the editor and output:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Description
   * - ``line_number_color``
     - RGB color for line number text
   * - ``line_number_bg_color``
     - RGB color for the line number gutter background
   * - ``current_line_color``
     - RGB color for the current line highlight
   * - ``normal_output_color``
     - RGB color for normal output text
   * - ``error_output_color``
     - RGB color for error output text
   * - ``warning_output_color``
     - RGB color for warning output text

All colors are specified as RGB arrays, e.g., ``[255, 0, 0]`` for red.

ai_config.json
^^^^^^^^^^^^^^^

AI assistant configuration (see :doc:`ai_assistant` for details):

- API base URL
- API key
- Model name
- System prompt template

Theming
--------

JEditor supports dark and light themes via `qt-material <https://github.com/UN-GCPDS/qt-material>`_:

- **Default:** Dark Amber theme
- Switch themes from the **UI Style** menu
- Theme changes may require an application restart to fully take effect

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
- **Git** — Git client panel
- **Browser** — Built-in web browser
- **Variable Inspector** — Runtime variable debugging

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

JEditor supports multiple UI languages:

**Built-in Languages:**

- English (default)
- Traditional Chinese (繁體中文)

**Adding Languages via Plugins:**

Additional languages can be added through the plugin system (see :doc:`plugins`).
Language changes take effect after restarting the application.

Switch languages from the **Language** menu.
