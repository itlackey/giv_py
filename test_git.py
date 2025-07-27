#!/usr/bin/env python3
"""
Simple test script to verify enhanced git functionality.
"""
import sys
from pathlib import Path

# Add the giv_cli package to Python path
sys.path.insert(0, str(Path(__file__).parent / "giv_cli"))

from git_utils import GitHistory

def test_git_functionality():
    """Test enhanced git functionality."""
    print("Testing Enhanced Git Integration...")
    
    git = GitHistory()
    
    # Test repository detection
    is_repo = git.is_repository()
    print(f"Is Git Repository: {is_repo}")
    
    if not is_repo:
        print("Not in a Git repository - skipping git-specific tests")
        return True
    
    # Test basic metadata
    try:
        current_branch = git.get_current_branch()
        print(f"Current Branch: {current_branch}")
        
        commit_hash = git.get_commit_hash()
        short_hash = git.get_short_commit_hash()
        print(f"Latest Commit: {short_hash} ({commit_hash})")
        
        commit_date = git.get_commit_date()
        print(f"Latest Commit Date: {commit_date}")
        
        commit_message = git.get_commit_message()
        print(f"Latest Commit Message: {commit_message}")
        
    except Exception as e:
        print(f"Error getting git metadata: {e}")
        return False
    
    # Test status checks
    try:
        has_staged = git.has_staged_changes()
        has_unstaged = git.has_unstaged_changes()
        print(f"Has Staged Changes: {has_staged}")
        print(f"Has Unstaged Changes: {has_unstaged}")
        
        untracked = git.get_untracked_files()
        print(f"Untracked Files: {len(untracked)}")
        if untracked and len(untracked) <= 5:
            for file in untracked:
                print(f"  - {file}")
        elif len(untracked) > 5:
            print(f"  - {untracked[0]} (and {len(untracked)-1} more)")
        
    except Exception as e:
        print(f"Error checking git status: {e}")
        return False
    
    # Test metadata dictionary
    try:
        metadata = git.build_history_metadata()
        print(f"\nHistory Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error building history metadata: {e}")
        return False
    
    # Test diff functionality
    try:
        diff = git.get_diff()
        print(f"\nCurrent Diff: {len(diff)} characters")
        if diff:
            lines = diff.splitlines()
            print(f"Diff has {len(lines)} lines")
            # Show first few lines
            for i, line in enumerate(lines[:5]):
                print(f"  {i+1}: {line[:80]}...")
        else:
            print("No current changes")
            
    except Exception as e:
        print(f"Error getting diff: {e}")
        return False
    
    print("\n✅ Enhanced Git Integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_git_functionality()
    sys.exit(0 if success else 1)
