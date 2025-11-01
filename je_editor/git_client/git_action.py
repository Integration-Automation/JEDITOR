import os
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError


# Simple audit logger
def audit_log(repo_path: str, action: str, detail: str, ok: bool, err: str = ""):
    """
    Append an audit log entry to 'audit.log' in the repo directory.
    This is useful for compliance and traceability.
    """
    try:
        path = os.path.join(repo_path if repo_path else ".", "audit.log")
        with open(path, "a", encoding="utf-8") as f:
            ts = datetime.now().isoformat(timespec="seconds")
            f.write(f"{ts}\taction={action}\tok={ok}\tdetail={detail}\terr={err}\n")
    except Exception:
        pass  # Never let audit logging failure break the UI


# Git service layer
class GitService:
    """
    Encapsulates Git operations using GitPython.
    Keeps UI logic separate from Git logic.
    """

    def __init__(self):
        self.repo: Repo | None = None
        self.repo_path: str | None = None

    def open_repo(self, path: str):
        try:
            self.repo = Repo(path)
            self.repo_path = path
            audit_log(path, "open_repo", path, True)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            audit_log(path, "open_repo", path, False, str(e))
            raise

    def list_branches(self):
        self._ensure_repo()
        branches = [head.name for head in self.repo.heads]
        audit_log(self.repo_path, "list_branches", ",".join(branches), True)
        return branches

    def current_branch(self):
        self._ensure_repo()
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "(detached HEAD)"

    def checkout(self, branch: str):
        self._ensure_repo()
        try:
            self.repo.git.checkout(branch)
            audit_log(self.repo_path, "checkout", branch, True)
        except GitCommandError as e:
            audit_log(self.repo_path, "checkout", branch, False, str(e))
            raise

    def list_commits(self, branch: str, max_count: int = 100):
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
            except Exception:
                pass
        out = "".join(text) if text else "(No patch content)"
        audit_log(self.repo_path, "show_diff", commit_sha, True)
        return out

    def stage_all(self):
        self._ensure_repo()
        try:
            self.repo.git.add(all=True)
            audit_log(self.repo_path, "stage_all", "git_client add -A", True)
        except GitCommandError as e:
            audit_log(self.repo_path, "stage_all", "git_client add -A", False, str(e))
            raise

    def commit(self, message: str):
        self._ensure_repo()
        if not message.strip():
            raise ValueError("Commit message is empty.")
        try:
            self.repo.index.commit(message)
            audit_log(self.repo_path, "commit", message, True)
        except Exception as e:
            audit_log(self.repo_path, "commit", message, False, str(e))
            raise

    def pull(self, remote: str = "origin", branch: str | None = None):
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

    def push(self, remote: str = "origin", branch: str | None = None):
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

    def remotes(self):
        self._ensure_repo()
        return [r.name for r in self.repo.remotes]

    def _ensure_repo(self):
        if self.repo is None:
            raise RuntimeError("Repository not opened.")


# Null tree constant for initial commit diff
NULL_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

# Worker thread wrapper
class GitWorker(QThread):
    """
    Runs a function in a separate thread to avoid blocking the UI.
    Emits (result, error) when done.
    """
    done = Signal(object, object)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.done.emit(res, None)
        except Exception as e:
            self.done.emit(None, e)
