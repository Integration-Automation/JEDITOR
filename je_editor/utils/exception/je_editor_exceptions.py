import sys


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
