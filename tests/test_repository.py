"""
Tests for repository root detection and validation functionality.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from giv.lib.repository import (
    RepositoryError,
    find_repository_root,
    is_git_repository,
    validate_and_change_to_repo_root,
    get_repository_info
)


class TestRepositoryDetection:
    """Test Git repository detection and root finding."""
    
    def test_find_repository_root_in_git_repo(self, git_repo):
        """Test finding repository root from within a git repository."""
        # Change to the git repository
        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            repo_root = find_repository_root()
            assert repo_root == Path(git_repo).resolve()
        finally:
            os.chdir(original_cwd)
    
    def test_find_repository_root_in_subdirectory(self, git_repo):
        """Test finding repository root from a subdirectory."""
        # Create a subdirectory
        subdir = Path(git_repo) / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            repo_root = find_repository_root()
            assert repo_root == Path(git_repo).resolve()
        finally:
            os.chdir(original_cwd)
    
    def test_find_repository_root_not_in_repo(self, temp_dir):
        """Test finding repository root when not in a git repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with pytest.raises(RepositoryError, match="Not in a Git repository"):
                find_repository_root()
        finally:
            os.chdir(original_cwd)
    
    def test_find_repository_root_git_not_found(self, git_repo):
        """Test handling when git command is not found."""
        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            with patch('subprocess.run', side_effect=FileNotFoundError("git not found")):
                with pytest.raises(RepositoryError, match="Git command not found"):
                    find_repository_root()
        finally:
            os.chdir(original_cwd)


class TestRepositoryValidation:
    """Test repository validation functionality."""
    
    def test_is_git_repository_true(self, git_repo):
        """Test is_git_repository returns True for git repository."""
        assert is_git_repository(Path(git_repo)) is True
    
    def test_is_git_repository_false(self, temp_dir):
        """Test is_git_repository returns False for non-git directory."""
        assert is_git_repository(Path(temp_dir)) is False
    
    def test_is_git_repository_git_not_found(self, git_repo):
        """Test is_git_repository handles missing git command."""
        with patch('subprocess.run', side_effect=FileNotFoundError("git not found")):
            assert is_git_repository(Path(git_repo)) is False
    
    def test_validate_and_change_to_repo_root_success(self, git_repo):
        """Test successful validation and directory change."""
        # Create a subdirectory to start from
        subdir = Path(git_repo) / "test_subdir"
        subdir.mkdir()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            
            # Should change to repository root
            repo_root = validate_and_change_to_repo_root()
            
            # Verify we're now in the repository root
            assert repo_root == Path(git_repo).resolve()
            assert Path.cwd().resolve() == Path(git_repo).resolve()
            
        finally:
            os.chdir(original_cwd)
    
    def test_validate_and_change_to_repo_root_not_in_repo(self, temp_dir):
        """Test validation failure when not in a git repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Should exit with code 1
            with pytest.raises(SystemExit) as exc_info:
                validate_and_change_to_repo_root()
            
            assert exc_info.value.code == 1
            
        finally:
            os.chdir(original_cwd)


class TestRepositoryInfo:
    """Test repository information gathering."""
    
    def test_get_repository_info_success(self, git_repo):
        """Test getting repository information."""
        original_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            
            # Create a commit to have a proper branch
            subprocess.run(["git", "config", "user.email", "test@example.com"], 
                         cwd=git_repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], 
                         cwd=git_repo, check=True)
            
            # Add a file and commit
            test_file = Path(git_repo) / "test.txt"
            test_file.write_text("test content")
            subprocess.run(["git", "add", "test.txt"], cwd=git_repo, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], 
                         cwd=git_repo, check=True)
            
            info = get_repository_info()
            
            assert "root" in info
            assert info["root"] == str(Path(git_repo).resolve())
            assert "branch" in info
            # Default branch could be 'main' or 'master' depending on git config
            assert info["branch"] in ["main", "master"]
            
        finally:
            os.chdir(original_cwd)
    
    def test_get_repository_info_not_in_repo(self, temp_dir):
        """Test getting repository info when not in a repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            info = get_repository_info()
            # Should return empty dict or minimal info
            assert isinstance(info, dict)
        finally:
            os.chdir(original_cwd)


class TestRepositoryIntegration:
    """Integration tests for repository functionality."""
    
    def test_repository_detection_with_nested_structure(self):
        """Test repository detection in a realistic nested project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Initialize git repository
            subprocess.run(["git", "init"], cwd=repo_root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], 
                         cwd=repo_root, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], 
                         cwd=repo_root, check=True)
            
            # Create nested directory structure
            nested_dir = repo_root / "src" / "giv" / "commands"
            nested_dir.mkdir(parents=True)
            
            original_cwd = os.getcwd()
            try:
                # Test from nested directory
                os.chdir(nested_dir)
                
                assert is_git_repository() is True
                repo_root_found = find_repository_root()
                assert repo_root_found == repo_root.resolve()
                
                # Test validate_and_change_to_repo_root
                validate_and_change_to_repo_root()
                assert Path.cwd().resolve() == repo_root.resolve()
                
            finally:
                os.chdir(original_cwd)
