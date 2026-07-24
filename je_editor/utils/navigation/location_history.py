"""
游標跳轉歷史（純邏輯，不含 Qt）
Cursor jump history (pure logic, no Qt imports).

行為與瀏覽器的上一頁/下一頁一致：在歷史中間造訪新位置時，會捨棄後方的
「前進」紀錄。
Behaves like a browser's back/forward: visiting a new location while in the middle
of the history discards the forward entries.
"""
from __future__ import annotations

# 歷史紀錄的預設上限，避免長時間使用後無限增長
# Default cap so the history cannot grow without bound over a long session
DEFAULT_MAX_SIZE = 50


class LocationHistory:
    """
    以行號表示的游標跳轉歷史
    A cursor jump history expressed as line numbers.

    :param max_size: 保留的最大紀錄數 / The maximum number of entries kept
    """

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        self._max_size = max(1, max_size)
        self._entries: list[int] = []
        self._index = -1

    @property
    def entries(self) -> list[int]:
        """目前的歷史紀錄（唯讀複本）/ The current history entries (read-only copy)."""
        return list(self._entries)

    @property
    def index(self) -> int:
        """目前所在的紀錄索引，空的時候為 -1 / Current entry index, -1 when empty."""
        return self._index

    def current(self) -> int | None:
        """目前所在的位置 / The current location, or ``None`` when empty."""
        if self._index < 0:
            return None
        return self._entries[self._index]

    def visit(self, line: int) -> None:
        """
        造訪一個新位置
        Record a visit to a new location.

        與目前位置相同時會被忽略（避免連續重複）；若目前不在最尾端，會先捨棄
        後方的前進紀錄，再加入新位置。
        A visit equal to the current location is ignored (no consecutive
        duplicates); if not at the end, the forward entries are discarded first.

        :param line: 造訪的行號 / The visited line number
        """
        if self._index >= 0 and self._entries[self._index] == line:
            return
        del self._entries[self._index + 1:]
        self._entries.append(line)
        self._enforce_max_size()
        self._index = len(self._entries) - 1

    def back(self) -> int | None:
        """
        回到上一個位置
        Move to the previous location.

        :return: 上一個位置，已在最前端時回傳 ``None``
            / The previous location, or ``None`` when already at the start
        """
        if self._index <= 0:
            return None
        self._index -= 1
        return self._entries[self._index]

    def forward(self) -> int | None:
        """
        前進到下一個位置
        Move to the next location.

        :return: 下一個位置，已在最尾端時回傳 ``None``
            / The next location, or ``None`` when already at the end
        """
        if self._index < 0 or self._index >= len(self._entries) - 1:
            return None
        self._index += 1
        return self._entries[self._index]

    def can_go_back(self) -> bool:
        """是否還能回上一步 / Whether a back step is available."""
        return self._index > 0

    def can_go_forward(self) -> bool:
        """是否還能前進一步 / Whether a forward step is available."""
        return 0 <= self._index < len(self._entries) - 1

    def clear(self) -> None:
        """清除所有歷史 / Clear the whole history."""
        self._entries.clear()
        self._index = -1

    def shift_after_edit(self, changed_line: int, line_delta: int) -> None:
        """
        文字增減行後調整歷史中的行號
        Adjust stored line numbers after lines were inserted or removed.

        位於變更點之後的紀錄整體平移 ``line_delta`` 行，讓歷史繼續指向原本的程式碼。
        Entries after the change point shift by ``line_delta`` so the history keeps
        pointing at the same code.

        :param changed_line: 發生變更的行 / The line where the change happened
        :param line_delta: 行數變化量（新增為正、刪除為負）/ The change in line count
        """
        if line_delta == 0:
            return
        self._entries = [
            entry + line_delta if entry > changed_line else entry
            for entry in self._entries
        ]

    def _enforce_max_size(self) -> None:
        """超過上限時從最舊的紀錄開始丟棄 / Drop oldest entries past the cap."""
        overflow = len(self._entries) - self._max_size
        if overflow > 0:
            del self._entries[:overflow]
