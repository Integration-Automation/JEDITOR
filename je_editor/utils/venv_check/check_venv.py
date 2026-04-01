# 匯入自訂錯誤訊息與例外類別
# Import custom error messages and exception class

import sys
import shutil
from pathlib import Path

# 匯入自訂錯誤訊息與例外類別
# Import custom error messages and exception class
from je_editor.utils.exception.exception_tags import compiler_not_found_error
from je_editor.utils.exception.exceptions import JEditorExecException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 平台常數 / Platform constants
WINDOWS_PLATFORMS = ("win32", "cygwin", "msys")


def is_windows() -> bool:
    """判斷是否為 Windows 平台 / Check if current platform is Windows"""
    return sys.platform in WINDOWS_PLATFORMS


def get_venv_path(base_path: Path | None = None) -> Path:
    """
    取得虛擬環境的 Python 執行路徑
    Get the Python executable path within a virtual environment

    :param base_path: 專案根目錄，預設為 cwd / Project root, defaults to cwd
    :return: venv 下的 Scripts 或 bin 路徑 / Scripts or bin path under venv
    """
    if base_path is None:
        base_path = Path.cwd()
    if is_windows():
        return base_path / "venv" / "Scripts"
    return base_path / "venv" / "bin"


def check_and_choose_venv(venv_path: Path) -> str:
    """
    功能說明 (Function Description):
    檢查虛擬環境 (venv) 路徑，並嘗試尋找可用的 Python 編譯器。
    Check the virtual environment (venv) path and try to find a usable Python interpreter.

    :param venv_path: 虛擬環境的路徑 / path to the virtual environment
    :return: Python 編譯器的完整路徑 / full path to the Python interpreter
    :raise JEditorExecException: 若找不到 Python 編譯器 / if no Python interpreter is found
    """

    jeditor_logger.info(f"check_venv.py check_and_choose_venv venv_path: {venv_path}")

    # 如果 venv_path 是資料夾且存在
    # If venv_path is a directory and exists
    if venv_path.is_dir() and venv_path.exists():
        # 先嘗試在該路徑下尋找 python3
        # Try to find python3 in the given path
        compiler_path = shutil.which("python3", path=str(venv_path))
        if compiler_path:
            return compiler_path

        # 如果找不到 python3，再找 python
        # If python3 not found, try python
        compiler_path = shutil.which("python", path=str(venv_path))
        if compiler_path:
            return compiler_path

    # 如果 venv_path 無效或都找不到，最後再嘗試系統預設的 python3 或 python
    # If venv_path is invalid or no interpreter found, try system default python3 or python
    compiler_path = shutil.which("python3") or shutil.which("python")

    # 如果還是找不到，拋出例外
    # If still not found, raise exception
    if compiler_path is None:
        raise JEditorExecException(compiler_not_found_error)

    return compiler_path
