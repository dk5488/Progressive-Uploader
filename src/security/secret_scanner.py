import re
from pathlib import Path
from typing import List, Set

class SecretScanner:
    """Scans content for potential secrets."""
    
    # Common patterns for secrets
    PATTERNS = [
        re.compile(r"AKIA[0-9A-Z]{16}"), # AWS
        re.compile(r"sk-[a-zA-Z0-9]{48}"), # OpenAI
        re.compile(r"AIza[0-9A-Za-z-_]{35}"), # GCP
        re.compile(r"(?i)(api_key|apikey|secret|token|password)[\s]*[:=][\s]*[\"'][^\"']+[\"']") # Generic
    ]
    
    # Files to always ignore entirely due to security
    IGNORE_FILES = {".env", "credentials", "secrets.json", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
    IGNORE_EXTENSIONS = {".pem", ".key", ".p12", ".pfx"}

    def is_file_allowed(self, path: Path) -> bool:
        """Check if file should be analyzed or ignored completely."""
        if path.name in self.IGNORE_FILES:
            return False
        if any(path.name.startswith(f) for f in {".env."}):
            return False
        if path.suffix in self.IGNORE_EXTENSIONS:
            return False
        return True

    def scan_content(self, content: str) -> bool:
        """Returns True if a secret is detected."""
        for pattern in self.PATTERNS:
            if pattern.search(content):
                return True
        return False
