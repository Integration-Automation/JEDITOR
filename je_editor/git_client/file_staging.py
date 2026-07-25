"""
把內容寫進 git 索引，並讀回已暫存的版本
Write content into the git index, and read the staged version back.

``GitService`` 只能一次暫存整個檔案；要「只暫存這一段」就得自己組出該版本的內容
再寫進索引，工作區的檔案則保持不動。
``GitService`` can only stage a whole file. Staging one hunk means assembling the
content that version would have and writing it into the index, while the file in
the working tree is left untouched.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from git import Blob, IndexEntry
from git.exc import GitError
from gitdb.base import IStream

from je_editor.git_client.file_baseline import open_repository
from je_editor.utils.logging.loggin_instance import jeditor_logger

# git 中一般檔案的模式 / The mode git uses for a normal file
_FILE_MODE = 0o100644


def _relative_to(repo, file_path: str | Path) -> str | None:
    """取得檔案相對於工作區的路徑 / The file's path relative to the working tree."""
    try:
        relative = Path(file_path).resolve().relative_to(Path(repo.working_tree_dir).resolve())
    except (ValueError, TypeError, AttributeError, OSError):
        return None
    return relative.as_posix()


def staged_text(file_path: str | Path) -> str | None:
    """
    取得檔案目前在索引中的內容
    Return the file's content as it currently stands in the index.

    :param file_path: 檔案路徑 / the file to read
    :return: 已暫存的文字；不在索引或不是文字時為 ``None``
        the staged text, or ``None`` when it is not in the index or not text
    """
    repo = open_repository(file_path)
    if repo is None:
        return None
    with repo:
        relative = _relative_to(repo, file_path)
        if relative is None:
            return None
        try:
            entry = repo.index.entries[(relative, 0)]
            blob = Blob(repo, entry.binsha, entry.mode, relative)
            text = blob.data_stream.read().decode("utf-8")
        except (KeyError, ValueError, TypeError, AttributeError, GitError, OSError):
            return None
        except UnicodeDecodeError:
            jeditor_logger.debug(f"file_staging: {file_path} is not utf-8 text")
            return None
        return text.replace("\r\n", "\n").replace("\r", "\n")


def stage_content(file_path: str | Path, content: str) -> bool:
    """
    把指定內容寫進索引，工作區的檔案不動
    Write the given content into the index, leaving the working tree alone.

    這正是「只暫存這一段」的做法：索引拿到套用了該段變更的版本，磁碟上的檔案仍是
    使用者正在編輯的樣子。
    This is how one hunk is staged: the index receives the version with that hunk
    applied while the file on disk stays as the user is editing it.

    :param file_path: 檔案路徑 / the file to stage
    :param content: 要暫存的內容 / the content to stage
    :return: 寫入成功時為 ``True`` / ``True`` when the index was updated
    """
    repo = open_repository(file_path)
    if repo is None:
        return False
    with repo:
        relative = _relative_to(repo, file_path)
        if relative is None:
            return False
        data = content.encode("utf-8")
        try:
            stream = repo.odb.store(IStream(Blob.type, len(data), BytesIO(data)))
            repo.index.add([IndexEntry.from_blob(
                Blob(repo, stream.binsha, _FILE_MODE, relative))])
            repo.index.write()
        except (ValueError, TypeError, AttributeError, GitError, OSError) as error:
            jeditor_logger.error(f"file_staging: could not stage {file_path}: {error!r}")
            return False
        return True
