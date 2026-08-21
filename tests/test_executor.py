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

def test_executor_empty_pushed_files_marks_skipped(mocks):
    """When all files are already clean/committed, release is marked SKIPPED and advances state."""
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    git.has_staged_changes.return_value = False
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"release_id": 7, "feature": "Core", "description": "Init", "files_involved": ["file1.txt", "file2.txt"], "_index": 6}
    success, msg = executor.execute(release)
    
    assert success == True
    assert "skipped" in msg.lower() or "already published" in msg.lower()
    git.commit.assert_not_called()
    git.push.assert_not_called()
    state.save_state.assert_called_once()
    state.save_history.assert_called_once()
    notifier.send_message.assert_called_once()
    
    # Verify history recorded SKIPPED status
    saved_history = state.save_history.call_args[0][0]
    assert saved_history["releases"][-1]["status"] == "SKIPPED"

def test_executor_no_files_involved_marks_skipped(mocks):
    """When release has no files involved, it is marked SKIPPED and advances state without failing."""
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"release_id": 7, "feature": "Core", "description": "Init", "files_involved": [], "_index": 6}
    success, msg = executor.execute(release)
    
    assert success == True
    assert "SKIPPED" in msg
    state.save_state.assert_called_once()
    state.save_history.assert_called_once()

def test_executor_crash_recovery_push_failure(mocks):
    """When crash recovery push fails, execute must return False and not save state."""
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    git.get_commit_history.return_value = ["feat(core): add file1.txt"]
    git.push.return_value = (False, "Authentication failed")
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"release_id": 1, "feature": "Core", "description": "Init", "files_involved": ["file1.txt"], "_index": 0}
    success, msg = executor.execute(release)
    
    assert success == False
    state.save_state.assert_not_called()

def test_executor_telegram_delivery_failure_logged(mocks, capsys):
    """When Telegram send_message returns False, release completes and logs a warning."""
    state, git, safety, diff_builder, validator, replanner, notifier = mocks
    notifier.send_message.return_value = False
    
    executor = ReleaseExecutor(state, git, safety, diff_builder, validator, replanner, notifier=notifier)
    
    release = {"release_id": 1, "feature": "Core", "description": "Init", "files_involved": ["file1.txt"], "_index": 0}
    success, msg = executor.execute(release)
    
    assert success == True
    captured = capsys.readouterr()
    assert "Telegram notification failed to deliver" in captured.out

