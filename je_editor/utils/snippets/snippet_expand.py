"""
展開程式碼片段，並算出每個定位點的位置
Expand a code snippet and work out where each tab stop lands.

片段用 ``$1``、``${2:預設值}`` 標定位點，``$0`` 是展開後游標最後停留的位置——
與大多數編輯器的寫法一致，使用者既有的片段可以直接沿用。
Snippets mark their stops with ``$1``, ``${2:default}`` and ``$0`` for where the
caret ends up, the same notation most editors use, so existing snippets can be
pasted in as they are.

純邏輯：只做文字與位置計算，插入與游標移動交給編輯器。
Pure logic: it computes text and offsets only, leaving insertion and caret
movement to the editor.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 比對 $1 或 ${1:預設值} / Matches $1 or ${1:default}
_STOP_PATTERN = re.compile(r"\$(\d+)|\$\{(\d+):([^}]*)\}")
# ``$0`` 代表最後停留的位置，排序時要放到最後
# ``$0`` is where the caret finishes, so it sorts after every other stop
_FINAL_STOP = 0


@dataclass(frozen=True)
class SnippetStop:
    """
    展開後的一個定位點
    One tab stop in the expanded text.

    :param position: 相對於片段起點的字元位置 / offset from the snippet's start
    :param length: 預設值的長度（沒有預設值時為 0）/ the default value's length
    """

    position: int
    length: int


def expand_snippet(body: str) -> tuple[str, list[SnippetStop]]:
    """
    展開片段內容，回傳文字與定位點
    Expand a snippet body into text and its tab stops.

    定位點依編號排序，``$0`` 排在最後；同一個編號出現多次時只取第一次。
    Stops come back in numeric order with ``$0`` last, and a number used more
    than once keeps only its first appearance.

    :param body: 片段內容 / the snippet body
    :return: ``(展開後的文字, 定位點清單)`` / ``(expanded text, stops)``
    """
    pieces: list[str] = []
    stops: dict[int, SnippetStop] = {}
    length = 0
    last_end = 0
    for match in _STOP_PATTERN.finditer(body):
        literal = body[last_end:match.start()]
        pieces.append(literal)
        length += len(literal)
        number = int(match.group(1) or match.group(2))
        default = match.group(3) or ""
        if number not in stops:
            stops[number] = SnippetStop(position=length, length=len(default))
        pieces.append(default)
        length += len(default)
        last_end = match.end()
    pieces.append(body[last_end:])
    text = "".join(pieces)
    ordered = sorted(stops.items(), key=lambda item: (item[0] == _FINAL_STOP, item[0]))
    return text, [stop for _number, stop in ordered]


def default_snippets() -> dict[str, str]:
    """
    內建的 Python 片段
    The Python snippets that ship with the editor.

    :return: 觸發字對應片段內容 / trigger word -> snippet body
    """
    return {
        "def": "def ${1:name}(${2:args}):\n    $0",
        "class": "class ${1:Name}:\n    def __init__(self${2:, args}):\n        $0",
        "for": "for ${1:item} in ${2:iterable}:\n    $0",
        "while": "while ${1:condition}:\n    $0",
        "if": "if ${1:condition}:\n    $0",
        "try": "try:\n    ${1:pass}\nexcept ${2:Exception} as error:\n    $0",
        "with": "with ${1:expression} as ${2:name}:\n    $0",
        "main": 'if __name__ == "__main__":\n    $0',
    }


# 各語言自己的片段；沒有列到的語言只會拿到通用片段
# Per-language snippets; a language not listed here gets only the shared ones
LANGUAGE_SNIPPETS: dict[str, dict[str, str]] = {
    ".ts": {
        "fn": "function ${1:name}(${2:args}) {\n    $0\n}",
        "cls": "class ${1:Name} {\n    constructor(${2:args}) {\n        $0\n    }\n}",
        "log": "console.log($0);",
        "iff": "if (${1:condition}) {\n    $0\n}",
    },
    ".js": {
        "fn": "function ${1:name}(${2:args}) {\n    $0\n}",
        "log": "console.log($0);",
        "iff": "if (${1:condition}) {\n    $0\n}",
    },
    ".go": {
        "fn": "func ${1:name}(${2:args}) ${3:error} {\n    $0\n}",
        "iferr": "if err != nil {\n    return $0\n}",
        "forr": "for ${1:index}, ${2:value} := range ${3:items} {\n    $0\n}",
    },
    ".rs": {
        "fn": "fn ${1:name}(${2:args}) -> ${3:()} {\n    $0\n}",
        "match": "match ${1:value} {\n    ${2:pattern} => $0,\n}",
        "test": "#[test]\nfn ${1:name}() {\n    $0\n}",
    },
}


def language_snippets(suffix: str) -> dict[str, str]:
    """
    取得某個副檔名專屬的片段
    The snippets belonging to one file suffix.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 該語言的片段 / that language's snippets
    """
    return dict(LANGUAGE_SNIPPETS.get(suffix.lower(), {}))


def merge_snippets(stored: object, suffix: str = "") -> dict[str, str]:
    """
    把使用者定義的片段併入內建片段
    Merge user-defined snippets over the built-in ones.

    順序由通用到專屬：內建的 Python 片段、該語言的片段，最後才是使用者定義的，
    因此使用者永遠可以蓋掉任何一個。
    The order runs from general to specific — the built-in Python set, then the
    language's own, then the user's — so a user definition always wins.

    使用者檔案可以是 ``{觸發字: 內容}``，也可以用副檔名分組，例如
    ``{".ts": {...}}``；兩種都接受。
    A user file may be ``{trigger: body}`` or grouped by suffix such as
    ``{".ts": {...}}``, and both forms are accepted.

    設定檔可能被手動編輯，因此型別不符的項目會被略過而不是讓載入失敗。
    A hand-edited file may hold anything, so entries with the wrong type are
    skipped rather than failing the load.

    :param stored: 讀進來的使用者片段，任何型別 / the loaded user snippets, any type
    :param suffix: 目前檔案的副檔名 / the current file's suffix
    :return: 可用的片段對照表 / the usable snippets
    """
    snippets = default_snippets()
    snippets.update(language_snippets(suffix))
    if not isinstance(stored, dict):
        return snippets
    for key, value in stored.items():
        if not isinstance(key, str) or not key:
            continue
        if isinstance(value, str):
            snippets[key] = value
        elif isinstance(value, dict) and suffix and key.lower() == suffix.lower():
            # 這一組是給這個副檔名的 / This group belongs to this suffix
            snippets.update({
                trigger: body for trigger, body in value.items()
                if isinstance(trigger, str) and trigger and isinstance(body, str)
            })
    return snippets
