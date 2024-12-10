import shutil
from pathlib import Path

from je_editor.utils.exception.exception_tags import compiler_not_found_error
from je_editor.utils.exception.exceptions import JEditorExecException
from je_editor.utils.logging.loggin_instance import jeditor_logger


def check_and_choose_venv(venv_path: Path) -> str:
    jeditor_logger.info(f"check_venv.py check_and_choose_venv venv_path: {venv_path}")
    compiler_path = None
    if venv_path.is_dir() and venv_path.exists():
        compiler_path = shutil.which(
            cmd="python3",
            path=str(venv_path)
        )
    if compiler_path is None:
        compiler_path = shutil.which(
            cmd="python",
            path=str(venv_path)
        )
    else:
        compiler_path = shutil.which(cmd="python")
    if compiler_path is None:
        compiler_path = shutil.which(cmd="python")
    if compiler_path is None:
        raise JEditorExecException(compiler_not_found_error)
    return compiler_path
