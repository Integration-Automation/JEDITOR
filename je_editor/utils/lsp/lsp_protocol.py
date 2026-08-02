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
from urllib.parse import unquote

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
            except ValueError:  # UnicodeDecodeError 也是 ValueError / it subclasses ValueError
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


def path_from_uri(uri: object) -> str:
    """
    把 LSP 的 ``file://`` URI 轉回檔案路徑
    Turn an LSP ``file://`` URI back into a file path.

    :param uri: 伺服器回報的 URI / the URI the server reported
    :return: 檔案路徑，無法辨識時為空字串 / the path, or an empty string
    """
    if not isinstance(uri, str) or not uri.startswith("file://"):
        return ""
    path = unquote(uri[len("file://"):])
    # Windows 的 URI 會多一個開頭斜線：``/D:/x`` 要還原成 ``D:/x``
    # A Windows URI carries a leading slash: ``/D:/x`` becomes ``D:/x``
    if len(path) > 2 and path[0] == "/" and path[2] == ":":
        return path[1:]
    return path


def definition_location(result: object) -> dict | None:
    """
    從 definition 回應取出第一個位置
    Take the first location out of a definition response.

    回應可能是單一位置、位置清單，或 ``LocationLink`` 清單，三種都要接受。
    A response may be a single location, a list of them, or a list of
    ``LocationLink``, and all three are accepted.

    :param result: 伺服器的回應內容 / the server's result
    :return: ``{"path", "line", "column"}``，無法辨識時為 ``None``
        the location, or ``None`` when it cannot be read
    """
    if isinstance(result, list):
        first = result[0] if result else None
    else:
        first = result
    if not isinstance(first, dict):
        return None
    uri = first.get("uri") or first.get("targetUri")
    span = first.get("range") or first.get("targetSelectionRange") or first.get("targetRange")
    path = path_from_uri(uri)
    if not path or not isinstance(span, dict):
        return None
    line, column = _position(span.get("start"))
    return {"path": path, "line": line, "column": column}


def hover_text(result: object) -> str:
    """
    從 hover 回應取出說明文字
    Take the description out of a hover response.

    ``contents`` 可能是字串、``{"value": ...}``，或兩者混合的清單，全部都要接受。
    ``contents`` may be a string, a ``{"value": ...}`` object, or a list mixing
    both, and all of those are accepted.

    :param result: 伺服器的回應內容 / the server's result
    :return: 說明文字，沒有內容時為空字串 / the text, or an empty string
    """
    if not isinstance(result, dict):
        return ""
    contents = result.get("contents")
    parts = contents if isinstance(contents, list) else [contents]
    texts: list[str] = []
    for part in parts:
        if isinstance(part, str) and part.strip():
            texts.append(part.strip())
        elif isinstance(part, dict):
            value = part.get("value")
            if isinstance(value, str) and value.strip():
                texts.append(value.strip())
    return "\n".join(texts)


def signature_text(result: object) -> str:
    """
    從 signature help 回應取出目前這個簽章
    Take the signature currently in play out of a signature help response.

    只取伺服器指的那一個：一個函式可能有好幾個多載，全部列出來反而看不出正在打的
    是哪一個。
    Only the one the server points at is taken: a function may have several
    overloads, and listing them all hides the one being typed.

    :param result: 伺服器的回應內容 / the server's result
    :return: 簽章文字，沒有內容時為空字串 / the signature, or an empty string
    """
    if not isinstance(result, dict):
        return ""
    signatures = result.get("signatures")
    if not isinstance(signatures, list) or not signatures:
        return ""
    index = result.get("activeSignature")
    if not isinstance(index, int) or not 0 <= index < len(signatures):
        index = 0
    active = signatures[index]
    if not isinstance(active, dict):
        return ""
    label = active.get("label")
    documentation = active.get("documentation")
    if isinstance(documentation, dict):
        documentation = documentation.get("value")
    parts = [str(part).strip() for part in (label, documentation) if isinstance(part, str)]
    return "\n".join(part for part in parts if part)


def reference_locations(result: object) -> list[dict]:
    """
    從 references 回應取出所有位置
    Take every location out of a references response.

    行列與 :func:`definition_location` 一樣轉成 1 起算，跳轉才不必再換算一次。
    Lines and columns come back 1-based, as :func:`definition_location` gives
    them, so a jump does not have to convert again.

    :param result: 伺服器的回應內容 / the server's result
    :return: ``{"path", "line", "column"}`` 的清單 / the locations
    """
    if not isinstance(result, list):
        return []
    locations = []
    for item in result:
        location = definition_location(item)
        if location is not None:
            locations.append(location)
    return locations


def code_action_titles(result: object) -> list[dict]:
    """
    從 code action 回應取出可以套用的動作
    Take the applicable actions out of a code action response.

    只保留帶著編輯內容的動作。純指令型的動作要再跟伺服器往返一次才知道要改什麼，
    列出來卻按不動比不列還糟。
    Only actions carrying edits are kept: a command-only action needs another
    round trip before anything can be changed, and listing one that does nothing
    when pressed is worse than not listing it.

    :param result: 伺服器的回應內容 / the server's result
    :return: ``{"title", "edits"}`` 的清單 / the actions
    """
    if not isinstance(result, list):
        return []
    actions = []
    for item in result:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        edits = text_edits(item.get("edit"))
        if isinstance(title, str) and title.strip() and edits:
            actions.append({"title": title.strip(), "edits": edits})
    return actions


def document_symbols(result: object) -> list[dict]:
    """
    從 document symbol 回應取出符號，巢狀的一併攤平
    Take the symbols out of a document symbol response, nesting included.

    回應可能是 ``DocumentSymbol``（有 ``children``）或 ``SymbolInformation``
    （帶 ``location``），兩種格式都要接受。
    A response may be ``DocumentSymbol`` with ``children`` or
    ``SymbolInformation`` with a ``location``, and both are accepted.

    行號轉成 1 起算，與其他位置一致。
    Lines come back 1-based, as every other position here does.

    :param result: 伺服器的回應內容 / the server's result
    :return: ``{"name", "kind", "line", "depth"}`` 的清單 / the symbols
    """
    return _flatten_symbols(result, depth=0)


def _symbol_entry(item: object, depth: int) -> dict | None:
    """把一筆符號轉成大綱用的形式，無法辨識時回傳 ``None`` / Convert one symbol."""
    if not isinstance(item, dict):
        return None
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    span = item.get("selectionRange") or item.get("range")
    if span is None:
        span = (item.get("location") or {}).get("range")
    line, _column = _position(span.get("start") if isinstance(span, dict) else None)
    kind = item.get("kind")
    return {
        "name": name.strip(),
        "kind": kind if isinstance(kind, int) else 0,
        "line": line,
        "depth": depth,
    }


def _flatten_symbols(result: object, depth: int) -> list[dict]:
    """把符號樹攤成一層，並記下每個符號的深度 / Flatten the symbol tree, noting each depth."""
    if not isinstance(result, list):
        return []
    symbols: list[dict] = []
    for item in result:
        entry = _symbol_entry(item, depth)
        if entry is None:
            continue
        symbols.append(entry)
        symbols.extend(_flatten_symbols(item.get("children"), depth + 1))
    return symbols


def text_edits(result: object, file_uri_text: str = "") -> list[dict]:
    """
    從 rename 或 formatting 回應取出要套用的編輯
    Take the edits to apply out of a rename or formatting response.

    格式化回傳的是編輯清單；重新命名回傳的是 ``WorkspaceEdit``，其中的 ``changes``
    以 URI 分組。只取目前這個檔案的編輯，跨檔案的重新命名不在這裡處理。
    Formatting returns a list of edits, while a rename returns a
    ``WorkspaceEdit`` whose ``changes`` are grouped by URI. Only the edits for
    this file are taken; a rename spanning several files is not handled here.

    :param result: 伺服器的回應內容 / the server's result
    :param file_uri_text: 目前檔案的 URI / this file's URI
    :return: 每筆編輯的範圍與新文字 / each edit's range and replacement text
    """
    raw = result
    if isinstance(result, dict):
        changes = result.get("changes")
        if isinstance(changes, dict):
            raw = changes.get(file_uri_text) or next(iter(changes.values()), [])
        else:
            raw = result.get("documentChanges") or []
            if raw and isinstance(raw[0], dict):
                raw = raw[0].get("edits", [])
    if not isinstance(raw, list):
        return []
    edits: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        span = item.get("range")
        new_text = item.get("newText")
        if not isinstance(span, dict) or not isinstance(new_text, str):
            continue
        start_line, start_column = _position(span.get("start"))
        end_line, end_column = _position(span.get("end"), start_line - 1, start_column - 1)
        edits.append({
            "start_line": start_line, "start_column": start_column,
            "end_line": end_line, "end_column": end_column,
            "new_text": new_text,
        })
    return edits


def diagnostic_entries(params: object) -> list[dict]:
    """
    從 publishDiagnostics 通知取出診斷
    Take the diagnostics out of a ``publishDiagnostics`` notification.

    :param params: 通知的參數 / the notification's parameters
    :return: 每筆診斷的位置、代碼與訊息 / each diagnostic's range, code and message
    """
    if not isinstance(params, dict):
        return []
    raw = params.get("diagnostics")
    if not isinstance(raw, list):
        return []
    entries: list[dict] = []
    for item in raw:
        entry = _diagnostic_entry(item)
        if entry is not None:
            entries.append(entry)
    return entries


def _position(raw: object, fallback_line: int = 0, fallback_column: int = 0) -> tuple[int, int]:
    """讀出 LSP 位置並轉成 1 起算 / Read an LSP position, converted to 1-based."""
    if not isinstance(raw, dict):
        return fallback_line + 1, fallback_column + 1
    line = raw.get("line")
    column = raw.get("character")
    return (
        (line if isinstance(line, int) and line >= 0 else fallback_line) + 1,
        (column if isinstance(column, int) and column >= 0 else fallback_column) + 1,
    )


def _diagnostic_entry(item: object) -> dict | None:
    """把一筆 LSP 診斷轉成編輯器用的形式 / Convert one LSP diagnostic for the editor."""
    if not isinstance(item, dict):
        return None
    message = item.get("message")
    if not isinstance(message, str) or not message:
        return None
    span = item.get("range") if isinstance(item.get("range"), dict) else {}
    line, column = _position(span.get("start"))
    end_line, end_column = _position(span.get("end"), line - 1, column - 1)
    code = item.get("code")
    return {
        # LSP 的行列是 0 起算，編輯器用 1 起算
        # LSP counts lines and columns from zero; the editor counts from one
        "line": line,
        "column": column,
        "end_line": max(end_line, line),
        "end_column": end_column,
        "code": str(code) if isinstance(code, (str, int)) else "",
        "message": message,
    }
