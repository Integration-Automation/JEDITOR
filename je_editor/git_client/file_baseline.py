"""
讀取檔案在 HEAD 的內容，作為變更標記的比較基準
Read a file's committed content, to serve as the baseline for change markers.

編輯器需要知道「上次提交時這個檔案長什麼樣」才能標出改動。這裡只做讀取，
不執行任何會改動工作區的 git 指令。
The editor needs to know what a file looked like at the last commit before it
can mark what changed. This only reads; it never runs a git command that
touches the working tree.
"""
from __future__ import annotations

from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from git.exc import GitError

from je_editor.utils.logging.loggin_instance import jeditor_logger


def open_repository(file_path: str | Path) -> Repo | None:
    """
    找出包含此檔案的 git 儲存庫
    Find the git repository that contains *file_path*.

    :param file_path: 檔案路徑 / the file to locate
    :return: 儲存庫，不在儲存庫內時為 ``None`` / the repository, or ``None``
    """
    try:
        return Repo(Path(file_path).parent, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError, ValueError, OSError):
        # 不在 git 儲存庫內是常態，不是錯誤 / Not being in a repo is normal
        return None


def baseline_text(file_path: str | Path) -> str | None:
    """
    取得檔案在 HEAD 的文字內容（行尾統一為 ``\\n``）
    Return the file's content as of HEAD, with line endings normalised to ``\\n``.

    編輯器的文件一律以 ``\\n`` 表示換行，基準也統一成同樣形式，比對才不會受
    儲存庫的行尾設定（例如 Windows 的 ``core.autocrlf``）影響。
    A Qt document always uses ``\\n``, so the baseline is normalised to match and
    the comparison is unaffected by how the repository stores line endings (for
    example ``core.autocrlf`` on Windows).

    :param file_path: 檔案路徑 / the file to read
    :return: HEAD 版本的文字；不在儲存庫、尚未提交過、或不是文字檔時為 ``None``
        the committed text, or ``None`` when the file is not in a repository,
        has never been committed, or is not text
    """
    repo = open_repository(file_path)
    if repo is None:
        return None
    # 每個 Repo 都會開著常駐的 git 子程序，用完一定要關掉
    # Every Repo keeps long-lived git subprocesses open, so it must be closed
    with repo:
        try:
            relative = Path(file_path).resolve().relative_to(
                Path(repo.working_tree_dir).resolve())
            blob = repo.head.commit.tree / relative.as_posix()
            text = blob.data_stream.read().decode("utf-8")
            return text.replace("\r\n", "\n").replace("\r", "\n")
        except (KeyError, ValueError, TypeError, AttributeError, GitError, OSError):
            # 新檔案、尚無提交、或路徑不在工作區內
            # New file, no commit yet, or outside the tree
            return None
        except UnicodeDecodeError:
            jeditor_logger.debug("file_baseline: %s is not utf-8 text", file_path)
            return None
