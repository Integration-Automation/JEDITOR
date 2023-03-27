from tkinter import ttk

from je_editor import start_editor

style = ttk.Style()
print(style.theme_names())
editor = start_editor(use_theme="clam", **{"debug": True})
