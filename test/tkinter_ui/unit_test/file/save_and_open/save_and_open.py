from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.file.save.save_file import write_file

write_file("test.py", r"""print("test_content")""")
print(read_file("test.py"))
