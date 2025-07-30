"""
Integration test for repository root behavior in main entry point.
"""
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from giv.main import main


class TestMainRepositoryBehavior:
    """Test main entry point repository validation behavior."""
    
    def test_main_exits_when_not_in_repository(self):
        """Test that main exits with error when not in a git repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Should exit with code 1 when not in a repository
                exit_code = main(["message", "--dry-run"])
                assert exit_code == 1
                
            finally:
                os.chdir(original_cwd)
    
    def test_main_changes_to_repo_root(self, git_repo):
        """Test that main changes to repository root."""
        # Create nested directory structure
        subdir = Path(git_repo) / "src" / "nested"
        subdir.mkdir(parents=True)
        
        # Configure git
        subprocess.run(["git", "config", "user.email", "test@example.com"], 
                     cwd=git_repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], 
                     cwd=git_repo, check=True)
        
        # Create and commit a file to have some changes
        test_file = Path(git_repo) / "test.txt"
        test_file.write_text("test content")
        subprocess.run(["git", "add", "test.txt"], cwd=git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], 
                     cwd=git_repo, check=True)
        
        # Modify file to have working tree changes
        test_file.write_text("modified content")
        
        original_cwd = os.getcwd()
        try:
            # Start from nested subdirectory
            os.chdir(subdir)
            assert Path.cwd().resolve() == subdir.resolve()  # Verify we're in subdirectory
            
            # Run giv command - should work and change to repo root
            exit_code = main(["--dry-run", "message"])
            
            # Should succeed (not exit with error)
            assert exit_code == 0
            
            # Should have changed to repository root
            assert Path.cwd().resolve() == Path(git_repo).resolve()
            
        finally:
            os.chdir(original_cwd)
    
    def test_main_skip_repo_validation_for_version_command(self):
        """Test that version command skips repository validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Version command should work even outside repository
                exit_code = main(["version"])
                assert exit_code == 0
                
            finally:
                os.chdir(original_cwd)
    
    def test_main_skip_repo_validation_for_help_command(self):
        """Test that help command skips repository validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Help command should work even outside repository
                exit_code = main(["help"])
                assert exit_code == 0
                
            finally:
                os.chdir(original_cwd)
