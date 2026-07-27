Getting Started
================

System Requirements
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Platform
     - Version
   * - Windows
     - Windows 10 / 11
   * - macOS
     - 10.5 ~ 11 Big Sur
   * - Linux
     - Ubuntu 20.04+
   * - Raspberry Pi
     - 3B+
   * - Python
     - 3.10, 3.11, 3.12

Installation
-------------

**Install from PyPI:**

.. code-block:: bash

   pip install je_editor

**Install from source:**

.. code-block:: bash

   git clone https://github.com/JE-Chen/je_editor.git
   cd je_editor
   pip install .

Dependencies
^^^^^^^^^^^^^

JEditor will automatically install the following dependencies:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Package
     - Purpose
   * - PySide6
     - GUI framework (Qt for Python)
   * - qt-material
     - Dark / Light material themes
   * - yapf
     - Python code formatting
   * - jedi
     - Python auto-completion
   * - ruff
     - Fast Python linter
   * - gitpython
     - Git operations
   * - langchain / langchain_openai
     - AI assistant (LLM integration)
   * - watchdog
     - File system monitoring
   * - pycodestyle
     - PEP 8 checking
   * - qtconsole
     - Jupyter / IPython console widget
   * - frontengine
     - Additional UI components

Launching JEditor
------------------

**From the command line:**

.. code-block:: bash

   python -m je_editor

**As a Python library:**

.. code-block:: python

   from je_editor import start_editor

   start_editor()

After launching, JEditor opens with a dark-themed interface by default. You can change the theme
from the **UI Style** menu at any time.

Project Structure
------------------

When JEditor starts, it creates a ``.jeditor/`` directory in the current working directory to store:

- ``user_setting.json`` — UI preferences, font, language, recent files, open tabs and any
  reassigned shortcuts
- ``user_color_setting.json`` — Color scheme for editor and output

Both are created automatically on first launch. A third file, ``ai_config.json``, is read
if you write it yourself; see :doc:`ai_assistant`.
