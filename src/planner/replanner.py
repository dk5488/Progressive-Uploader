from typing import Dict, Any
from src.llm.provider import LLMProvider
from src.analyzer.repository_analyzer import RepositoryAnalyzer
from src.state.state_manager import StateManager

class Replanner:
    """Dynamically replans the remaining roadmap after a release."""
    
    def __init__(self, llm: LLMProvider, analyzer: RepositoryAnalyzer, state: StateManager):
        self.llm = llm
        self.analyzer = analyzer
        self.state = state
        
    def replan_if_needed(self):
        """
        Reevaluates the remaining project and updates the roadmap.
        Safely handles LLM rate limits without failing the release.
        """
        project_state = self.state.load_state()
        if project_state.get("status") == "COMPLETED":
            return
            
        print("Re-evaluating project state for dynamic replanning...")
        
        try:
            # 1. Gather current state using compact file list for token efficiency
            file_tree = self.analyzer.get_file_tree()
            arch = self.llm.analyze_repository(file_tree)
            file_contents = self.analyzer.get_file_contents()
            file_list = self.analyzer.get_file_list_string()
            
            # 2. Identify remaining features/complexity
            features_data = self.llm.identify_features(arch, file_contents, file_tree=file_list)
            
            # 3. Generate new roadmap based on remaining work
            new_roadmap = self.llm.generate_roadmap(features_data, file_tree=file_list)
            
            # Update estimate
            completed = project_state.get('completed_releases', 0)
            estimated_remaining = len(new_roadmap)
            
            new_total = completed + estimated_remaining
            if project_state.get('total_releases', 0) != new_total:
                print(f"Roadmap updated! New estimated total releases: {new_total}")
                project_state['total_releases'] = new_total
                self.state.save_state(project_state)
        except Exception as e:
            print(f"Warning: Replanning skipped due to LLM limit: {e}")
