"""
Language Server Protocol 的訊息編解碼
Encode and decode Language Server Protocol messages.

LSP 走 JSON-RPC，每則訊息前面有 ``Content-Length`` 標頭；從管線讀到的資料可能
切在任意位置，因此讀取端要能把不完整的訊息留著等下一批資料。
LSP speaks JSON-RPC with a ``Content-Length`` header before each message. Data
arrives from a pipe split at arbitrary points, so the reader has to hold an
incomplete message until the rest turns up.

純邏輯：不啟動任何程序，因此可以直接餵位元組測試。
Pure logic: it starts no process, so it can be tested by feeding it bytes.
"""
from __future__ import annotations

import json

# 標頭與內容之間的分隔 / What separates the header from the body
HEADER_SEPARATOR = b"\r\n\r\n"
# 內容長度標頭 / The content-length header
CONTENT_LENGTH_HEADER = b"Content-Length:"


def encode_message(payload: dict) -> bytes:
    """
    把一則訊息編碼成 LSP 的傳輸格式
    Encode one message in the framing LSP uses on the wire.

    :param payload: JSON-RPC 訊息內容 / the JSON-RPC message
    :return: 可直接寫入管線的位元組 / bytes ready to write to the pipe
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _content_length(header: bytes) -> int | None:
    """讀出標頭中的內容長度 / Read the content length out of a header block."""
    for line in header.split(b"\r\n"):
        if line.lower().startswith(CONTENT_LENGTH_HEADER.lower()):
            try:
                return int(line.split(b":", 1)[1].strip())
            except ValueError:
                return None
    return None


class MessageReader:
    """
    把陸續讀到的位元組組回一則則訊息
    Reassemble whole messages from bytes as they arrive.
    """

    def __init__(self) -> None:
        self._buffer = b""

    def feed(self, data: bytes) -> list[dict]:
        """
        餵入剛讀到的資料，取出其中完整的訊息
        Feed in what was just read and take out every complete message.

        內容長度不合理或內容不是 JSON 時，該則訊息會被丟掉而不是拋出例外——
        伺服器輸出異常不該讓編輯器停擺。
        A nonsensical length or a body that is not JSON drops that message rather
        than raising: a misbehaving server must not stall the editor.

        :param data: 剛讀到的位元組 / the bytes just read
        :return: 這次能組出的完整訊息 / the messages that are now complete
        """
        self._buffer += data
        messages: list[dict] = []
        while True:
            separator = self._buffer.find(HEADER_SEPARATOR)
            if separator < 0:
                break
            header = self._buffer[:separator]
            length = _content_length(header)
            body_start = separator + len(HEADER_SEPARATOR)
            if length is None:
                # 標頭讀不出長度：丟掉這段標頭，繼續找下一則
                # No usable length: drop this header and look for the next message
                self._buffer = self._buffer[body_start:]
                continue
            if len(self._buffer) < body_start + length:
                break  # 內容還沒到齊 / the body has not all arrived yet
            body = self._buffer[body_start:body_start + length]
            self._buffer = self._buffer[body_start + length:]
            try:
                messages.append(json.loads(body.decode("utf-8")))
            except (ValueError, UnicodeDecodeError):
                continue
        return messages

    @property
    def pending_bytes(self) -> int:
        """還沒組成訊息的位元組數 / How many bytes are still waiting."""
        return len(self._buffer)


def request(request_id: int, method: str, params: dict | None = None) -> dict:
    """
    組出一則 JSON-RPC 請求
    Build a JSON-RPC request.

    :param request_id: 請求編號 / the request's id
    :param method: 方法名稱 / the method to call
    :param params: 參數 / the parameters
    :return: 請求訊息 / the request message
    """
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}


def notification(method: str, params: dict | None = None) -> dict:
    """
    組出一則 JSON-RPC 通知（不需要回應）
    Build a JSON-RPC notification, which expects no reply.

    :param method: 方法名稱 / the method to call
    :param params: 參數 / the parameters
    :return: 通知訊息 / the notification message
    """
    return {"jsonrpc": "2.0", "method": method, "params": params or {}}


def file_uri(path: str) -> str:
    """
    把檔案路徑轉成 LSP 使用的 URI
    Turn a file path into the URI form LSP uses.

    :param path: 檔案路徑 / the file path
    :return: ``file://`` 開頭的 URI / a ``file://`` URI
    """
    normalised = str(path).replace("\\", "/")
    if normalised.startswith("/"):
        return f"file://{normalised}"
    return f"file:///{normalised}"


def completion_labels(response: object) -> list[str]:
    """
    從 completion 回應取出候選字
    Take the candidate words out of a completion response.

    回應可能是清單，也可能是 ``{"items": [...]}``，兩種形式都要接受。
    A response may be a plain list or ``{"items": [...]}``, and both are accepted.

    :param response: 伺服器的回應內容 / the server's result
    :return: 候選字，去重且保留順序 / the candidates, unique and in order
    """
    items = response.get("items") if isinstance(response, dict) else response
    if not isinstance(items, list):
        return []
    labels: list[str] = []
    for item in items:
        label = item.get("label") if isinstance(item, dict) else item
        if isinstance(label, str) and label and label not in labels:
            labels.append(label)
    return labels


def diagnostic_entries(params: object) -> list[dict]:
    """
    從 publishDiagnostics 通知取出診斷
    Take the diagnostics out of a ``publishDiagnostics`` notification.

    :param params: 通知的參數 / the notification's parameters
    :return: 每筆診斷的 ``行、欄、訊息`` / each diagnostic's line, column and message
    """
    if not isinstance(params, dict):
        return []
    raw = params.get("diagnostics")
    if not isinstance(raw, list):
        return []
    entries: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        start = (item.get("range") or {}).get("start") or {}
        message = item.get("message")
        if not isinstance(message, str):
            continue
        entries.append({
            # LSP 的行列是 0 起算，編輯器用 1 起算
            # LSP counts lines and columns from zero; the editor counts from one
            "line": int(start.get("line", 0)) + 1,
            "column": int(start.get("character", 0)) + 1,
            "message": message,
        })
    return entries
