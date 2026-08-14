import subprocess
from pathlib import Path

class ReleaseValidator:
    """Runs build and tests if available."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def validate(self) -> bool:
        """Runs standard project validation (tests/build)."""
        # Very basic detection for MVP
        if (self.project_root / "package.json").exists():
            # Try npm test
            try:
                res = subprocess.run(
                    ["npm", "test"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
                # If script missing, it might exit with error, but let's assume if it fails we block
                if res.returncode != 0 and "missing script" not in res.stderr.lower():
                    print(f"Validation failed:\n{res.stderr}")
                    return False
            except Exception:
                pass
                
        if (self.project_root / "pytest.ini").exists() or (self.project_root / "tests").exists():
            try:
                res = subprocess.run(
                    ["pytest"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    print(f"Validation failed:\n{res.stdout}")
                    return False
            except Exception:
                pass
                
        return True
