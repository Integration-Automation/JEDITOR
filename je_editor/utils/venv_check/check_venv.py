import shutil
from pathlib import Path

from je_editor.utils.exception.exception_tags import compiler_not_found_error
from je_editor.utils.exception.exceptions import JEditorExecException


def check_and_choose_venv(venv_path: Path) -> str:
    if venv_path.is_dir() and venv_path.exists():
        compiler_path = shutil.which(
            cmd="python3",
            path=str(venv_path)
        )
    else:
        compiler_path = shutil.which(cmd="python3")
    if compiler_path is None:
        compiler_path = shutil.which(
            cmd="python",
            path=str(venv_path)
        )
    else:
        compiler_path = shutil.which(cmd="python")
    if compiler_path is None:
        raise JEditorExecException(compiler_not_found_error)
    return compiler_path
