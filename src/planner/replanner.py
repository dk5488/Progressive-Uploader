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

        roadmap = self.state.load_roadmap() or {}
        releases = roadmap.get("releases", [])
        completed = project_state.get("completed_releases", 0)

        # 1. If all releases in roadmap are already completed, mark completed and sync total
        if releases and completed >= len(releases):
            project_state["status"] = "COMPLETED"
            project_state["total_releases"] = completed
            self.state.save_state(project_state)
            return

        # 2. Check if replanning is actually needed based on repository files
        all_repo_files = None
        if hasattr(self.analyzer, "get_all_files"):
            try:
                res = self.analyzer.get_all_files()
                if isinstance(res, (list, set, tuple)):
                    all_repo_files = set(res)
            except Exception:
                pass

        if all_repo_files is not None and len(all_repo_files) > 0 and releases:
            all_planned_files = {f for r in releases for f in r.get("files_involved", [])}
            completed_files = {f for r in releases[:completed] for f in r.get("files_involved", [])}
            pending_releases = releases[completed:]
            uncovered_files = all_repo_files - all_planned_files

            # Case A: Every file in repo is already planned in roadmap, and pending releases exist
            if len(uncovered_files) == 0 and len(pending_releases) > 0:
                if project_state.get("total_releases") != len(releases):
                    project_state["total_releases"] = len(releases)
                    self.state.save_state(project_state)
                return

            # Case B: All repo files have already been published
            if (all_repo_files - completed_files) == set():
                project_state["status"] = "COMPLETED"
                project_state["total_releases"] = completed
                self.state.save_state(project_state)
                return

        print("Re-evaluating project state for dynamic replanning...")
        
        try:
            # 3. Determine remaining unreleased files for token efficiency and preventing re-planning of finished work
            completed_files = set()
            if releases and completed > 0:
                completed_files = {f for r in releases[:completed] for f in r.get("files_involved", [])}

            if all_repo_files is not None and len(all_repo_files) > 0:
                unreleased_files = sorted(list(all_repo_files - completed_files))
                if not unreleased_files:
                    project_state["status"] = "COMPLETED"
                    project_state["total_releases"] = completed
                    self.state.save_state(project_state)
                    return
                file_list = "\n".join(unreleased_files)
                file_contents = self.analyzer.get_file_contents_for_files(unreleased_files) if hasattr(self.analyzer, "get_file_contents_for_files") else self.analyzer.get_file_contents()
            else:
                file_contents = self.analyzer.get_file_contents()
                file_list = self.analyzer.get_file_list_string()

            file_tree = self.analyzer.get_file_tree()
            arch = self.llm.analyze_repository(file_tree)
            
            # 4. Identify remaining features/complexity on remaining files
            features_data = self.llm.identify_features(arch, file_contents, file_tree=file_list)
            
            # 5. Generate new roadmap based on remaining work
            new_roadmap = self.llm.generate_roadmap(features_data, file_tree=file_list)
            
            # 6. Update roadmap and state
            estimated_remaining = len(new_roadmap) if new_roadmap else 0
            new_total = completed + estimated_remaining

            if new_roadmap and isinstance(new_roadmap, list):
                # Update roadmap so new remaining releases actually exist and can be executed
                if releases:
                    updated_releases = list(releases[:completed]) + list(new_roadmap)
                    self.state.save_roadmap({"releases": updated_releases})
                    new_total = len(updated_releases)

            if project_state.get('total_releases', 0) != new_total or (new_roadmap and releases):
                print(f"Roadmap updated! New estimated total releases: {new_total}")
                project_state['total_releases'] = new_total
                self.state.save_state(project_state)
        except Exception as e:
            print(f"Warning: Replanning skipped due to LLM limit: {e}")
