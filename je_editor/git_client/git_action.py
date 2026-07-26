import os
from datetime import datetime

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from je_editor.utils.logging.loggin_instance import jeditor_logger


# Simple audit logger
def audit_log(repo_path: str, action: str, detail: str, ok: bool, err: str = "") -> None:
    """
    Append an audit log entry to 'audit.log' in the repo directory.
    This is useful for compliance and traceability.
    """
    try:
        path = os.path.join(repo_path if repo_path else ".", "audit.log")
        with open(path, "a", encoding="utf-8") as f:
            ts = datetime.now().isoformat(timespec="seconds")
            f.write(f"{ts}\taction={action}\tok={ok}\tdetail={detail}\terr={err}\n")
    except OSError as audit_err:
        # Never let audit logging failure break the UI; record at debug level
        jeditor_logger.debug(f"audit_log write failed: {audit_err}")


# Git service layer
class GitService:
    """
    Encapsulates Git operations using GitPython.
    Keeps UI logic separate from Git logic.
    """

    def __init__(self) -> None:
        self.repo: Repo | None = None
        self.repo_path: str | None = None

    def close(self) -> None:
        """
        關掉目前的儲存庫
        Close the repository currently open.

        每個開著的 ``Repo`` 都帶著常駐的 ``git cat-file`` 子程序，不關掉就會一直
        累積；開了幾十個之後，同一個程序裡連要開一條新執行緒都會變慢。
        Every open ``Repo`` carries long-lived ``git cat-file`` child processes and
        they pile up if it is never closed; after a few dozen, even starting a
        thread in the same process gets slow.
        """
        repo, self.repo = self.repo, None
        if repo is not None:
            repo.close()

    def open_repo(self, path: str) -> None:
        # 換儲存庫時先把上一個關掉，否則它的子程序會一直留著
        # Close the previous one first, or its child processes stay behind
        self.close()
        try:
            self.repo = Repo(path)
            self.repo_path = path
            audit_log(path, "open_repo", path, True)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            audit_log(path, "open_repo", path, False, str(e))
            raise

    def list_branches(self) -> list[str]:
        self._ensure_repo()
        branches = [head.name for head in self.repo.heads]
        audit_log(self.repo_path, "list_branches", ",".join(branches), True)
        return branches

    def current_branch(self) -> str:
        self._ensure_repo()
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "(detached HEAD)"

    def checkout(self, branch: str) -> None:
        self._ensure_repo()
        try:
            self.repo.git.checkout(branch)
            audit_log(self.repo_path, "checkout", branch, True)
        except GitCommandError as e:
            audit_log(self.repo_path, "checkout", branch, False, str(e))
            raise

    def list_commits(self, branch: str, max_count: int = 100) -> list[dict]:
        self._ensure_repo()
        commits = list(self.repo.iter_commits(branch, max_count=max_count))
        data = [
            {
                "hexsha": c.hexsha,
                "summary": c.summary,
                "author": c.author.name if c.author else "",
                "date": datetime.fromtimestamp(c.committed_date).isoformat(sep=" ", timespec="seconds"),
            }
            for c in commits
        ]
        audit_log(self.repo_path, "list_commits", f"{branch}:{len(data)}", True)
        return data

    def show_diff_of_commit(self, commit_sha: str) -> str:
        self._ensure_repo()
        commit = self.repo.commit(commit_sha)
        parent = commit.parents[0] if commit.parents else None
        if parent is None:
            null_tree = self.repo.tree(NULL_TREE)
            diffs = commit.diff(null_tree, create_patch=True)
        else:
            diffs = commit.diff(parent, create_patch=True)
        text = []
        for d in diffs:
            try:
                text.append(d.diff.decode("utf-8", errors="replace"))
            except (UnicodeDecodeError, AttributeError) as decode_err:
                jeditor_logger.debug(f"diff decode skipped: {decode_err}")
        out = "".join(text) if text else "(No patch content)"
        audit_log(self.repo_path, "show_diff", commit_sha, True)
        return out

    def stage_all(self) -> None:
        self._ensure_repo()
        try:
            self.repo.git.add(all=True)
            audit_log(self.repo_path, "stage_all", "git_client add -A", True)
        except GitCommandError as e:
            audit_log(self.repo_path, "stage_all", "git_client add -A", False, str(e))
            raise

    def commit(self, message: str) -> None:
        self._ensure_repo()
        if not message.strip():
            raise ValueError("Commit message is empty.")
        try:
            self.repo.index.commit(message)
            audit_log(self.repo_path, "commit", message, True)
        except Exception as e:
            audit_log(self.repo_path, "commit", message, False, str(e))
            raise

    def pull(self, remote: str = "origin", branch: str | None = None) -> str:
        self._ensure_repo()
        if branch is None:
            branch = self.current_branch()
        try:
            res = self.repo.git.pull(remote, branch)
            audit_log(self.repo_path, "pull", f"{remote}/{branch}", True)
            return res
        except GitCommandError as e:
            audit_log(self.repo_path, "pull", f"{remote}/{branch}", False, str(e))
            raise

    def push(self, remote: str = "origin", branch: str | None = None) -> str:
        self._ensure_repo()
        if branch is None:
            branch = self.current_branch()
        try:
            res = self.repo.git.push(remote, branch)
            audit_log(self.repo_path, "push", f"{remote}/{branch}", True)
            return res
        except GitCommandError as e:
            audit_log(self.repo_path, "push", f"{remote}/{branch}", False, str(e))
            raise

    def remotes(self) -> list[str]:
        self._ensure_repo()
        return [r.name for r in self.repo.remotes]

    def stash_save(self, message: str = "") -> str:
        """
        把目前的修改收進 stash
        Put the current changes away in a stash.

        要暫時放下手邊的東西去改別的地方時用這個；內容留在 stash 裡，之後可以取回。
        This is for putting work down to deal with something else; the changes
        stay in the stash and can be taken back afterwards.

        :param message: 這次 stash 的說明 / a note describing the stash
        :return: git 的輸出 / what git printed
        """
        self._ensure_repo()
        arguments = ["push"] + (["-m", message] if message.strip() else [])
        try:
            result = self.repo.git.stash(*arguments)
            audit_log(self.repo_path, "stash_save", message, True)
            return result
        except GitCommandError as error:
            audit_log(self.repo_path, "stash_save", message, False, str(error))
            raise

    def stash_list(self) -> list[str]:
        """
        列出目前收著的 stash
        The stashes currently put away.

        :return: 每個 stash 的說明 / a description of each
        """
        self._ensure_repo()
        output = self.repo.git.stash("list")
        return [line for line in output.splitlines() if line.strip()]

    def stash_pop(self, index: int = 0) -> str:
        """
        取回一個 stash，並把它從清單移除
        Take a stash back, removing it from the list.

        :param index: 要取回的 stash 編號 / which stash to take back
        :return: git 的輸出 / what git printed
        """
        self._ensure_repo()
        reference = f"stash@{{{max(0, index)}}}"
        try:
            result = self.repo.git.stash("pop", reference)
            audit_log(self.repo_path, "stash_pop", reference, True)
            return result
        except GitCommandError as error:
            audit_log(self.repo_path, "stash_pop", reference, False, str(error))
            raise

    def conflicted_files(self) -> list[str]:
        """
        列出目前處於衝突狀態的檔案
        The files currently left in conflict.

        合併或 pull 之後，這些檔案裡有需要人來決定的部分。
        After a merge or a pull, these hold the parts someone has to decide about.

        :return: 相對於儲存庫根目錄的路徑 / paths relative to the repository root
        """
        self._ensure_repo()
        # 索引裡同一個路徑有多個 stage 就代表衝突：2 是我們的版本，3 是對方的
        # A path with more than one stage in the index is in conflict: 2 is ours
        # and 3 is theirs
        return sorted({
            path for path, stage in self.repo.index.entries.keys() if stage != 0
        })

    def resolve_conflict(self, file_path: str, keep: str = "ours") -> bool:
        """
        以某一邊的內容解決一個檔案的衝突
        Resolve a file's conflict by keeping one side of it.

        :param file_path: 相對於儲存庫根目錄的路徑 / the path, relative to the root
        :param keep: ``ours`` 保留自己這邊，``theirs`` 保留對方 / which side to keep
        :return: 有解決時為 ``True`` / ``True`` when it was resolved
        """
        self._ensure_repo()
        if keep not in ("ours", "theirs"):
            return False
        # 沒有衝突的檔案也吃得下 ``checkout --ours``，但那只會把它默默加進索引——
        # 呼叫端要的是解決衝突，不是暫存一個沒事的檔案
        # ``checkout --ours`` is accepted for a file with no conflict too, but all
        # that does is quietly stage it, which is not what resolving asks for
        if file_path not in self.conflicted_files():
            return False
        try:
            self.repo.git.checkout(f"--{keep}", "--", file_path)
            self.repo.git.add(file_path)
            audit_log(self.repo_path, "resolve_conflict", f"{file_path} {keep}", True)
        except GitCommandError as error:
            audit_log(self.repo_path, "resolve_conflict", file_path, False, str(error))
            return False
        return True

    def _ensure_repo(self) -> None:
        if self.repo is None:
            raise RuntimeError("Repository not opened.")


# Null tree constant for initial commit diff
NULL_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
