from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
from src.llm.provider import LLMProvider
from src.analyzer.repository_analyzer import RepositoryAnalyzer
from src.state.state_manager import StateManager
import os
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Threshold for batched processing — repos with more files than this
# will be processed in chunks to avoid exceeding LLM token limits.
BATCH_THRESHOLD = 100
# Max files per batch when doing batched feature identification
MAX_FILES_PER_BATCH = 50


class RoadmapGenerator:
    def __init__(self, llm: LLMProvider, analyzer: RepositoryAnalyzer, state: StateManager):
        self.llm = llm
        self.analyzer = analyzer
        self.state = state

    def generate(self) -> List[Dict[str, Any]]:
        """Analyzes repo and generates a roadmap.
        Automatically selects single-pass or batched mode based on repo size.
        """
        print("Analyzing repository structure...")
        total_files = self.analyzer.count_files()
        print(f"Repository contains {total_files} analyzable files.")
        
        file_tree = self.analyzer.get_file_tree()
        architecture = self.llm.analyze_repository(file_tree)
        self.state.save_analysis("architecture.json", architecture)
        
        print(f"Architecture detected: {architecture.get('architecture_type')} using {architecture.get('language')}")
        
        # Choose strategy based on repo size
        if total_files <= BATCH_THRESHOLD:
            features_data = self._identify_features_single(architecture, file_tree)
        else:
            features_data = self._identify_features_batched(architecture, file_tree)
        
        self.state.save_analysis("features.json", features_data)
        print(f"Detected {len(features_data.get('features', []))} potential features.")
        
        # For roadmap generation, use compact file list instead of tree for token efficiency
        file_list = self.analyzer.get_file_list_string()
        
        print("Generating release roadmap...")
        roadmap = self.llm.generate_roadmap(features_data, file_tree=file_list)
        
        # Validate file coverage, deduplicate, and patch any gaps
        roadmap = self._ensure_full_coverage(roadmap)
        
        # Validate that every file belongs to exactly one release with zero duplicates
        self.validate_roadmap(roadmap, all_files=set(self.analyzer.get_all_files()))
        
        # Save to state
        self.state.save_roadmap({"releases": roadmap})
        
        # Initialize state with roadmap info
        current_state = self.state.load_state()
        current_state.update({
            "status": "IN_PROGRESS",
            "total_releases": len(roadmap),
            "completed_releases": 0,
            "last_successful_release_index": -1
        })
        self.state.save_state(current_state)
        
        return roadmap

    def _identify_features_single(self, architecture: Dict[str, Any], file_tree: str) -> Dict[str, Any]:
        """Single-pass feature identification for small repos."""
        print("Identifying logical features (single-pass mode)...")
        file_contents = self.analyzer.get_file_contents()
        # Use compact file list for token efficiency
        file_list = self.analyzer.get_file_list_string()
        return self.llm.identify_features(architecture, file_contents, file_tree=file_list)

    def _identify_features_batched(self, architecture: Dict[str, Any], file_tree: str) -> Dict[str, Any]:
        """Batched feature identification for large repos.
        Splits files by directory, processes each batch separately, then merges.
        """
        print("Identifying logical features (batched mode for large repo)...")
        dir_groups = self.analyzer.get_files_by_directory()
        
        # Build batches — merge small directories together, split large ones
        batches: List[List[str]] = []
        current_batch: List[str] = []
        
        for dir_name, files in sorted(dir_groups.items()):
            if len(files) > MAX_FILES_PER_BATCH:
                # Flush current batch first
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                # Split large directory into sub-batches
                for i in range(0, len(files), MAX_FILES_PER_BATCH):
                    batches.append(files[i:i + MAX_FILES_PER_BATCH])
            elif len(current_batch) + len(files) > MAX_FILES_PER_BATCH:
                # Current batch would overflow — flush it
                batches.append(current_batch)
                current_batch = list(files)
            else:
                current_batch.extend(files)
        
        if current_batch:
            batches.append(current_batch)
        
        print(f"  Processing {len(batches)} batches...")
        
        all_features: List[Dict[str, Any]] = []
        
        for i, batch_files in enumerate(batches):
            print(f"  Batch {i + 1}/{len(batches)}: {len(batch_files)} files...")
            
            # Get content samples for this batch
            contents = self.analyzer.get_file_contents_for_files(batch_files, max_lines_per_file=30)
            
            # Create a compact file list for just this batch
            batch_file_list = "\n".join(batch_files)
            
            try:
                batch_result = self.llm.identify_features(architecture, contents, file_tree=batch_file_list)
                batch_features = batch_result.get("features", [])
                all_features.extend(batch_features)
                print(f"    Found {len(batch_features)} features.")
            except Exception as e:
                print(f"    Warning: Batch {i + 1} failed: {e}")
                # Create a fallback feature for the batch
                all_features.append({
                    "name": f"Batch {i + 1} Files",
                    "description": f"Files from batch {i + 1} that could not be analyzed",
                    "complexity": "M",
                    "dependencies": [],
                    "files_involved": batch_files
                })
        
        # Merge duplicate feature names
        merged = self._merge_features(all_features)
        
        return {"features": merged}

    def _merge_features(self, features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merges features with the same name from different batches."""
        by_name: Dict[str, Dict[str, Any]] = {}
        
        for feat in features:
            name = feat.get("name", "Unknown")
            if name in by_name:
                # Merge files_involved and dependencies
                existing = by_name[name]
                existing_files = set(existing.get("files_involved", []))
                new_files = set(feat.get("files_involved", []))
                existing["files_involved"] = list(existing_files | new_files)
                
                existing_deps = set(existing.get("dependencies", []))
                new_deps = set(feat.get("dependencies", []))
                existing["dependencies"] = list(existing_deps | new_deps)
                
                # Upgrade complexity if the new feature is larger
                complexity_order = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4}
                existing_c = complexity_order.get(existing.get("complexity", "S"), 1)
                new_c = complexity_order.get(feat.get("complexity", "S"), 1)
                if new_c > existing_c:
                    existing["complexity"] = feat["complexity"]
            else:
                by_name[name] = dict(feat)
        
        return list(by_name.values())

    def _ensure_full_coverage(self, roadmap: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates every repo file appears in exactly one release.
        Deduplicates files so each file belongs only to its first assigned release.
        Groups uncovered files into catch-all releases by directory.
        """
        all_files = set(self.analyzer.get_all_files())
        
        # Deduplicate files across roadmap releases (assign to first release seen)
        seen_files = set()
        for release in roadmap:
            unique_files = []
            for f in release.get("files_involved", []):
                normalized = f.replace("\\", "/")
                if normalized not in seen_files:
                    seen_files.add(normalized)
                    unique_files.append(normalized)
            release["files_involved"] = unique_files
        
        uncovered = all_files - seen_files
        
        if not uncovered:
            print(f"File coverage: {len(all_files)}/{len(all_files)} files covered.")
            return roadmap
        
        print(f"File coverage: {len(seen_files)}/{len(all_files)} files covered. Adding {len(uncovered)} missing files...")
        
        # Group uncovered files by their top-level directory (or root)
        groups: Dict[str, List[str]] = {}
        for f in sorted(uncovered):
            parts = f.split("/")
            if len(parts) > 1:
                group_key = parts[0]
            else:
                group_key = "root"
            groups.setdefault(group_key, []).append(f)
        
        # Determine next release_id
        max_id = 0
        for r in roadmap:
            rid = r.get("release_id", 0)
            try:
                max_id = max(max_id, int(rid))
            except (ValueError, TypeError):
                max_id = max(max_id, len(roadmap))
        
        # Create catch-all releases for each group, splitting large groups
        for group_name, files in groups.items():
            group_label = group_name.replace("/", " ").replace("_", " ").title()
            
            # Split large groups into multiple releases (max 20 files per release)
            chunk_size = 20
            for chunk_idx in range(0, len(files), chunk_size):
                chunk = files[chunk_idx:chunk_idx + chunk_size]
                max_id += 1
                
                suffix = f" (part {chunk_idx // chunk_size + 1})" if len(files) > chunk_size else ""
                
                catch_all = {
                    "release_id": max_id,
                    "feature": f"{group_label} Files{suffix}",
                    "description": f"Remaining {group_label.lower()} files not covered by primary releases",
                    "complexity": "S" if len(chunk) <= 5 else "M",
                    "dependencies": [],
                    "files_involved": chunk,
                    "validation_requirements": [f"Verify {group_label.lower()} files are present"]
                }
                roadmap.append(catch_all)
                print(f"  Added catch-all release {max_id}: {len(chunk)} {group_label.lower()} files")
        
        return roadmap

    def validate_roadmap(self, roadmap: List[Dict[str, Any]], all_files: Optional[Set[str]] = None) -> bool:
        """Validates roadmap integrity:
        - Every file must belong to exactly one release.
        - Rejects duplicate file assignments across releases.
        - Optionally verifies that all repository files are covered.
        """
        file_to_releases = defaultdict(list)
        
        for release in roadmap:
            rel_id = release.get("release_id", "unknown")
            for f in release.get("files_involved", []):
                normalized = f.replace("\\", "/")
                file_to_releases[normalized].append(str(rel_id))
                
        duplicates = {f: rids for f, rids in file_to_releases.items() if len(rids) > 1}
        if duplicates:
            duplicate_details = "; ".join([f"'{f}' in releases {rids}" for f, rids in duplicates.items()])
            raise ValueError(f"Roadmap validation failed: duplicate file assignments detected: {duplicate_details}")
            
        if all_files is not None:
            normalized_all = {f.replace("\\", "/") for f in all_files}
            covered = set(file_to_releases.keys())
            missing = normalized_all - covered
            if missing:
                raise ValueError(f"Roadmap validation failed: {len(missing)} files missing from roadmap: {sorted(list(missing))[:10]}")
                
        return True
