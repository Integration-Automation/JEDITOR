"""Tests for exception hierarchy."""
from __future__ import annotations

from je_editor.utils.exception.exceptions import (
    JEditorException,
    JEditorExecException,
    JEditorRunOnShellException,
    JEditorSaveFileException,
    JEditorOpenFileException,
    JEditorContentFileException,
    JEditorCantFindLanguageException,
    JEditorJsonException,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_jeditor_exception(self):
        for exc_cls in (
            JEditorExecException,
            JEditorRunOnShellException,
            JEditorSaveFileException,
            JEditorOpenFileException,
            JEditorContentFileException,
            JEditorCantFindLanguageException,
            JEditorJsonException,
        ):
            assert issubclass(exc_cls, JEditorException)

    def test_jeditor_exception_inherits_exception(self):
        assert issubclass(JEditorException, Exception)

    def test_can_raise_and_catch(self):
        with __import__("pytest").raises(JEditorJsonException):
            raise JEditorJsonException("test error")
