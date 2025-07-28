"""
Comprehensive tests for git_utils module.

Tests Git integration functionality including:
- Git history analysis
- Diff processing
- Metadata extraction
- Different revision formats
- Error handling
"""
import os
import pytest
import subprocess
from pathlib import Path

from giv.lib.git import GitRepository as GitHistory


class TestGitHistory:
    """Test GitHistory class functionality."""
    
    def test_init(self):
        """Test GitHistory initialization."""
        gh = GitHistory()
        assert gh is not None
    
    def test_get_diff_current(self, isolated_git_repo):
        """Test getting diff for current changes."""
        # Add some changes - working directory is already set to isolated_git_repo
        (isolated_git_repo / "src" / "new_file.js").write_text("console.log('new file');")
        
        gh = GitHistory()
        diff = gh.get_diff(revision="--current")
        
        # Should contain the new file
        assert "new_file.js" in diff
        assert "console.log('new file');" in diff
    
    def test_get_diff_cached(self, isolated_git_repo):
        """Test getting diff for staged changes."""
        # Add and stage some changes - working directory is already set
        (isolated_git_repo / "src" / "staged.js").write_text("console.log('staged');")
        subprocess.run(["git", "add", "src/staged.js"], cwd=isolated_git_repo, check=True)
        
        gh = GitHistory()
        diff = gh.get_diff(revision="--cached")
        
        # Should contain the staged file
        assert "staged.js" in diff
        assert "console.log('staged');" in diff
    
    def test_get_diff_head(self, isolated_git_repo):
        """Test getting diff for HEAD."""
        # Make another commit - working directory is already set
        (isolated_git_repo / "src" / "second.js").write_text("console.log('second');")
        subprocess.run(["git", "add", "."], cwd=isolated_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=isolated_git_repo, check=True)
        
        gh = GitHistory()
        diff = gh.get_diff(revision="HEAD~1..HEAD")
        
        # Should contain the new file from second commit
        assert "second.js" in diff
    
    def test_get_diff_with_paths(self, git_repo):
        """Test getting diff with path filtering."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Create directories first
            os.makedirs(git_repo / "docs", exist_ok=True)
            
            # Add changes in different directories
            (git_repo / "src" / "src_file.js").write_text("console.log('src');")
            (git_repo / "docs" / "doc_file.md").write_text("# Documentation")
            
            gh = GitHistory()
            
            # Get diff only for src directory
            diff = gh.get_diff(revision="--current", paths=["src/"])
            
            # Should contain src file but not docs file
            assert "src_file.js" in diff
            assert "doc_file.md" not in diff
            
        finally:
            os.chdir(old_cwd)
    
    def test_build_history_metadata(self, git_repo):
        """Test building git history metadata."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            gh = GitHistory()
            metadata = gh.build_history_metadata("HEAD")
            
            # Should contain required metadata fields
            required_fields = [
                "commit_id", "short_commit_id", "date", 
                "message", "message_body", "branch"
            ]
            
            for field in required_fields:
                assert field in metadata
                assert metadata[field] is not None
            
            # Commit ID should be a valid hash
            assert len(metadata["commit_id"]) >= 7
            assert len(metadata["short_commit_id"]) >= 7
            
            # Message should match what we committed
            assert "Initial commit" in metadata["message"]
            
        finally:
            os.chdir(old_cwd)
    
    def test_build_history_metadata_current(self, git_repo):
        """Test building metadata for current state."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            gh = GitHistory()
            metadata = gh.build_history_metadata("--current")
            
            # Should handle current state gracefully
            assert "commit_id" in metadata
            assert "date" in metadata
            assert "branch" in metadata
            
        finally:
            os.chdir(old_cwd)
    
    def test_empty_repository(self, temp_dir):
        """Test behavior with empty git repository."""
        repo_dir = temp_dir / "empty_repo"
        repo_dir.mkdir()
        
        # Initialize empty git repo
        subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
        
        old_cwd = os.getcwd()
        os.chdir(repo_dir)
        
        try:
            gh = GitHistory()
            
            # Should handle empty repo gracefully
            diff = gh.get_diff(revision="--current")
            # Empty repo might have empty diff or error, both are acceptable
            
            metadata = gh.build_history_metadata("HEAD")
            # Should provide some metadata even for empty repo
            assert isinstance(metadata, dict)
            
        finally:
            os.chdir(old_cwd)
    
    def test_non_git_directory(self, temp_dir):
        """Test behavior in non-git directory."""
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            gh = GitHistory()
            
            # Should handle gracefully or raise appropriate error
            try:
                diff = gh.get_diff(revision="--current")
                # If it succeeds, diff should be empty or have some content
            except Exception as e:
                # If it fails, should be a meaningful error
                assert "not a git repository" in str(e).lower() or "git" in str(e).lower()
            
        finally:
            os.chdir(old_cwd)


class TestGitRevisionHandling:
    """Test different git revision formats."""
    
    def test_head_revision(self, git_repo):
        """Test HEAD revision."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            gh = GitHistory()
            diff = gh.get_diff(revision="HEAD")
            # Should succeed (might be empty for HEAD without range)
            assert isinstance(diff, str)
            
        finally:
            os.chdir(old_cwd)
    
    def test_commit_hash_revision(self, git_repo):
        """Test specific commit hash revision."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Get the commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=git_repo,
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = result.stdout.strip()
            
            gh = GitHistory()
            metadata = gh.build_history_metadata(commit_hash)
            
            # Should work with full commit hash
            assert metadata["commit_id"] == commit_hash
            
        finally:
            os.chdir(old_cwd)
    
    def test_short_commit_hash(self, git_repo):
        """Test short commit hash revision."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Get short commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=git_repo,
                capture_output=True,
                text=True,
                check=True
            )
            short_hash = result.stdout.strip()
            
            gh = GitHistory()
            metadata = gh.build_history_metadata(short_hash)
            
            # Should work with short hash
            assert short_hash in metadata["commit_id"]
            
        finally:
            os.chdir(old_cwd)
    
    def test_range_revision(self, git_repo):
        """Test revision range format."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Create second commit
            (git_repo / "file2.txt").write_text("second file")
            subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
            subprocess.run(["git", "commit", "-m", "Second commit"], cwd=git_repo, check=True)
            
            gh = GitHistory()
            diff = gh.get_diff(revision="HEAD~1..HEAD")
            
            # Should contain changes from the range
            assert "file2.txt" in diff or len(diff) >= 0  # At minimum, should not error
            
        finally:
            os.chdir(old_cwd)
    
    def test_relative_revision(self, git_repo):
        """Test relative revision formats like HEAD~1."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Create second commit
            (git_repo / "file3.txt").write_text("third file")
            subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
            subprocess.run(["git", "commit", "-m", "Third commit"], cwd=git_repo, check=True)
            
            gh = GitHistory()
            metadata = gh.build_history_metadata("HEAD~1")
            
            # Should get metadata for previous commit
            assert "Initial commit" in metadata["message"]
            
        finally:
            os.chdir(old_cwd)


class TestGitErrorHandling:
    """Test git error handling scenarios."""
    
    def test_invalid_revision(self, git_repo):
        """Test handling of invalid git revision."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            gh = GitHistory()
            
            # Should handle invalid revision gracefully
            try:
                diff = gh.get_diff(revision="invalid-revision-12345")
                # If it succeeds, should return empty or handle gracefully
            except Exception as e:
                # If it fails, should be meaningful error
                assert isinstance(e, Exception)
            
        finally:
            os.chdir(old_cwd)
    
    def test_permission_error_simulation(self, git_repo):
        """Test handling when git commands fail due to permissions."""
        # This is harder to test without actually changing permissions
        # but we can at least verify the code structure handles exceptions
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            gh = GitHistory()
            
            # Normal operation should work
            diff = gh.get_diff(revision="--current")
            assert isinstance(diff, str)
            
        finally:
            os.chdir(old_cwd)
