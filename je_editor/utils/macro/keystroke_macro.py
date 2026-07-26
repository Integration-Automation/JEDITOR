"""
記錄與重播一段按鍵操作
Record a run of keystrokes and play it back.

錄製時把每個按鍵存成 ``(鍵碼, 修飾鍵, 文字)``，重播時再依序送出。純資料結構，
不含 Qt，因此錄製內容可以單獨測試。
Recording stores each key as ``(key, modifiers, text)`` and playback sends them
again in order. Pure data with no Qt, so what was recorded can be tested on its
own.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 一段巨集最多記幾個按鍵，避免錄製中忘記停止而無限成長
# How many keystrokes one macro holds, so a forgotten recording cannot grow forever
MAX_KEYSTROKES = 2000


@dataclass(frozen=True)
class Keystroke:
    """
    一個被記錄下來的按鍵
    One recorded keystroke.

    :param key: Qt 的鍵碼 / Qt's key code
    :param modifiers: 修飾鍵的位元值 / the modifier flags
    :param text: 該按鍵產生的文字 / the text the key produced
    """

    key: int
    modifiers: int
    text: str


@dataclass
class KeystrokeMacro:
    """
    一段巨集的錄製狀態
    The recording state of one macro.

    :param keystrokes: 已錄下的按鍵 / the keystrokes recorded so far
    :param recording: 是否正在錄製 / whether recording is under way
    """

    keystrokes: list[Keystroke] = field(default_factory=list)
    recording: bool = False

    def start(self) -> None:
        """開始錄製，並丟掉上一段 / Start recording, discarding the previous run."""
        self.keystrokes = []
        self.recording = True

    def stop(self) -> None:
        """停止錄製 / Stop recording."""
        self.recording = False

    def toggle(self) -> bool:
        """
        切換錄製狀態
        Start recording, or stop if already going.

        :return: 切換後是否正在錄製 / whether recording is now under way
        """
        if self.recording:
            self.stop()
        else:
            self.start()
        return self.recording

    def record(self, key: int, modifiers: int, text: str) -> bool:
        """
        記下一個按鍵
        Record one keystroke.

        :param key: Qt 的鍵碼 / Qt's key code
        :param modifiers: 修飾鍵的位元值 / the modifier flags
        :param text: 該按鍵產生的文字 / the text the key produced
        :return: 有記下時為 ``True`` / ``True`` when it was recorded
        """
        if not self.recording or len(self.keystrokes) >= MAX_KEYSTROKES:
            return False
        self.keystrokes.append(Keystroke(key=key, modifiers=modifiers, text=text))
        return True

    @property
    def is_empty(self) -> bool:
        """是否還沒錄到任何按鍵 / Whether nothing has been recorded yet."""
        return not self.keystrokes
