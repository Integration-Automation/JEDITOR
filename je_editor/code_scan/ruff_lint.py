"""
對編輯中的內容執行 ruff，取得診斷
Run ruff over the text being edited and collect its diagnostics.

檢查的是**緩衝區內容**而不是磁碟上的檔案，所以還沒存檔的修改也會被檢查；
內容經由標準輸入傳給 ruff，只用 ``--stdin-filename`` 告訴它檔名，好讓 per-file
的設定與規則照常套用。
This lints the **buffer**, not the file on disk, so unsaved edits are checked
too. The text goes in through standard input and only ``--stdin-filename`` tells
ruff what the file is called, so per-file configuration still applies.
"""
from __future__ import annotations

import shutil
import subprocess  # nosec B404 - 以引數清單呼叫 ruff，未使用 shell
import sys
from pathlib import Path

from je_editor.utils.lint.ruff_diagnostics import Diagnostic, parse_ruff_json
from je_editor.utils.logging.loggin_instance import jeditor_logger

# ruff 執行檔名稱 / The ruff executable's name
_RUFF_NAME = "ruff.exe" if sys.platform == "win32" else "ruff"
# 單次檢查的逾時（秒）：ruff 很快，超過就是出了別的問題
# Timeout for one run: ruff is fast, so exceeding this means something else is wrong
LINT_TIMEOUT_SECONDS = 20
# 可以檢查的副檔名 / Suffixes worth linting
PYTHON_SUFFIXES = (".py", ".pyi")


def find_ruff_executable() -> str | None:
    """
    找出可用的 ruff 執行檔
    Locate a usable ruff executable.

    先找目前直譯器所在的環境（通常就是專案的虛擬環境），再退回 PATH。
    The running interpreter's environment is tried first, since that is usually
    the project's virtual environment, then PATH.

    :return: 執行檔路徑，找不到時為 ``None`` / the path, or ``None`` when absent
    """
    beside_interpreter = Path(sys.executable).parent / _RUFF_NAME
    if beside_interpreter.is_file():
        return str(beside_interpreter)
    return shutil.which("ruff")


def is_lintable(file_path: str | Path | None) -> bool:
    """
    判斷這個檔案是否值得檢查
    Whether this file is worth linting.

    :param file_path: 檔案路徑 / the file to consider
    :return: 是 Python 檔時為 ``True`` / ``True`` for a Python file
    """
    if file_path is None:
        return False
    return Path(file_path).suffix.lower() in PYTHON_SUFFIXES


def lint_command(executable: str, file_path: str | Path) -> list[str]:
    """
    組出檢查用的指令
    Build the command that lints one buffer.

    :param executable: ruff 執行檔 / the ruff executable
    :param file_path: 緩衝區對應的檔名 / the name the buffer is saved under
    :return: 引數清單（不經過 shell）/ the argument list, never a shell string
    """
    return [
        executable, "check",
        "--output-format", "json",
        "--stdin-filename", str(file_path),
        "-",
    ]


def lint_text(text: str, file_path: str | Path) -> list[Diagnostic]:
    """
    檢查一段內容並回傳診斷
    Lint *text* as if it were *file_path*.

    ruff 找到問題時回傳碼是 1，那是正常結果而不是失敗，因此不特別處理回傳碼。
    ruff exits with 1 when it finds problems, which is a result rather than a
    failure, so the return code is not inspected.

    :param text: 要檢查的內容 / the text to lint
    :param file_path: 內容對應的檔名 / the name the text is saved under
    :return: 診斷清單；ruff 不存在或執行失敗時為空清單
        the diagnostics, or an empty list when ruff is missing or fails
    """
    executable = find_ruff_executable()
    if executable is None:
        return []
    try:
        completed = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
            lint_command(executable, file_path),
            input=text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=LINT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        jeditor_logger.debug(f"ruff_lint: could not run ruff: {error!r}")
        return []
    return parse_ruff_json(completed.stdout or "")
