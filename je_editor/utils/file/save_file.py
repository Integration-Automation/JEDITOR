import os

from PyQt5.QtWidgets import QFileDialog

cwd = os.getcwd()


def save_file():
    file = QFileDialog.getSaveFileName(None, "choose file", cwd)
    return file
