import subprocess
import os
from pathlib import Path
from typing import List, Tuple, Optional

class GitOperations:
    """Wraps git commands for the publisher."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root

    def _run(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check
        )

    def is_git_repo(self) -> bool:
        """Check if the directory is a git repository."""
        res = self._run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
        return res.returncode == 0

    def init_repo(self):
        """Initializes a git repository."""
        self._run(["git", "init"])
        self._run(["git", "branch", "-M", "main"], check=False)

    def get_current_branch(self) -> str:
        """Returns current git branch name."""
        res = self._run(["git", "branch", "--show-current"], check=False)
        branch = res.stdout.strip()
        return branch if branch else "main"

    def get_status(self) -> str:
        """Returns the git status."""
        return self._run(["git", "status", "-s"]).stdout.strip()
    
    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        return bool(self.get_status())

    def has_staged_changes(self, file_path: Optional[str] = None) -> bool:
        """Checks if there are staged changes (optionally for a specific file)."""
        cmd = ["git", "diff", "--cached", "--name-only"]
        if file_path:
            cmd.extend(["--", file_path])
        res = self._run(cmd, check=False)
        return bool(res.stdout.strip())

    def get_diff(self) -> str:
        """Returns the current git diff of working tree."""
        # Include untracked files by doing a fake add and diff, or just diffing everything
        self._run(["git", "add", "-N", "."], check=False)
        diff = self._run(["git", "diff"]).stdout
        return diff

    def add_files(self, files: List[str]):
        """Stages specific files."""
        if not files:
            return
        self._run(["git", "add"] + files)

    def add_all(self):
        self._run(["git", "add", "."])

    def commit(self, message: str):
        """Commits staged changes."""
        self._run(["git", "commit", "-m", message])

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> Tuple[bool, str]:
        """Pushes to remote using -u flag. Returns (success, output)."""
        target_branch = branch or self.get_current_branch()
        res = self._run(["git", "push", "-u", remote, target_branch], check=False)
        output = (res.stdout + "\n" + res.stderr).strip()
        if res.returncode == 0:
            return True, output
        else:
            return False, output

    def get_remotes(self) -> List[str]:
        """Returns list of remotes."""
        out = self._run(["git", "remote"]).stdout.strip()
        return out.split("\n") if out else []

    def get_commit_history(self) -> List[str]:
        """Returns list of commit messages."""
        if not self.is_git_repo():
            return []
        res = self._run(["git", "log", "--oneline"], check=False)
        if res.returncode != 0:
            return []
        return res.stdout.strip().split("\n")

