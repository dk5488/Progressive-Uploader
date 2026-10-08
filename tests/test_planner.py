import pytest
from unittest.mock import Mock
from src.planner.roadmap_generator import RoadmapGenerator
from src.planner.replanner import Replanner

def test_roadmap_generator_basic():
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    analyzer.get_file_tree.return_value = "tree"
    analyzer.get_file_contents.return_value = {}
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py"]
    analyzer.count_files.return_value = 2
    analyzer.get_file_list_string.return_value = "fileA.py\nfileB.py"
    
    llm.analyze_repository.return_value = {"architecture_type": "MVC"}
    llm.identify_features.return_value = {"features": [{"name": "A"}, {"name": "B"}]}
    
    llm.generate_roadmap.return_value = [
        {"release_id": "r1", "feature": "A", "files_involved": ["fileA.py"]},
        {"release_id": "r2", "feature": "B", "files_involved": ["fileB.py"]}
    ]
    
    state.load_state.return_value = {}
    
    gen = RoadmapGenerator(llm, analyzer, state)
    roadmap = gen.generate()
    
    assert len(roadmap) == 2
    state.save_roadmap.assert_called_once()
    state.save_state.assert_called_once()
    
    # State should have total_releases set
    saved_state = state.save_state.call_args[0][0]
    assert saved_state["total_releases"] == 2
    assert saved_state["status"] == "IN_PROGRESS"

def test_roadmap_generator_coverage_validation():
    """Test that uncovered files are automatically added to catch-all releases."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    analyzer.get_file_tree.return_value = "tree"
    analyzer.get_file_contents.return_value = {}
    analyzer.count_files.return_value = 4
    analyzer.get_file_list_string.return_value = "fileA.py\nfileB.py\nutils/helper.py\nREADME.md"
    # Repo has 4 files, but roadmap only covers 2
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py", "utils/helper.py", "README.md"]
    
    llm.analyze_repository.return_value = {"architecture_type": "MVC"}
    llm.identify_features.return_value = {"features": [{"name": "A"}]}
    
    llm.generate_roadmap.return_value = [
        {"release_id": 1, "feature": "A", "files_involved": ["fileA.py", "fileB.py"]}
    ]
    
    state.load_state.return_value = {}
    
    gen = RoadmapGenerator(llm, analyzer, state)
    roadmap = gen.generate()
    
    # Should have the original release + catch-all releases for uncovered files
    assert len(roadmap) > 1
    
    # All files should now be covered
    all_covered = set()
    for r in roadmap:
        for f in r.get("files_involved", []):
            all_covered.add(f)
    
    assert "utils/helper.py" in all_covered
    assert "README.md" in all_covered

def test_roadmap_generator_batched_mode():
    """Test that large repos trigger batched processing."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    # Create a repo with 150 files (above BATCH_THRESHOLD)
    many_files = [f"src/file_{i}.py" for i in range(120)] + [f"tests/test_{i}.py" for i in range(30)]
    
    analyzer.get_file_tree.return_value = "large tree"
    analyzer.count_files.return_value = 150
    analyzer.get_all_files.return_value = many_files
    analyzer.get_file_list_string.return_value = "\n".join(many_files)
    analyzer.get_files_by_directory.return_value = {
        "src": [f"src/file_{i}.py" for i in range(120)],
        "tests": [f"tests/test_{i}.py" for i in range(30)]
    }
    analyzer.get_file_contents_for_files.return_value = {}
    
    llm.analyze_repository.return_value = {"architecture_type": "Modular"}
    llm.identify_features.return_value = {"features": [
        {"name": "Core", "files_involved": many_files[:75], "dependencies": [], "complexity": "L"},
    ]}
    
    # Roadmap covers all files
    llm.generate_roadmap.return_value = [
        {"release_id": 1, "feature": "Core", "files_involved": many_files}
    ]
    
    state.load_state.return_value = {}
    
    gen = RoadmapGenerator(llm, analyzer, state)
    roadmap = gen.generate()
    
    # Should have called identify_features multiple times (batched)
    assert llm.identify_features.call_count > 1
    
    # Roadmap should exist
    assert len(roadmap) >= 1

def test_merge_features():
    """Test that features with the same name from different batches are merged."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    gen = RoadmapGenerator(llm, analyzer, state)
    
    features = [
        {"name": "Auth", "complexity": "S", "dependencies": [], "files_involved": ["login.py"]},
        {"name": "Auth", "complexity": "M", "dependencies": ["DB"], "files_involved": ["register.py"]},
        {"name": "DB", "complexity": "S", "dependencies": [], "files_involved": ["db.py"]},
    ]
    
    merged = gen._merge_features(features)
    
    assert len(merged) == 2  # Auth + DB
    
    auth = [f for f in merged if f["name"] == "Auth"][0]
    assert set(auth["files_involved"]) == {"login.py", "register.py"}
    assert "DB" in auth["dependencies"]
    assert auth["complexity"] == "M"  # Upgraded from S

def test_replanner_updates_estimate():
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    # Project state
    state.load_state.return_value = {
        "status": "IN_PROGRESS",
        "completed_releases": 5,
        "total_releases": 10
    }
    state.load_roadmap.return_value = {}
    
    # New remaining roadmap has 7 items
    llm.generate_roadmap.return_value = [{} for _ in range(7)]
    
    replanner = Replanner(llm, analyzer, state)
    replanner.replan_if_needed()
    
    # New total should be completed (5) + new remaining (7) = 12
    saved_state = state.save_state.call_args[0][0]
    assert saved_state["total_releases"] == 12

def test_replanner_completed_skips():
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    state.load_state.return_value = {"status": "COMPLETED"}
    
    replanner = Replanner(llm, analyzer, state)
    replanner.replan_if_needed()
    
    llm.analyze_repository.assert_not_called()

def test_validate_roadmap_rejects_duplicates():
    gen = RoadmapGenerator(Mock(), Mock(), Mock())
    roadmap = [
        {"release_id": 1, "feature": "A", "files_involved": ["file1.py", "file2.py"]},
        {"release_id": 2, "feature": "B", "files_involved": ["file2.py", "file3.py"]}
    ]
    with pytest.raises(ValueError, match="duplicate file assignments detected"):
        gen.validate_roadmap(roadmap)

def test_validate_roadmap_success():
    gen = RoadmapGenerator(Mock(), Mock(), Mock())
    roadmap = [
        {"release_id": 1, "feature": "A", "files_involved": ["file1.py", "file2.py"]},
        {"release_id": 2, "feature": "B", "files_involved": ["file3.py"]}
    ]
    assert gen.validate_roadmap(roadmap, all_files={"file1.py", "file2.py", "file3.py"}) is True

def test_roadmap_generator_deduplicates_llm_output():
    """Test that if LLM returns duplicate files across releases, generator deduplicates so each file belongs to exactly one release."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    analyzer.get_file_tree.return_value = "tree"
    analyzer.get_file_contents.return_value = {}
    analyzer.count_files.return_value = 2
    analyzer.get_file_list_string.return_value = "fileA.py\nfileB.py"
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py"]
    
    llm.analyze_repository.return_value = {"architecture_type": "MVC"}
    llm.identify_features.return_value = {"features": [{"name": "A"}]}
    # LLM mistakenly puts fileA.py in both releases
    llm.generate_roadmap.return_value = [
        {"release_id": 1, "feature": "A", "files_involved": ["fileA.py", "fileB.py"]},
        {"release_id": 2, "feature": "B", "files_involved": ["fileA.py"]}
    ]
    
    state.load_state.return_value = {}
    
    gen = RoadmapGenerator(llm, analyzer, state)
    roadmap = gen.generate()
    
    # Should validate cleanly without throwing duplicate error
    assert gen.validate_roadmap(roadmap) is True
    # fileA.py should only be in release 1
    assert roadmap[0]["files_involved"] == ["fileA.py", "fileB.py"]
    assert roadmap[1]["files_involved"] == []

def test_replanner_skips_when_all_files_covered():
    """Replanner should NOT invoke LLM when all repository files are already planned and pending releases exist."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    state.load_state.return_value = {
        "status": "IN_PROGRESS",
        "completed_releases": 1,
        "total_releases": 10  # Drifted total
    }
    state.load_roadmap.return_value = {
        "releases": [
            {"files_involved": ["fileA.py"]},
            {"files_involved": ["fileB.py"]}
        ]
    }
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py"]
    
    replanner = Replanner(llm, analyzer, state)
    replanner.replan_if_needed()
    
    # LLM must not be called
    llm.analyze_repository.assert_not_called()
    # State should synchronize total_releases to 2
    saved_state = state.save_state.call_args[0][0]
    assert saved_state["total_releases"] == 2

def test_replanner_completes_when_all_files_published():
    """Replanner marks project COMPLETED when all repo files have already been published."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    state.load_state.return_value = {
        "status": "IN_PROGRESS",
        "completed_releases": 2,
        "total_releases": 5
    }
    state.load_roadmap.return_value = {
        "releases": [
            {"files_involved": ["fileA.py"]},
            {"files_involved": ["fileB.py"]}
        ]
    }
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py"]
    
    replanner = Replanner(llm, analyzer, state)
    replanner.replan_if_needed()
    
    llm.analyze_repository.assert_not_called()
    saved_state = state.save_state.call_args[0][0]
    assert saved_state["status"] == "COMPLETED"
    assert saved_state["total_releases"] == 2

def test_replanner_detects_new_uncovered_files():
    """Replanner triggers LLM analysis when new uncovered files are added to repository."""
    llm = Mock()
    analyzer = Mock()
    state = Mock()
    
    state.load_state.return_value = {
        "status": "IN_PROGRESS",
        "completed_releases": 1,
        "total_releases": 2
    }
    state.load_roadmap.return_value = {
        "releases": [
            {"files_involved": ["fileA.py"]},
            {"files_involved": ["fileB.py"]}
        ]
    }
    # fileC.py is newly added to repository
    analyzer.get_all_files.return_value = ["fileA.py", "fileB.py", "fileC.py"]
    analyzer.get_file_tree.return_value = "tree"
    analyzer.get_file_contents_for_files.return_value = {"fileB.py": "b", "fileC.py": "c"}
    
    llm.analyze_repository.return_value = {"architecture_type": "Modular"}
    llm.identify_features.return_value = {"features": [{"name": "New"}]}
    llm.generate_roadmap.return_value = [
        {"release_id": 2, "feature": "New", "files_involved": ["fileB.py", "fileC.py"]}
    ]
    
    replanner = Replanner(llm, analyzer, state)
    replanner.replan_if_needed()
    
    llm.analyze_repository.assert_called_once()
    state.save_roadmap.assert_called_once()
    saved_state = state.save_state.call_args[0][0]
    assert saved_state["total_releases"] == 2


