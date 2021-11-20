import os

from je_editor.utils.text_process.program_exec.exec_text import exec_code
exec_result = exec_code(os.getcwd() + "/get_exec_test.py")
print(exec_result[0])
print(exec_result[1])
