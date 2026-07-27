Keyboard Shortcuts
====================

JEditor provides keyboard shortcuts for common operations, making your workflow faster
and more efficient.

Most of the shortcuts on this page can be reassigned from **Style → Keyboard
Shortcuts**. Two commands cannot be given the same keys: Qt runs neither of them when
that happens, so the settings dialog refuses to save a clash. A change takes effect
immediately, and only what differs from a default is stored. The few keys handled
directly by the editing area — listed under `Fixed Keys`_ — are not in that list and
cannot be reassigned.

File Operations
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+N``
     - Create a new file
   * - ``Ctrl+O``
     - Open an existing file
   * - ``Ctrl+K``
     - Open a folder (project)
   * - ``Ctrl+S``
     - Save the current file
   * - ``Ctrl+Shift+S``
     - Save every modified tab

Search and Navigation
----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+F``
     - Find text in the file (also the browser's in-page search)
   * - ``Ctrl+H``
     - Find and replace
   * - ``Ctrl+Shift+F``
     - Search across files
   * - ``Ctrl+G``
     - Go to line
   * - ``Ctrl+P``
     - Quick open (go to file)
   * - ``Ctrl+Shift+A``
     - Command palette
   * - ``Ctrl+Shift+O``
     - Go to symbol
   * - ``Alt+Left`` / ``Alt+Right``
     - Navigate back / forward through cursor jumps
   * - ``Ctrl+Alt+E``
     - Recent locations

Code Editing
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+D``
     - Delete the current line or selection
   * - ``Ctrl+Shift+J``
     - Join the selected lines
   * - ``Ctrl+Alt+S``
     - Sort the selected lines
   * - ``Ctrl+Alt+Right`` / ``Ctrl+Alt+Left``
     - Expand / shrink the selection
   * - ``Ctrl+Alt+Up`` / ``Ctrl+Alt+Down``
     - Increment / decrement the number under the caret
   * - ``F2``
     - Rename every occurrence in the file

Multiple Carets
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+L``
     - Put a caret at the end of every selected line
   * - ``Ctrl+Alt+N``
     - Add a caret at the next occurrence
   * - ``Ctrl+Alt+Shift+Up`` / ``Ctrl+Alt+Shift+Down``
     - Add a caret above / below
   * - ``Ctrl+Shift+Esc``
     - Back to a single caret

Arrow keys, ``Home`` and ``End`` move every caret together, and ``Shift`` with any
of them extends a selection at each one.

Folding and Bookmarks
----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+[``
     - Toggle the fold at the caret
   * - ``Ctrl+Alt+[`` / ``Ctrl+Alt+]``
     - Fold / unfold everything
   * - ``Ctrl+Alt+K``
     - Toggle a bookmark
   * - ``Ctrl+Alt+L`` / ``Ctrl+Alt+J``
     - Next / previous bookmark

Git
----

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``F7`` / ``Shift+F7``
     - Next / previous change
   * - ``Ctrl+Alt+Z``
     - Revert the change under the caret
   * - ``Ctrl+Alt+B``
     - Toggle inline blame

Code Execution and Debugging
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``F5``
     - Run the current Python file
   * - ``F9``
     - Debug the current Python file
   * - ``Shift+F5``
     - Stop all running processes
   * - ``Ctrl+F9``
     - Toggle a breakpoint
   * - ``Ctrl+F5``
     - Continue
   * - ``F10`` / ``F11`` / ``Shift+F11``
     - Step over / into / out

Code Quality
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+Y``
     - Format Python code with YAPF
   * - ``Ctrl+Alt+P``
     - Check PEP 8 compliance
   * - ``Ctrl+J``
     - Reformat / validate JSON

Macros and View
----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+R``
     - Start / stop recording a macro
   * - ``Ctrl+Shift+G``
     - Play the macro back
   * - ``Ctrl+Alt+\``
     - Toggle the split view
   * - ``Ctrl+Alt+M``
     - Toggle the minimap
   * - ``Alt+W``
     - Toggle word wrap

Python Environment
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+Shift+P``
     - Install a package with pip
   * - ``Ctrl+Shift+U``
     - Upgrade and install packages
   * - ``Ctrl+Shift+V``
     - Change the Python interpreter

Console
--------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Up``
     - Previous command in history
   * - ``Down``
     - Next command in history

Fixed Keys
-----------

These are handled by the editing area itself rather than by a command, so they do not
appear in the shortcut settings and cannot be reassigned:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+D``
     - Duplicate the line or selection
   * - ``Ctrl+/``
     - Toggle comment
   * - ``Alt+Up`` / ``Alt+Down``
     - Move the line up / down
   * - ``Ctrl+B``
     - Jump to the definition under the caret
   * - ``Ctrl+Shift+\``
     - Jump to the matching bracket
   * - ``Ctrl++`` / ``Ctrl+-``
     - Zoom the editor font in / out
   * - ``Tab`` / ``Shift+Tab``
     - Indent / unindent the line or selection

Typing ``(``, ``[``, ``{``, ``"`` or ``'`` with text selected surrounds the selection
with that pair instead of replacing it.
