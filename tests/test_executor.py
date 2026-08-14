import pytest
from unittest.mock import Mock, call
from pathlib import Path
import tempfile
from src.release.release_executor import ReleaseExecutor

@pytest.fixture
def mocks(tmp_path):
    state = Mock()
    git = Mock()
    safety = Mock()
    diff_builder = Mock()
    validator = Mock()
    replanner = Mock()
    notifier = Mock()
    
    # Defaults
    validator.validate.return_value = True
    safety.check_unrelated_changes.return_value = (True, "OK")
    git.push.return_value = (True, "Success")
    git.get_commit_history.return_value = []
    git.has_staged_changes.return_value = True
    state.load_state.return_value = {}
    state.load_roadmap.return_value = {"releases": [{}, {}]}
    state.load_history.return_value = {"releases": []}
    state.state_dir = tmp_path / ".incremental-publisher"
    state.state_dir.mkdir(parents=True, exist_ok=True)
    
    return state, git, safety, diff_builder, validator, replanner, notifier

def test_executor_successful_release(mocks):
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"feature": "Core", "description": "Init", "files_involved": ["file1.txt", "file2.txt"], "_index": 0}
    success, msg = executor.execute(release)
    
    assert success == True
    assert git.commit.call_count == 2
    assert git.push.call_count == 2
    state.save_state.assert_called_once()
    replanner.replan_if_needed.assert_called_once()
    notifier.send_message.assert_called_once()

def test_executor_push_failure(mocks):
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    git.push.return_value = (False, "Network error")
    
    release = {"feature": "Core", "description": "Init", "files_involved": ["file1.txt"], "_index": 0}
    success, msg = executor.execute(release)
    
    assert success == False
    assert "Push failed" in msg
    git.commit.assert_called_once()
    state.save_state.assert_not_called()

def test_executor_crash_recovery(mocks):
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    # Simulate that file1.txt is already committed
    git.get_commit_history.return_value = ["feat(core): add file1.txt"]
    
    release = {"feature": "Core", "description": "Init", "files_involved": ["file1.txt"], "_index": 0}
    success, msg = executor.execute(release)
    
    assert success == True
    git.commit.assert_not_called()
    git.push.assert_called_once()
    state.save_state.assert_called_once()

def test_executor_validation_failure(mocks):
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    validator.validate.return_value = False
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"feature": "Core", "description": "Init", "files_involved": ["file1.txt"]}
    success, msg = executor.execute(release)
    
    assert success == False
    git.commit.assert_not_called()
    git.push.assert_not_called()

def test_executor_safety_failure(mocks):
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    safety.check_unrelated_changes.return_value = (False, "Unrelated file")
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"feature": "Core", "description": "Init", "files_involved": ["file1.txt"]}
    success, msg = executor.execute(release)
    
    assert success == False
    git.commit.assert_not_called()
    git.push.assert_not_called()
