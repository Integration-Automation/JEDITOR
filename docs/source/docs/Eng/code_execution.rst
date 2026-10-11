Code Execution & Debugging
===========================

JEditor includes a built-in code execution engine that supports running Python scripts,
compiled languages, and arbitrary shell commands — all without leaving the editor.

Running Python Scripts
-----------------------

Press **F5** to run the current Python file. JEditor will:

1. Detect the Python interpreter (or virtual environment if present)
2. Execute the script in a background process
3. Stream real-time output to the result panel
4. Display errors in red for easy identification

**Virtual Environment Support:**

JEditor automatically detects ``venv`` directories in the project root and uses the
virtual environment's Python interpreter for execution, ensuring correct package resolution.

You can also manually select a Python interpreter from the **Python Env** menu.

Debugging
----------

Press **F9** to debug the current Python file. The program runs under ``debugpy`` through the
Debug Adapter Protocol, and the **Debug Panel** opens beside the editor. The program may use
another interpreter than the editor's (the one chosen in **Python Env**); debugpy does not have
to be installed in that environment.

**Breakpoints**

``Ctrl+F9`` toggles a breakpoint on the current line, and a red dot appears in the
gutter. Breakpoints are anchored to the text, so they follow their code when lines are
inserted or removed above them. The breakpoints of every open file are sent when the debug run
starts, and toggling one during a run takes effect immediately.

**Run > Debug > Breakpoint Condition...** gives the breakpoint on the current line a condition,
an expression such as ``count > 10``: the program stops there only when it is true. Leave it
empty to stop every time. A line without a breakpoint gets one.

**The Debug Panel**

- **Continue**, **Pause**, **Step Over**, **Step Into**, **Step Out** and **Stop**, with the
  current state beside them (``Running``, ``Paused: breakpoint``, ``Ended``).
- **Thread** lists the program's threads and **Call Stack** the frames of the chosen one,
  innermost first. Choosing a frame opens its file and marks the line it is on.
- The variables of the chosen frame, grouped as the debugger groups them (locals, globals).
  A list, dictionary or object opens to show what it holds, fetched when you open it.
- The program's output, and below it a box to evaluate an expression in the chosen frame.
- When the program stops on an uncaught exception, its type, message and traceback are shown
  in the output.

The line where the program has stopped is highlighted in the editor
(``debug_execution_line_color``). The panel can also be opened from **Dock > Debug Panel**.

**Stepping**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Ctrl+F5``
     - Continue to the next breakpoint
   * - ``F10``
     - Step over the current line
   * - ``F11``
     - Step into the call on the current line
   * - ``Shift+F11``
     - Step out of the current function

**Attaching to a running program**

Start the program so that it waits for a debugger::

   python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py

then choose **Run > Debug > Attach to Process...** and enter ``127.0.0.1:5678``. A port alone
means this machine.

**Without debugpy**

When debugpy is not installed the editor falls back to its earlier debugger, ``python -m pdb``
driven through the **Debugger** output tab: the shortcuts above send the matching pdb commands,
and anything pdb understands can be typed into **Run > Debug > Show Debugger Input**.

Variable inspection during execution is covered by the Variable Inspector below.

Stop Execution
^^^^^^^^^^^^^^^

- **Shift+F5** — Stop all running processes
- Individual processes can also be stopped from the **Run** menu

Running Other Languages
------------------------

Through the plugin system, JEditor supports running files in other languages:

**Interpreted Languages** (run directly):

- **Go** — ``go run file.go``
- **Java** — ``java file.java``

**Compiled Languages** (compile then run):

- **C** — ``gcc file.c -o file && ./file``
- **C++** — ``g++ file.cpp -o file && ./file``
- **Rust** — ``rustc file.rs -o file && ./file``

See :doc:`plugins` for details on adding run configurations for new languages.

Shell Command Execution
------------------------

JEditor provides a built-in shell for running arbitrary commands:

- Execute any shell/terminal command
- Cross-platform shell support: ``cmd``, ``PowerShell``, ``bash``, ``sh``
- Select your preferred shell from the console widget's dropdown
- Real-time output streaming with color-coded results
- Stop running shell processes at any time

Output Display
---------------

The result panel at the bottom of the editor shows execution output:

- **Normal output** — displayed in the configured normal color
- **Error output** — displayed in red for easy identification
- **System messages** — displayed in a distinct color
- Output line limit is configurable (default: 200,000 lines) to prevent memory issues
- Clear results from the **Run** menu or via the console's Clear button

Variable Inspector
-------------------

The Variable Inspector provides runtime variable debugging in a table view:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Column
     - Description
   * - Name
     - The variable name
   * - Type
     - The Python type of the variable
   * - Value
     - The current value (editable)

Features:

- Live variable inspection during script execution
- Filters out built-in variables (those starting with ``__``)
- Editable variable values with AST-based type conversion
- Dynamic namespace updates
- Sort and search capabilities
