"""
語言服務可以提供的功能
What a language service can offer.

獨立成一個模組，發問的形式與服務的介面才能都引用它而不互相匯入。
A module of its own, so that the request shape and the service interface can
both refer to it without importing each other.
"""
from __future__ import annotations

from enum import Enum


class LanguageCapability(Enum):
    """
    語言服務可以提供的功能
    What a language service can offer.
    """

    DIAGNOSTICS = "diagnostics"
    COMPLETION = "completion"
    HOVER = "hover"
    SIGNATURE_HELP = "signature_help"
    DEFINITION = "definition"
    REFERENCES = "references"
    RENAME = "rename"
    FORMATTING = "formatting"
    CODE_ACTION = "code_action"
    DOCUMENT_SYMBOLS = "document_symbols"
    SYNTAX_TREE = "syntax_tree"
