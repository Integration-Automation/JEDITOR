import datetime
import traceback

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError


class GitCloneHandler:
    """
    Handles cloning of remote Git repositories with audit logging.
    Can be reused in UI or CLI contexts.
    """

    def __init__(self, audit_log_path: str = "git_clone_audit.log"):
        self.audit_log_path = audit_log_path

    def clone_repo(self, remote_url: str, local_path: str) -> str:
        """
        Clone a remote repository to a local path.

        :param remote_url: The Git repository URL (e.g., https://github.com/user/repo.git)
        :param local_path: The local directory to clone into
        :return: The path to the cloned repository
        :raises: Exception if cloning fails
        """
        try:
            self._log_audit(f"Cloning started: {remote_url} -> {local_path}")
            Repo.clone_from(remote_url, local_path)
            self._log_audit(f"Cloning completed: {remote_url} -> {local_path}")
            return local_path
        except (GitCommandError, InvalidGitRepositoryError, NoSuchPathError) as e:
            self._log_audit(
                f"ERROR: Git operation failed: {remote_url} -> {local_path}\n{str(e)}\nTraceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Git operation failed: {str(e)}") from e
        except Exception as e:
            self._log_audit(
                f"ERROR: Unexpected error during clone: {remote_url} -> {local_path}\n{str(e)}\nTraceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Unexpected error during clone: {str(e)}") from e

    def _log_audit(self, message: str):
        """
        Append an audit log entry with timestamp.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            # Never let audit logging failure break the flow
            pass
