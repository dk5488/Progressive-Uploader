from typing import Dict, Any, Optional
from src.state.state_manager import StateManager

class ReleaseSelector:
    def __init__(self, state: StateManager):
        self.state = state
        
    def get_next_release(self) -> Optional[Dict[str, Any]]:
        """Returns the next uncompleted release from the roadmap."""
        roadmap = self.state.load_roadmap()
        releases = roadmap.get("releases", [])
        
        project_state = self.state.load_state()
        last_success = project_state.get("last_successful_release_index", -1)
        
        next_index = last_success + 1
        
        if next_index < len(releases):
            # Annotate with index so we can update state later
            rel = releases[next_index].copy()
            rel['_index'] = next_index
            return rel
            
        return None
        
    def is_project_completed(self) -> bool:
        project_state = self.state.load_state()
        if project_state.get("status") == "COMPLETED":
            return True
        roadmap = self.state.load_roadmap() or {}
        releases = roadmap.get("releases", [])
        if releases and project_state.get("completed_releases", 0) >= len(releases):
            return True
        return False

