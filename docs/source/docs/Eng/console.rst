Console & REPL
===============

JEditor provides two types of interactive consoles: a Shell Console for running system commands,
and a Jupyter/IPython Console for interactive Python sessions.

Shell Console
--------------

The built-in shell console lets you run system commands without leaving the editor.

**Features:**

- Execute any shell command directly
- **Command history** — Navigate previous commands with **Up/Down** arrow keys
- **Color-coded output:**
  - Normal output in the default color
  - Error output in red
  - System messages in a distinct color
- **Working directory** — Select and display the current working directory
- **Shell selection** — Choose from: ``auto``, ``cmd``, ``PowerShell``, ``bash``, ``sh``
- **Controls:** Run, Stop, and Clear buttons
- Output is limited to 10,000 lines to prevent memory issues
- Monospace font (Consolas or system default)

**Shell Selector:**

Use the dropdown at the top of the console widget to choose which shell to use.
The ``auto`` option selects the platform default (``cmd`` on Windows, ``bash`` on Linux/macOS).

Jupyter / IPython Console
--------------------------

JEditor includes an embedded Jupyter/IPython console powered by ``qtconsole``:

- Full in-process IPython kernel
- Rich interactive Python environment
- Tab completion and syntax highlighting
- Magic commands (``%timeit``, ``%run``, etc.)
- Qt event loop integration for seamless GUI interaction
- Proper resource cleanup when the editor closes

**Usage:**

Open the IPython console from the **Tab** or **Dock** menu. You get a fully functional
IPython session with access to all installed packages in your environment.
