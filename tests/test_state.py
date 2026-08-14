import pytest
import os
import shutil
from src.state.state_manager import StateManager

@pytest.fixture
def temp_project(tmp_path):
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    yield str(project_dir)
    if project_dir.exists():
        shutil.rmtree(project_dir)

def test_state_initialization(temp_project):
    state = StateManager(temp_project)
    assert not state.is_initialized()
    
    state.init_project()
    assert state.is_initialized()
    
    # Check default structure
    assert state.load_config() == {}
    assert state.load_roadmap() == {}
    assert state.load_state() == {}
    assert state.load_history() == {}

def test_state_persistence(temp_project):
    state = StateManager(temp_project)
    state.init_project()
    
    test_roadmap = {"releases": [{"id": 1}]}
    state.save_roadmap(test_roadmap)
    
    loaded = state.load_roadmap()
    assert loaded == test_roadmap
