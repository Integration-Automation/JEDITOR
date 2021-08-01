import os

from PyQt5.QtWidgets import QFileDialog

cwd = os.getcwd()


def open_file():
    file = QFileDialog.getOpenFileName(None, "choose file", cwd)
    return file
