import json
import os
from pathlib import Path
from typing import Dict, Any

class StateManager:
    """Manages the persistent state for the incremental publisher."""
    
    DIR_NAME = ".incremental-publisher"
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / self.DIR_NAME
        self.config_path = self.state_dir / "config.json"
        self.roadmap_path = self.state_dir / "roadmap.json"
        self.state_path = self.state_dir / "state.json"
        self.history_path = self.state_dir / "history.json"
        self.analysis_dir = self.state_dir / "analysis"

    def init_project(self):
        """Creates the necessary directories if they don't exist."""
        self.state_dir.mkdir(exist_ok=True)
        self.analysis_dir.mkdir(exist_ok=True)
        (self.state_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize empty files if they don't exist
        for path in [self.config_path, self.roadmap_path, self.state_path, self.history_path]:
            if not path.exists():
                self._write_json(path, {})

    def is_initialized(self) -> bool:
        """Checks if the project has been initialized."""
        return self.state_dir.exists() and self.state_path.exists()

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _write_json(self, path: Path, data: Dict[str, Any]):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        return self._read_json(self.config_path)

    def save_config(self, data: Dict[str, Any]):
        self._write_json(self.config_path, data)

    def load_roadmap(self) -> Dict[str, Any]:
        return self._read_json(self.roadmap_path)

    def save_roadmap(self, data: Dict[str, Any]):
        self._write_json(self.roadmap_path, data)

    def load_state(self) -> Dict[str, Any]:
        return self._read_json(self.state_path)

    def save_state(self, data: Dict[str, Any]):
        self._write_json(self.state_path, data)

    def load_history(self) -> Dict[str, Any]:
        return self._read_json(self.history_path)

    def save_history(self, data: Dict[str, Any]):
        self._write_json(self.history_path, data)

    def save_analysis(self, filename: str, data: Dict[str, Any]):
        self._write_json(self.analysis_dir / filename, data)

    def load_analysis(self, filename: str) -> Dict[str, Any]:
        return self._read_json(self.analysis_dir / filename)
