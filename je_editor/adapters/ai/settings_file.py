"""
讀寫 AI 助理的設定檔
Read and write the AI assistant's settings file.

設定檔裡有 API 金鑰，所以這裡的日誌只記路徑，從不記內容；也因此沒有沿用共用的
JSON 寫檔函式——它會把寫入的內容整份記進日誌。
The file holds API keys, so the log lines here carry the path and never the
content. That is also why the shared JSON writer is not used: it logs everything
it writes.
"""
from __future__ import annotations

import json
from pathlib import Path

from je_editor.core.ai.ai_settings import AISettings
from je_editor.utils.exception.exceptions import JEditorJsonException, JEditorServiceException
from je_editor.utils.json.json_file import read_json
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 設定檔的位置：工作目錄下的 ``.jeditor/ai_config.json``
# Where the file lives: ``.jeditor/ai_config.json`` under the working directory
SETTINGS_DIRECTORY = ".jeditor"
SETTINGS_FILE_NAME = "ai_config.json"
_JSON_INDENT = 4


def ai_settings_path(directory: str | Path | None = None) -> Path:
    """
    取得設定檔的路徑
    The path of the settings file.

    :param directory: 放 ``.jeditor`` 的目錄，沒給時用目前工作目錄
        the directory holding ``.jeditor``, the working directory when omitted
    :return: 設定檔路徑 / the path of the settings file
    """
    base = Path(directory) if directory is not None else Path.cwd()
    return base / SETTINGS_DIRECTORY / SETTINGS_FILE_NAME


def load_ai_settings(path: str | Path | None = None) -> AISettings:
    """
    讀取設定
    Load the settings.

    檔案不存在、是空的或讀不懂時回傳空的設定：設定檔壞掉不該讓對話面板開不起來。
    A file that is missing, empty or unreadable gives empty settings: a broken
    settings file must not keep the chat panel from opening.

    :param path: 設定檔路徑，沒給時用預設位置 / the file, the default place when omitted
    :return: 設定 / the settings
    """
    target = Path(path) if path is not None else ai_settings_path()
    try:
        return AISettings.from_dict(read_json(str(target)))
    except JEditorJsonException:
        jeditor_logger.warning("AI settings at %s could not be read; starting empty", target)
        return AISettings()


def save_ai_settings(settings: AISettings, path: str | Path | None = None) -> Path:
    """
    寫入設定
    Save the settings.

    :param settings: 要寫入的設定 / the settings to save
    :param path: 設定檔路徑，沒給時用預設位置 / the file, the default place when omitted
    :return: 寫入的檔案路徑 / the file that was written
    :raises JEditorServiceException: 檔案寫不進去 / when the file cannot be written
    """
    target = Path(path) if path is not None else ai_settings_path()
    content = json.dumps(settings.to_dict(), indent=_JSON_INDENT, ensure_ascii=False)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as error:
        raise JEditorServiceException(f"The AI settings could not be saved to {target}") from error
    jeditor_logger.info("AI settings saved to %s", target)
    return target
