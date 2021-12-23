import os
import sys

from je_editor import exec_code
from je_editor import JEditorExecException

exec_result = exec_code(os.getcwd() + "/get_exec_test.py")
print(exec_result[0])
print(exec_result[1], file=sys.stderr)

try:
    exec_result = exec_code("wrong path test !>@j@LKJ!LKJLKJ@!LKJL:HJH@:JH:!J@HD!")
except JEditorExecException as error:
    print(repr(error), file=sys.stderr)
