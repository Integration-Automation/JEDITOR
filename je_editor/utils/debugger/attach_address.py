"""
解析「要接上哪個程式」的位址
Parse the address of the program to attach to.

純邏輯，不含 Qt。
Pure logic, with no Qt.
"""
from __future__ import annotations

DEFAULT_HOST = "127.0.0.1"
MAX_PORT = 65535


def parse_address(text: str | None) -> tuple[str, int] | None:
    """
    把 ``host:port`` 或只有 ``port`` 的文字變成主機與連接埠
    Turn ``host:port``, or a port alone, into a host and a port.

    :param text: 使用者輸入的文字 / what the user typed
    :return: ``(主機, 連接埠)``；不是合法的位址時為 ``None``
        ``(host, port)``, or ``None`` when it is not a usable address
    """
    cleaned = (text or "").strip()
    host, separator, port_text = cleaned.rpartition(":")
    if not separator:
        host = DEFAULT_HOST
    if not host.strip() or not port_text.isascii() or not port_text.isdigit():
        return None
    port = int(port_text)
    if not 0 < port <= MAX_PORT:
        return None
    return host.strip(), port
