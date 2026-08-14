from typing import List, Dict, Any
from src.git.operations import GitOperations

class DiffBuilder:
    """Builds a candidate diff for a release."""
    def __init__(self, git: GitOperations):
        self.git = git

    def get_candidate_diff(self, release: Dict[str, Any]) -> str:
        files = release.get("files_involved", [])
        
        if files:
            for f in files:
                try:
                    clean_f = f.replace("\\", "/")
                    self.git._run(["git", "add", "-N", clean_f], check=False)
                except Exception:
                    pass
            
            clean_files = [f.replace("\\", "/") for f in files]
            res = self.git._run(["git", "diff"] + clean_files, check=False)
            return res.stdout or ""
            
        return self.git.get_diff() or ""
