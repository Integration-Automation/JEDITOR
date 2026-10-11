"""
Debug Adapter Protocol 的訊息：怎麼組、怎麼讀
The messages of the Debug Adapter Protocol: how to build them and how to read them.

DAP 的傳輸格式跟語言伺服器協定一樣（``Content-Length`` 標頭加一段 JSON），所以
組框與拆框直接沿用 ``lsp_protocol``。不同的是訊息本身：請求、回應與事件各有
``type``，請求以 ``seq`` 編號，回應以 ``request_seq`` 對回去。
DAP is framed exactly as the language server protocol is, a ``Content-Length``
header and a JSON body, so framing reuses ``lsp_protocol``. What differs is the
message: requests, responses and events each carry a ``type``, a request is
numbered by ``seq`` and its response points back with ``request_seq``.

轉接器送來的東西一律當成不可信的輸入：欄位缺了、型別不對都以預設值帶過，不丟例外。
Whatever an adapter sends is treated as untrusted input: a missing field or a
wrong type becomes a default rather than an exception.

純邏輯，不含 Qt。
Pure logic, with no Qt.
"""
from __future__ import annotations

from je_editor.utils.lsp.lsp_protocol import MessageReader, encode_message

__all__ = [
    "MessageReader", "encode_message", "request", "message_kind", "source_breakpoints",
    "text_of", "number_of", "items_of",
]

TYPE_REQUEST = "request"
TYPE_RESPONSE = "response"
TYPE_EVENT = "event"


def request(seq: int, command: str, arguments: dict | None = None) -> dict:
    """
    組出一個請求
    Build one request.

    :param seq: 這個請求的編號 / the number of this request
    :param command: 指令名稱，例如 ``stackTrace`` / the command, such as ``stackTrace``
    :param arguments: 指令的引數 / the command's arguments
    :return: 可以交給 ``encode_message`` 的訊息 / a message ready for ``encode_message``
    """
    message: dict = {"seq": seq, "type": TYPE_REQUEST, "command": command}
    if arguments:
        message["arguments"] = arguments
    return message


def message_kind(message: object) -> str:
    """
    判斷一則訊息是請求、回應還是事件
    Tell whether a message is a request, a response or an event.

    :param message: 轉接器送來的訊息 / a message from the adapter
    :return: ``request``、``response``、``event``，看不懂時為空字串
        ``request``, ``response`` or ``event``, empty when it is none of them
    """
    kind = message.get("type") if isinstance(message, dict) else None
    return kind if kind in (TYPE_REQUEST, TYPE_RESPONSE, TYPE_EVENT) else ""


def text_of(source: object, key: str, default: str = "") -> str:
    """
    從字典取出一個字串欄位
    Read a text field out of a mapping.

    :param source: 可能是字典的東西 / something that may be a mapping
    :param key: 欄位名稱 / the field's name
    :param default: 欄位不存在或不是字串時用的值 / the value when it is absent or not text
    :return: 欄位的值 / the field's value
    """
    value = source.get(key) if isinstance(source, dict) else None
    return value if isinstance(value, str) else default


def number_of(source: object, key: str, default: int = 0) -> int:
    """
    從字典取出一個整數欄位
    Read an integer field out of a mapping.

    :param source: 可能是字典的東西 / something that may be a mapping
    :param key: 欄位名稱 / the field's name
    :param default: 欄位不存在或不是整數時用的值 / the value when it is absent or not an integer
    :return: 欄位的值 / the field's value
    """
    value = source.get(key) if isinstance(source, dict) else None
    # bool 是 int 的子類別，但 true/false 不是編號 / bool is an int, yet true and false are not numbers
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def items_of(source: object, key: str) -> list[dict]:
    """
    從字典取出一個「字典的清單」欄位
    Read a list-of-mappings field out of a mapping.

    :param source: 可能是字典的東西 / something that may be a mapping
    :param key: 欄位名稱 / the field's name
    :return: 清單裡是字典的那些項目 / the entries of the list that are mappings
    """
    value = source.get(key) if isinstance(source, dict) else None
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def source_breakpoints(lines_and_conditions: list[tuple[int, str]]) -> list[dict]:
    """
    組出 ``setBreakpoints`` 要的中斷點清單
    Build the breakpoint list ``setBreakpoints`` takes.

    :param lines_and_conditions: 每個中斷點的行號（1 起算）與條件，條件可以是空字串
        each breakpoint's 1-based line and its condition, which may be empty
    :return: DAP 的 ``SourceBreakpoint`` 清單 / DAP ``SourceBreakpoint`` entries
    """
    found = []
    for line, condition in lines_and_conditions:
        entry: dict = {"line": line}
        if condition:
            entry["condition"] = condition
        found.append(entry)
    return found
