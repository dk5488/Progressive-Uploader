from typing import Dict, Any, Tuple
from pathlib import Path
from src.git.operations import GitOperations
from src.llm.provider import LLMProvider

class GitSafety:
    def __init__(self, git: GitOperations, llm: LLMProvider):
        self.git = git
        self.llm = llm
        
    def check_unrelated_changes(self, diff: str, release: Dict[str, Any]) -> Tuple[bool, str]:
        """Uses LLM to verify that the diff only contains changes relevant to the release."""
        diff_str = (diff or "").strip()
        files = release.get("files_involved", [])
        
        # If diff is empty, check if candidate files exist on disk
        if not diff_str:
            if files:
                root_path = Path(self.git.project_root)
                existing = [f for f in files if (root_path / f.replace("/", "\\")).exists() or (root_path / f).exists()]
                if existing:
                    return True, f"Verified {len(existing)} candidate files present on disk for release."
            return False, "No changes or candidate files detected."
            
        desc = f"{release.get('feature')}: {release.get('description')}"
        
        # Truncate diff sample if too long to avoid token limit errors
        diff_sample = diff_str[:4000]
        if len(diff_str) > 4000:
            diff_sample += f"\n... [diff truncated from {len(diff_str)} chars]"
            
        evaluation = self.llm.evaluate_diff(diff_sample, desc)
        
        if evaluation.get("unrelated_changes_detected") or not evaluation.get("is_safe"):
            return False, evaluation.get("reasoning", "Unsafe or unrelated changes detected.")
            
        return True, "Diff is safe and coherent."
        
    def has_pending_unrelated_changes(self) -> bool:
        """Basic check if git tree is dirty before we even start."""
        return self.git.has_uncommitted_changes()
