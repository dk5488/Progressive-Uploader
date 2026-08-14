import os
from pathlib import Path
from typing import List, Dict, Tuple
from src.security.secret_scanner import SecretScanner

class RepositoryAnalyzer:
    """Analyzes the local repository structure."""

    IGNORE_DIRS = {".git", ".incremental-publisher", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea", ".vscode", ".qodo"}

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scanner = SecretScanner()

    def get_all_files(self) -> List[str]:
        """Returns a flat list of all relative file paths in the repo (excluding ignored dirs and secrets).
        Used for coverage validation to ensure every file is assigned to a release.
        """
        all_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for f in files:
                path = Path(root) / f
                if self.scanner.is_file_allowed(path):
                    rel_path = str(path.relative_to(self.project_root)).replace("\\", "/")
                    all_files.append(rel_path)
        return all_files

    def count_files(self) -> int:
        """Returns the total number of analyzable files in the repo."""
        return len(self.get_all_files())

    def get_file_list_string(self) -> str:
        """Returns a compact one-file-per-line listing — much more token-efficient than get_file_tree()."""
        return "\n".join(self.get_all_files())

    def get_files_by_directory(self) -> Dict[str, List[str]]:
        """Groups files by their top-level directory (or 'root' for top-level files).
        Used for batched processing of large repos.
        """
        groups: Dict[str, List[str]] = {}
        for f in self.get_all_files():
            parts = f.split("/")
            key = parts[0] if len(parts) > 1 else "root"
            groups.setdefault(key, []).append(f)
        return groups

    def get_file_contents_for_files(self, file_list: List[str], max_lines_per_file: int = 50) -> Dict[str, str]:
        """Gets content samples for a specific list of files."""
        contents = {}
        for rel_path in file_list:
            path = self.project_root / rel_path.replace("/", os.sep)
            if not path.exists() or not self.scanner.is_file_allowed(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    lines = [next(fh) for _ in range(max_lines_per_file)]
                    sample = "".join(lines)
                    if not self.scanner.scan_content(sample):
                        contents[rel_path] = sample
            except (UnicodeDecodeError, StopIteration, Exception):
                pass
        return contents

    def get_file_tree(self, max_depth: int = 5, max_files_per_dir: int = 50) -> str:
        """Returns a string representation of the file tree.
        Truncates deep directories and large numbers of files to prevent context window overflows.
        """
        tree = []
        for root, dirs, files in os.walk(self.project_root):
            # Mutate dirs in-place to ignore directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            level = root.replace(str(self.project_root), '').count(os.sep)
            
            if level > max_depth:
                dirs[:] = []
                continue
                
            indent = ' ' * 4 * (level)
            tree.append(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 4 * (level + 1)
            
            allowed_files = [f for f in files if self.scanner.is_file_allowed(Path(f))]
            for i, f in enumerate(allowed_files):
                if i >= max_files_per_dir:
                    tree.append(f"{subindent}... and {len(allowed_files) - max_files_per_dir} more files")
                    break
                tree.append(f"{subindent}{f}")
                
            if level == max_depth and dirs:
                tree.append(f"{subindent}... and {len(dirs)} subdirectories (truncated)")
                dirs[:] = []
                
        return "\n".join(tree)

    def get_file_contents(self, max_files: int = 50, max_lines_per_file: int = 50) -> Dict[str, str]:
        """Gets a sample of file contents for AI analysis. Avoids binaries and secrets.
        Automatically raises limits for repos with fewer than 200 files.
        """
        # Auto-detect repo size and raise limits for small repos
        total_files = self.count_files()
        if total_files <= 200:
            max_files = max(max_files, total_files)
            max_lines_per_file = max(max_lines_per_file, 100)
        
        contents = {}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for f in files:
                if len(contents) >= max_files:
                    return contents
                
                path = Path(root) / f
                if not self.scanner.is_file_allowed(path):
                    continue
                
                try:
                    with open(path, 'r', encoding='utf-8') as file_handle:
                        lines = [next(file_handle) for _ in range(max_lines_per_file)]
                        content_sample = "".join(lines)
                        
                        if not self.scanner.scan_content(content_sample):
                            rel_path = str(path.relative_to(self.project_root)).replace("\\", "/")
                            contents[rel_path] = content_sample
                except (UnicodeDecodeError, StopIteration):
                    # Skip binaries or empty files
                    pass
                except Exception:
                    pass
                    
        return contents

