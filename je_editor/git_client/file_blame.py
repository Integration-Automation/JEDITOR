"""
取得檔案每一行最後修改的提交
Find the commit that last touched each line of a file.

用於在編輯器行尾顯示「這行是誰、哪個提交改的」。只讀取，不改動工作區。
Used to show who last changed a line, and in which commit, at the end of that
line in the editor. Read-only; the working tree is never touched.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from git.exc import GitError

from je_editor.git_client.file_baseline import open_repository
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 顯示用的提交編號長度 / How much of the commit hash to show
SHORT_HASH_LENGTH = 8
# 摘要過長時截斷的長度 / Where an over-long summary is cut
MAX_SUMMARY_LENGTH = 60


@dataclass(frozen=True)
class BlameLine:
    """
    一行的提交資訊
    The commit information for one line.

    :param commit: 提交編號（已截短）/ the shortened commit hash
    :param author: 作者名稱 / the author's name
    :param summary: 提交訊息第一行 / the first line of the commit message
    """

    commit: str
    author: str
    summary: str

    @property
    def annotation(self) -> str:
        """行尾顯示的一行文字 / The single line shown at the end of the code line."""
        return f"{self.commit}  {self.author}  {self.summary}"


def _short_summary(message: object) -> str:
    """取提交訊息的第一行並截斷 / Take the first line of a commit message, shortened."""
    text = str(message or "").strip().splitlines()
    if not text:
        return ""
    first = text[0]
    return first if len(first) <= MAX_SUMMARY_LENGTH else f"{first[:MAX_SUMMARY_LENGTH]}…"


def blame_lines(file_path: str | Path) -> dict[int, BlameLine]:
    """
    取得檔案每一行的提交資訊
    Return the commit information for each line of a file.

    :param file_path: 檔案路徑 / the file to annotate
    :return: 以 0 起算的行號對應提交資訊；無法取得時為空字典
        0-based line number -> its commit, or an empty mapping when unavailable
    """
    repo = open_repository(file_path)
    if repo is None:
        return {}
    # 每個 Repo 都會開著常駐的 git 子程序，用完一定要關掉
    # Every Repo keeps long-lived git subprocesses open, so it must be closed
    with repo:
        try:
            relative = Path(file_path).resolve().relative_to(
                Path(repo.working_tree_dir).resolve())
            entries = repo.blame("HEAD", relative.as_posix())
        except (KeyError, ValueError, TypeError, AttributeError, GitError, OSError) as error:
            # 未提交過、不在工作區內、或沒有 HEAD
            # Never committed, outside the tree, or no HEAD
            jeditor_logger.debug(f"file_blame: no blame for {file_path}: {error!r}")
            return {}
        # 提交資料在 Repo 關閉前就要讀完，關閉之後就取不到了
        # The commit data is read before the Repo closes; afterwards it is gone
        return _annotations_from(entries)


def _annotations_from(entries: object) -> dict[int, BlameLine]:
    """把 GitPython 的 blame 結果轉成逐行標註 / Turn a blame result into per-line notes."""
    annotations: dict[int, BlameLine] = {}
    line_number = 0
    for entry in entries or []:
        commit, lines = entry[0], entry[1]
        blame = BlameLine(
            commit=str(commit.hexsha)[:SHORT_HASH_LENGTH],
            author=str(getattr(commit.author, "name", "")),
            summary=_short_summary(getattr(commit, "summary", "")),
        )
        for _line in lines or []:
            annotations[line_number] = blame
            line_number += 1
    return annotations
