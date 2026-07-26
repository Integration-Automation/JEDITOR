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
        except UnicodeDecodeError:
            # 必須排在 ValueError 之前，否則永遠輪不到它
            # Must come before ValueError, which is its base class
            jeditor_logger.debug(f"file_staging: {file_path} is not utf-8 text")
            return None
        except (KeyError, ValueError, TypeError, AttributeError, GitError, OSError):
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


def unstage_file(file_path: str | Path) -> bool:
    """
    把一個檔案的暫存內容還原成 HEAD 的版本
    Put a file's staged content back to the way HEAD has it.

    這是「取消暫存」：索引回到已提交的內容，工作區的檔案完全不動，因此使用者正在
    編輯的東西不會受影響。暫存了不該暫存的一段之後，這是唯一能收回的方法。
    This is unstaging: the index goes back to the committed content while the file
    on disk is left exactly as it is, so nothing the user is editing is touched.
    After staging a hunk that should not have been staged, this is the only way
    back.

    尚未提交過的新檔案沒有 HEAD 版本可回去，改為從索引移除。
    A new file has no committed version to return to, so it is removed from the
    index instead.

    :param file_path: 檔案路徑 / the file to unstage
    :return: 索引有變時為 ``True`` / ``True`` when the index changed
    """
    repo = open_repository(file_path)
    if repo is None:
        return False
    with repo:
        relative = _relative_to(repo, file_path)
        if relative is None:
            return False
        try:
            blob = repo.head.commit.tree / relative
        except (KeyError, ValueError, TypeError, AttributeError, GitError):
            return _remove_from_index(repo, relative, file_path)
        try:
            repo.index.add([IndexEntry.from_blob(
                Blob(repo, blob.binsha, _FILE_MODE, relative))])
            repo.index.write()
        except (ValueError, TypeError, AttributeError, GitError, OSError) as error:
            jeditor_logger.error(f"file_staging: could not unstage {file_path}: {error!r}")
            return False
        return True


def commit_index(file_path: str | Path, message: str) -> bool:
    """
    把索引目前的內容提交出去
    Commit whatever the index currently holds.

    提交的是索引而不是磁碟上的檔案，因此逐段暫存之後可以只提交挑好的那幾段，還沒
    暫存的修改留在工作區。
    What is committed is the index rather than the files on disk, so after staging
    hunk by hunk only the chosen parts go in and the rest stays in the working
    tree.

    :param file_path: 儲存庫中的任一個檔案 / any file in the repository
    :param message: 提交訊息 / the commit message
    :return: 有提交時為 ``True`` / ``True`` when a commit was made
    """
    if not message.strip():
        return False
    repo = open_repository(file_path)
    if repo is None:
        return False
    with repo:
        try:
            repo.index.commit(message.strip())
        except (ValueError, TypeError, AttributeError, GitError, OSError) as error:
            jeditor_logger.error(f"file_staging: could not commit: {error!r}")
            return False
        return True


def _remove_from_index(repo, relative: str, file_path: str | Path) -> bool:
    """把一個還沒提交過的檔案從索引移除 / Drop a never-committed file from the index."""
    try:
        if (relative, 0) not in repo.index.entries:
            return False
        repo.index.remove([relative])
        repo.index.write()
    except (KeyError, ValueError, TypeError, AttributeError, GitError, OSError) as error:
        jeditor_logger.error(f"file_staging: could not unstage {file_path}: {error!r}")
        return False
    return True
