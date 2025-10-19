import datetime
import traceback

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError


class GitCloneHandler:
    """
    Handles cloning of remote Git repositories with audit logging.
    負責複製遠端 Git 儲存庫，並記錄稽核日誌。
    可在 UI 或 CLI 環境中重複使用。
    """

    def __init__(self, audit_log_path: str = "git_clone_audit.log"):
        """
        Initialize the handler with an audit log file path.
        初始化處理器，指定稽核日誌檔案路徑。

        :param audit_log_path: Path to the audit log file
                               稽核日誌檔案的路徑
        """
        self.audit_log_path = audit_log_path

    def clone_repo(self, remote_url: str, local_path: str) -> str:
        """
        Clone a remote repository to a local path.
        將遠端 Git 儲存庫複製到本地路徑。

        :param remote_url: The Git repository URL (e.g., https://github.com/user/repo.git)
                           Git 儲存庫的 URL
        :param local_path: The local directory to clone into
                           要複製到的本地目錄
        :return: The path to the cloned repository
                 複製完成後的本地路徑
        :raises: RuntimeError if cloning fails
                 若複製失敗則拋出 RuntimeError
        """
        try:
            # 記錄開始複製 / Log start of cloning
            self._log_audit(f"Cloning started: {remote_url} -> {local_path}")

            # 執行 Git 複製 / Perform Git clone
            Repo.clone_from(remote_url, local_path)

            # 記錄完成複製 / Log completion
            self._log_audit(f"Cloning completed: {remote_url} -> {local_path}")
            return local_path

        except (GitCommandError, InvalidGitRepositoryError, NoSuchPathError) as e:
            # 捕捉 Git 相關錯誤 / Catch Git-related errors
            self._log_audit(
                f"ERROR: Git operation failed: {remote_url} -> {local_path}\n"
                f"{str(e)}\nTraceback:\n{traceback.format_exc()}"
            )
            raise RuntimeError(f"Git operation failed: {str(e)}") from e

        except Exception as e:
            # 捕捉其他未預期錯誤 / Catch unexpected errors
            self._log_audit(
                f"ERROR: Unexpected error during clone: {remote_url} -> {local_path}\n"
                f"{str(e)}\nTraceback:\n{traceback.format_exc()}"
            )
            raise RuntimeError(f"Unexpected error during clone: {str(e)}") from e

    def _log_audit(self, message: str):
        """
        Append an audit log entry with timestamp.
        在稽核日誌中加入帶有時間戳的紀錄。

        :param message: The message to log
                        要記錄的訊息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            # 確保日誌寫入失敗不會影響主要流程
            # Never let audit logging failure break the flow
            pass