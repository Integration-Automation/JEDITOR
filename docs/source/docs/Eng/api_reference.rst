API Reference
==============

JEditor exposes a public Python API that allows you to use it as a library, extend its
functionality, or integrate it into your own applications.

Starting the Editor
--------------------

.. code-block:: python

   from je_editor import start_editor

   start_editor()

Launches the full JEditor application. This is the simplest way to start the editor
programmatically.

Core Classes
-------------

EditorMain
^^^^^^^^^^^

The main window class that contains the entire editor UI.

.. code-block:: python

   from je_editor import EditorMain

EditorWidget
^^^^^^^^^^^^^

The code editor widget (single editor tab) — a customized ``QPlainTextEdit``.

.. code-block:: python

   from je_editor import EditorWidget

FullEditorWidget
^^^^^^^^^^^^^^^^^

A complete editor widget with line numbers, syntax highlighting, and output display,
suitable for embedding in dock panels.

.. code-block:: python

   from je_editor import FullEditorWidget

MainBrowserWidget
^^^^^^^^^^^^^^^^^^

The embedded web browser widget.

.. code-block:: python

   from je_editor import MainBrowserWidget

Extending the Editor with Custom Tabs
---------------------------------------

Use ``EDITOR_EXTEND_TAB`` to add custom tabs to JEditor:

.. code-block:: python

   from je_editor import start_editor, EDITOR_EXTEND_TAB

   EDITOR_EXTEND_TAB.update({"My Tab": MyCustomWidget})

   start_editor()

See :doc:`how_to_extend_using_pyside` for a complete example.

Process Managers
-----------------

ExecManager
^^^^^^^^^^^^

Manages program execution (running Python scripts and compiled binaries).

.. code-block:: python

   from je_editor import ExecManager

ShellManager
^^^^^^^^^^^^^

Manages shell command execution.

.. code-block:: python

   from je_editor import ShellManager

Syntax Highlighting
--------------------

PythonHighlighter
^^^^^^^^^^^^^^^^^^

The built-in Python syntax highlighter.

.. code-block:: python

   from je_editor import PythonHighlighter

syntax_extend_setting_dict / syntax_rule_setting_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Dictionaries that define syntax keywords and rules for the highlighter.

.. code-block:: python

   from je_editor import syntax_extend_setting_dict, syntax_rule_setting_dict

Settings
---------

user_setting_dict
^^^^^^^^^^^^^^^^^^

Dictionary containing all user settings (font, language, theme, etc.).

.. code-block:: python

   from je_editor import user_setting_dict

user_setting_color_dict
^^^^^^^^^^^^^^^^^^^^^^^^

Dictionary containing all color settings.

.. code-block:: python

   from je_editor import user_setting_color_dict

Multi-Language
---------------

language_wrapper
^^^^^^^^^^^^^^^^^

A function that returns the translated string for a given key, based on the current language.

.. code-block:: python

   from je_editor import language_wrapper

   label = language_wrapper("file_menu_label")  # Returns "File" or translated equivalent

english_word_dict / traditional_chinese_word_dict
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Built-in translation dictionaries.

.. code-block:: python

   from je_editor import english_word_dict, traditional_chinese_word_dict

Plugin API
-----------

Programming Language Plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_programming_language,
       get_programming_language_plugin,
       get_all_programming_language_suffixes,
   )

- ``register_programming_language(suffix, syntax_words, syntax_rules=None)`` — Register a new language
- ``get_programming_language_plugin(suffix)`` — Get the plugin for a file extension
- ``get_all_programming_language_suffixes()`` — List all registered extensions

Natural Language Plugins
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_natural_language,
       get_natural_language_plugin,
       get_all_natural_languages,
   )

- ``register_natural_language(language_key, display_name, word_dict)`` — Register a translation
- ``get_natural_language_plugin(language_key)`` — Get a translation dictionary
- ``get_all_natural_languages()`` — List all registered languages

Run Configuration Plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_plugin_run_config,
       get_all_plugin_run_configs,
       get_plugin_run_config_by_suffix,
   )

- ``register_plugin_run_config(config)`` — Register a run configuration
- ``get_all_plugin_run_configs()`` — List all run configurations
- ``get_plugin_run_config_by_suffix(suffix)`` — Get the run config for a file extension

Plugin Metadata
^^^^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import (
       register_plugin_metadata,
       get_all_plugin_metadata,
   )

- ``register_plugin_metadata(name, author, version)`` — Register plugin info
- ``get_all_plugin_metadata()`` — List all registered plugin metadata

Plugin Loader
^^^^^^^^^^^^^^

.. code-block:: python

   from je_editor import load_external_plugins

   load_external_plugins()

Scans the ``jeditor_plugins/`` directory and loads all discovered plugins.

Logging
--------

.. code-block:: python

   from je_editor import jeditor_logger

   jeditor_logger.info("Custom log message")

The ``jeditor_logger`` is a standard Python logger that writes to ``JEditor.log``.

Exceptions
-----------

JEditor defines a hierarchy of custom exceptions:

.. code-block:: python

   from je_editor import (
       JEditorException,              # Base exception
       JEditorExecException,          # Execution errors
       JEditorRunOnShellException,    # Shell execution errors
       JEditorSaveFileException,      # File save errors
       JEditorOpenFileException,      # File open errors
       JEditorContentFileException,   # File content errors
       JEditorCantFindLanguageException,  # Language not found
       JEditorJsonException,          # JSON parsing errors
   )
