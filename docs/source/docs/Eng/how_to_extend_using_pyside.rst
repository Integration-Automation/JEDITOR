Extending with PySide6
=======================

JEditor is built on PySide6 (Qt for Python), and you can extend it by adding custom
tabs or dock panels using your own Qt widgets.

Adding a Custom Tab
--------------------

Use the ``EDITOR_EXTEND_TAB`` dictionary to register your custom widget as a new tab
in the editor. The key is the tab name, and the value is the widget class (not an instance).

**Example:**

.. code-block:: python

   from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel
   from je_editor import start_editor, EDITOR_EXTEND_TAB


   class TestUI(QWidget):
       """A simple custom widget with a text input and a submit button."""

       def __init__(self):
           super().__init__()
           self.grid_layout = QGridLayout(self)
           self.grid_layout.setContentsMargins(0, 0, 0, 0)

           self.label = QLabel("")
           self.line_edit = QLineEdit()
           self.submit_button = QPushButton("Submit")
           self.submit_button.clicked.connect(self.show_input_text)

           self.grid_layout.addWidget(self.label, 0, 0)
           self.grid_layout.addWidget(self.line_edit, 1, 0)
           self.grid_layout.addWidget(self.submit_button, 2, 0)

       def show_input_text(self):
           self.label.setText(self.line_edit.text())


   # Register the custom tab: {"tab_name": WidgetClass}
   EDITOR_EXTEND_TAB.update({"test": TestUI})

   # Start the editor with the custom tab
   start_editor()

After running this script, JEditor will include a "test" tab alongside the default tabs.

How It Works
^^^^^^^^^^^^^

1. ``EDITOR_EXTEND_TAB`` is a dictionary that maps tab names to widget classes
2. JEditor creates an instance of each registered widget class when building the UI
3. The widget is added as a new tab in the tab bar
4. Your widget has full access to PySide6/Qt functionality

Tips
^^^^^

- Your widget class must inherit from ``QWidget`` (or a subclass)
- Use layouts (``QGridLayout``, ``QVBoxLayout``, etc.) for responsive design
- You can access JEditor's internal components through the public API
- Multiple custom tabs can be registered by calling ``update()`` multiple times or
  passing a dictionary with multiple entries

Using JEditor Components
--------------------------

You can also use JEditor's individual components in your own PySide6 applications:

.. code-block:: python

   from je_editor import EditorWidget, MainBrowserWidget, FullEditorWidget

- ``EditorWidget`` — A standalone code editor widget
- ``FullEditorWidget`` — A complete editor with line numbers and output panel
- ``MainBrowserWidget`` — A standalone web browser widget

These widgets can be added to any PySide6 layout, making it easy to integrate
code editing or browsing capabilities into your own applications.
