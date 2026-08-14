import pytest
from unittest.mock import Mock, patch
from src.git.safety import GitSafety

def test_has_pending_unrelated_changes():
    mock_git = Mock()
    mock_git.has_uncommitted_changes.return_value = True
    
    mock_llm = Mock()
    
    safety = GitSafety(mock_git, mock_llm)
    assert safety.has_pending_unrelated_changes() == True
    
def test_check_unrelated_changes_safe():
    mock_git = Mock()
    mock_llm = Mock()
    mock_llm.evaluate_diff.return_value = {
        "is_safe": True,
        "unrelated_changes_detected": False,
        "reasoning": "Looks good"
    }
    
    safety = GitSafety(mock_git, mock_llm)
    
    release = {"feature": "Auth", "description": "Add login"}
    is_safe, reason = safety.check_unrelated_changes("+ login code", release)
    
    assert is_safe == True

def test_check_unrelated_changes_unsafe():
    mock_git = Mock()
    mock_llm = Mock()
    mock_llm.evaluate_diff.return_value = {
        "is_safe": False,
        "unrelated_changes_detected": True,
        "reasoning": "Unrelated payment code found"
    }
    
    safety = GitSafety(mock_git, mock_llm)
    
    release = {"feature": "Auth", "description": "Add login"}
    is_safe, reason = safety.check_unrelated_changes("+ login code + payment code", release)
    
    assert is_safe == False
    assert "Unrelated payment code found" in reason
