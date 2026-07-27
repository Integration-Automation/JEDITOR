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

Press **F9** to launch the current Python file in debug mode. The debugger is
``python -m pdb``, driven from the editor rather than from a separate terminal.

**Breakpoints**

``Ctrl+F9`` toggles a breakpoint on the current line, and a red dot appears in the
gutter. Breakpoints are anchored to the text, so they follow their code when lines are
inserted or removed above them. Every breakpoint in the file is sent to pdb when the
debug run starts, and toggling one during a run takes effect immediately.

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

The same commands are on the **Run > Debug** menu, and anything pdb understands can be
typed directly into the debugger input.

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
