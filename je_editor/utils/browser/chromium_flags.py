"""
壓下內嵌瀏覽器的啟動雜訊
Quiet the embedded browser's startup noise.

QtWebEngine 裡包著一整個 Chromium，它會把自己的訊息寫到標準錯誤，例如探測硬體
視訊編碼器失敗的 ``mf_video_encoder_util.cc: Set output type failed``。那些訊息
對編輯器的使用者沒有意義——Chromium 自己會退回可用的路徑——但這個編輯器把標準
錯誤導進輸出面板，於是它們就出現在使用者眼前。
QtWebEngine embeds a whole Chromium, which writes its own messages to standard
error -- such as ``mf_video_encoder_util.cc: Set output type failed`` when it
probes a hardware video encoder that will not take the settings. None of that
means anything to someone using a text editor, since Chromium falls back on its
own, but this editor pipes standard error into its output pane, so it lands in
front of the user.

純邏輯：只組出環境變數的值，不啟動任何東西。
Pure logic: it only assembles an environment variable, starting nothing.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

# Chromium 讀取旗標的環境變數 / The variable Chromium reads its flags from
FLAGS_VARIABLE = "QTWEBENGINE_CHROMIUM_FLAGS"
# 只保留致命錯誤：0=INFO、1=WARNING、2=ERROR、3=FATAL
# Keep fatal messages only: 0=INFO, 1=WARNING, 2=ERROR, 3=FATAL
QUIET_FLAG = "--log-level=3"


def flags_with_quiet_logging(existing: Optional[str]) -> str:
    """
    把「安靜」旗標加進既有的旗標字串
    Add the quiet flag to whatever flags are already set.

    使用者自己設過 log level 就不動它：他顯然是想看那些訊息。
    A log level the user set is left alone: they evidently want to see them.

    :param existing: 目前的旗標字串 / the flags as they stand
    :return: 加上之後的旗標字串 / the flags afterwards
    """
    current = (existing or "").strip()
    if "--log-level" in current:
        return current
    return f"{current} {QUIET_FLAG}".strip()


def quiet_chromium_logging(environment: Optional[Dict[str, str]] = None) -> str:
    """
    設定環境變數，讓內嵌的 Chromium 少說話
    Set the environment variable that keeps the embedded Chromium quiet.

    必須在 QtWebEngine 初始化之前呼叫，也就是第一個瀏覽器分頁被建立之前。
    This has to run before QtWebEngine initialises, which is before the first
    browser tab is created.

    :param environment: 要設定的環境，省略時用行程本身的
        / the environment to set, or the process's own when omitted
    :return: 設定後的旗標字串 / the flags as they now stand
    """
    target = os.environ if environment is None else environment
    flags = flags_with_quiet_logging(target.get(FLAGS_VARIABLE))
    target[FLAGS_VARIABLE] = flags
    return flags
