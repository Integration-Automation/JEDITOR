from je_editor import start_editor
from tkinter import ttk

style = ttk.Style()
print(style.theme_names())
editor = start_editor(use_theme="clam", **{"debug": True})

