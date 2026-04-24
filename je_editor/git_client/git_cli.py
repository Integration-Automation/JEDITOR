import logging
import subprocess  # nosec B404 - 呼叫 git 子命令皆以引數清單送入，未使用 shell
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)


class GitCLI:
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = Path(repo_path)

    def is_git_repo(self) -> bool:
        return (self.repo_path / ".git").exists()

    def _run(self, args: List[str]) -> str:
        log.debug("git %s", " ".join(args))
        # 以固定可執行檔 "git" 與引數清單呼叫，沒有使用 shell
        # Invoked with fixed "git" binary and argument list; no shell involved
        res = subprocess.run(  # nosemgrep  # noqa: S603  # nosec B603
            ["git"] + args,
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if res.returncode != 0:
            log.error("Git failed: %s", res.stderr.strip())
            raise RuntimeError(res.stderr.strip())
        return res.stdout

    def get_all_refs(self) -> Dict[str, str]:
        # returns refname -> commit hash
        out = self._run(["show-ref", "--heads", "--tags"])
        refs = {}
        for line in out.splitlines():
            if not line.strip():
                continue
            sha, ref = line.split(" ", 1)
            refs[ref.strip()] = sha.strip()
        return refs

    def get_commits(self, max_count: int = 500) -> List[Dict]:
        """
        Return recent commits across all refs, with parents.
        """
        fmt = "%H%x01%P%x01%an%x01%ad%x01%s"
        out = self._run([
            "log", "--date=short", f"--format={fmt}", "--all",
            f"--max-count={max_count}", "--topo-order"
        ])
        commits = []
        for line in out.splitlines():
            if not line.strip():
                continue
            parts = line.split("\x01")
            if len(parts) != 5:
                continue
            sha, parents, author, date, msg = parts
            commits.append({
                "sha": sha,
                "parents": [p for p in parents.strip().split() if p],
                "author": author,
                "date": date,
                "message": msg,
            })
        return commits
