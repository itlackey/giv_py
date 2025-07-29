"""
Git repository operations and utilities.

This module provides comprehensive Git functionality that matches the Bash
implementation exactly, including:
- Advanced diff extraction with unified context
- Support for cached, current, and commit-specific diffs  
- Untracked file handling
- Commit metadata extraction
- Branch and tag operations
- Repository status information
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class GitRepository:
    """Interact with Git repositories and their history.
    
    This class provides a normalized interface to Git operations,
    replacing the original GitHistory class with more consistent naming.
    """

    def __init__(self, repo_path: Optional[Path] = None) -> None:
        """Initialize Git repository interface.
        
        Parameters
        ----------
        repo_path : Optional[Path]
            Path to the Git repository. Defaults to current working directory.
        """
        self.repo_path = repo_path or Path.cwd()

    def get_diff(self, revision: Optional[str] = None, paths: Optional[List[str]] = None, 
                 include_untracked: bool = True) -> str:
        """Return the diff for the given revision range or working tree.

        This method matches the Bash implementation's build_diff functionality,
        supporting cached, current, and commit-specific diffs with untracked files.

        Parameters
        ----------
        revision : Optional[str]
            A Git revision range (e.g. ``HEAD~1..HEAD``), single commit, 
            "--cached" for staged changes, "--current" or None for working tree.
        paths : Optional[List[str]]
            Optional list of paths to limit the diff to.  When provided, only
            matching files are included.
        include_untracked : bool
            Whether to include untracked files in the diff output.

        Returns
        -------
        str
            The textual diff, or an empty string if the command fails.
        """
        # Get the main diff
        diff_output = self._get_tracked_diff(revision, paths)
        
        # For --current revision, always include untracked files to match Bash behavior
        if revision == "--current" or (revision is None and include_untracked):
            untracked_diff = self._get_untracked_diff(paths)
            if diff_output and untracked_diff:
                diff_output = f"{diff_output}\n{untracked_diff}"
            elif untracked_diff:
                diff_output = untracked_diff
        
        return diff_output

    def _get_tracked_diff(self, revision: Optional[str] = None, paths: Optional[List[str]] = None) -> str:
        """Get diff for tracked files matching Bash get_diff function."""
        cmd = ["git", "--no-pager", "diff", "--unified=3", "--no-prefix", "--color=never"]
        
        # Handle special revision cases
        if revision == "--cached":
            cmd.append("--cached")
        elif revision == "--current" or revision is None:
            # Default behavior - diff working tree against HEAD
            pass
        else:
            # Check if it's a commit range (contains ..)
            if ".." in revision:
                cmd.append(revision)
            else:
                # Specific commit - show changes in that commit
                cmd.append(f"{revision}^!")
        
        # Add path specifications
        if paths:
            cmd.append("--")
            cmd.extend(paths)
        
        return self._run_git_diff_command(cmd)

    def _get_untracked_diff(self, paths: Optional[List[str]] = None) -> str:
        """Get diff for untracked files matching Bash untracked file handling."""
        # Get list of untracked files
        untracked_files = self.get_untracked_files()
        if not untracked_files:
            return ""
        
        # Filter by paths if specified
        if paths:
            filtered_files = []
            for file in untracked_files:
                for path_pattern in paths:
                    # Simple pattern matching - could be enhanced with fnmatch
                    if path_pattern in file or file.startswith(path_pattern):
                        filtered_files.append(file)
                        break
            untracked_files = filtered_files
        
        # Generate diffs for untracked files
        untracked_diffs = []
        for file in untracked_files:
            file_path = self.repo_path / file
            if not file_path.exists() or not file_path.is_file():
                continue
            
            # Use simpler diff command
            cmd = [
                "git", "--no-pager", "diff", "--no-prefix", "--unified=3", 
                "--no-color", "--no-index", "/dev/null", str(file_path)
            ]
            
            diff_output = self._run_git_diff_command(cmd)
            if diff_output:
                untracked_diffs.append(diff_output)
        
        return "\n".join(untracked_diffs)

    def get_untracked_files(self) -> List[str]:
        """Get list of untracked files."""
        cmd = ["git", "ls-files", "--others", "--exclude-standard"]
        output = self._run_git_command(cmd)
        return [line.strip() for line in output.splitlines() if line.strip()]

    def get_commit_date(self, commit: str = "HEAD") -> str:
        """Get the date of a commit, matching Bash get_commit_date functionality.
        
        Parameters
        ----------
        commit : str
            Commit hash, reference, or special values "--current", "--cached"
            
        Returns
        -------
        str
            Date in YYYY-MM-DD format
        """
        if commit in ("--current", "--cached"):
            return datetime.now().strftime("%Y-%m-%d")
        
        cmd = ["git", "show", "-s", "--format=%ci", commit]
        output = self._run_git_command(cmd)
        if output:
            # Extract date part (YYYY-MM-DD) from full timestamp
            return output.split()[0] if output.split() else ""
        return ""

    def get_commit_message(self, commit: str = "HEAD") -> str:
        """Get the commit message for a specific commit."""
        cmd = ["git", "show", "-s", "--format=%s", commit]
        return self._run_git_command(cmd).strip()

    def get_commit_message_body(self, commit: str = "HEAD") -> str:
        """Get the full commit message body for a specific commit."""
        cmd = ["git", "show", "-s", "--format=%B", commit]
        return self._run_git_command(cmd).strip()

    def get_commit_author(self, commit: str = "HEAD") -> str:
        """Get the author name for a specific commit."""
        cmd = ["git", "show", "-s", "--format=%an", commit]
        return self._run_git_command(cmd).strip()

    def get_commit_hash(self, commit: str = "HEAD") -> str:
        """Get the full SHA hash of a commit."""
        cmd = ["git", "rev-parse", commit]
        return self._run_git_command(cmd).strip()

    def get_short_commit_hash(self, commit: str = "HEAD") -> str:
        """Get the short SHA hash of a commit."""
        cmd = ["git", "rev-parse", "--short", commit]
        return self._run_git_command(cmd).strip()

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        cmd = ["git", "branch", "--show-current"]
        return self._run_git_command(cmd).strip()

    def get_repository_root(self) -> str:
        """Get the root directory of the Git repository."""
        cmd = ["git", "rev-parse", "--show-toplevel"]
        return self._run_git_command(cmd).strip()

    def is_repository(self) -> bool:
        """Check if the current directory is inside a Git repository."""
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        output = self._run_git_command(cmd).strip()
        return output == "true"

    def has_staged_changes(self) -> bool:
        """Check if there are staged changes."""
        cmd = ["git", "diff", "--cached", "--quiet"]
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return result.returncode != 0  # Non-zero means there are staged changes
        except FileNotFoundError:
            return False

    def has_unstaged_changes(self) -> bool:
        """Check if there are unstaged changes."""
        cmd = ["git", "diff", "--quiet"]
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return result.returncode != 0  # Non-zero means there are unstaged changes
        except FileNotFoundError:
            return False

    def get_tags(self, pattern: Optional[str] = None) -> List[str]:
        """Get list of tags, optionally filtered by pattern."""
        cmd = ["git", "tag"]
        if pattern:
            cmd.extend(["-l", pattern])
        output = self._run_git_command(cmd)
        return [line.strip() for line in output.splitlines() if line.strip()]

    def build_history_metadata(self, commit: str = "HEAD") -> Dict[str, str]:
        """Build commit metadata dictionary matching Bash print_commit_metadata.
        
        Parameters
        ----------
        commit : str
            Commit reference to get metadata for
            
        Returns
        -------
        Dict[str, str]
            Dictionary with keys: commit_id, date, message, project_title, version
        """
        return {
            "commit_id": self.get_commit_hash(commit),
            "short_commit_id": self.get_short_commit_hash(commit),
            "date": self.get_commit_date(commit),
            "message": self.get_commit_message(commit),
            "message_body": self.get_commit_message_body(commit),
            "author": self.get_commit_author(commit),
            "branch": self.get_current_branch(),
        }

    def get_log(self, revision: Optional[str] = None, paths: Optional[List[str]] = None, 
                pretty: str = "oneline", max_count: Optional[int] = None) -> str:
        """Return the git log for the given range.

        Enhanced version with more options to match Bash functionality.
        
        Parameters
        ----------
        revision : Optional[str]
            Revision range to get log for
        paths : Optional[List[str]]
            Paths to limit log to
        pretty : str
            Format for log output
        max_count : Optional[int]
            Maximum number of commits to return
            
        Returns
        -------
        str
            Git log output
        """
        cmd: List[str] = ["git", "log"]
        if max_count is not None:
            cmd.extend(["-n", str(max_count)])
        if revision:
            cmd.append(revision)
        if paths:
            cmd.append("--")
            cmd.extend(paths)
        # Use a simple format by default
        cmd.extend(["--pretty", pretty])
        
        return self._run_git_command(cmd)

    def _run_git_command(self, cmd: List[str]) -> str:
        """Run a git command and return output, with proper error handling."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                logger.debug("Git command failed: %s, stderr: %s", " ".join(cmd), result.stderr.strip())
                return ""
            return result.stdout
        except FileNotFoundError:
            # Git is not installed
            logger.debug("git executable not found")
            return ""

    def _run_git_diff_command(self, cmd: List[str]) -> str:
        """Run a git diff command with proper exit code handling.
        
        git diff commands return exit code 1 when there are differences,
        which is normal and should not be treated as an error.
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            # git diff returns 0=no differences, 1=differences found, 2+=error
            if result.returncode in (0, 1):
                return result.stdout
            else:
                logger.debug("Git diff command failed: %s, stderr: %s", " ".join(cmd), result.stderr.strip())
                return ""
        except FileNotFoundError:
            # Git is not installed
            logger.debug("git executable not found")
            return ""

    def get_cache_path(self, commit: str, cache_type: str = "summary") -> Path:
        """Get the cache file path for a commit.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
        cache_type : str
            Type of cache (summary, history)
            
        Returns
        -------
        Path
            Path to the cache file
        """
        giv_home = Path.cwd() / ".giv"
        cache_dir = giv_home / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{commit}-{cache_type}.md"

    def get_cached_summary(self, commit: str) -> Optional[str]:
        """Get cached summary for a commit if it exists.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
            
        Returns
        -------
        Optional[str]
            Cached summary content, or None if not cached
        """
        cache_path = self.get_cache_path(commit, "summary")
        if cache_path.exists():
            try:
                content = cache_path.read_text(encoding='utf-8')
                # Verify cache has proper metadata format
                if content.startswith("Commit:"):
                    logger.debug(f"Cache hit for commit: {commit}")
                    return content
                else:
                    logger.debug(f"Cache exists but lacks metadata, removing: {cache_path}")
                    cache_path.unlink()
            except (OSError, IOError) as e:
                logger.warning(f"Failed to read cache file {cache_path}: {e}")
        return None

    def cache_summary(self, commit: str, summary: str) -> None:
        """Cache a summary for a commit.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
        summary : str
            Summary content to cache
        """
        cache_path = self.get_cache_path(commit, "summary")
        try:
            cache_path.write_text(summary, encoding='utf-8')
            logger.debug(f"Cached summary for commit {commit} at {cache_path}")
        except (OSError, IOError) as e:
            logger.warning(f"Failed to cache summary for {commit}: {e}")

    def build_commit_history(self, commit: str, pathspec: Optional[List[str]] = None) -> str:
        """Build detailed history for a single commit in Markdown format.
        
        This matches the build_history function from the shell implementation.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference  
        pathspec : Optional[List[str]]
            Optional path specifications to limit analysis
            
        Returns
        -------
        str
            Formatted commit history in Markdown
        """
        # Check for cached history
        history_cache = self.get_cache_path(commit, "history")
        if history_cache.exists():
            try:
                return history_cache.read_text(encoding='utf-8')
            except (OSError, IOError):
                pass  # Continue to regenerate if cache read fails

        # Build history content
        history_parts = []
        
        # Commit header
        history_parts.append(f"### Commit ID {commit}")
        history_parts.append(f"**Date:** {self.get_commit_date(commit)}")
        
        # Version if available
        from .metadata import ProjectMetadata
        try:
            version = ProjectMetadata.get_version(commit)
            if version and version != "unknown":
                history_parts.append(f"**Version:** {version}")
        except Exception:
            pass  # Version detection failed, continue without it
        
        # Commit message
        message = self.get_commit_message(commit) or "No commit message"
        history_parts.append(f"**Message:** {message}")
        
        # Get diff content
        diff_content = self.get_diff(commit, pathspec)
        if diff_content.strip():
            # Get diff stats if available
            diff_stats = self._get_diff_stats(commit, pathspec)
            if diff_stats:
                history_parts.append(f"```diff\n{diff_content}\n{diff_stats}\n```")
            else:
                history_parts.append(f"```diff\n{diff_content}\n```")
        
        # TODO: Add TODO changes extraction if needed
        # This would require implementing extract_todo_changes equivalent
        
        history_content = "\n".join(history_parts)
        
        # Cache the history
        try:
            history_cache.write_text(history_content, encoding='utf-8')
        except (OSError, IOError) as e:
            logger.warning(f"Failed to cache history for {commit}: {e}")
        
        return history_content

    def _get_diff_stats(self, commit: str, pathspec: Optional[List[str]] = None) -> str:
        """Get diff statistics for a commit.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
        pathspec : Optional[List[str]]
            Optional path specifications
            
        Returns
        -------
        str
            Diff statistics output
        """
        cmd = ["git", "--no-pager", "diff", "--stat"]
        
        if commit == "--cached":
            cmd.append("--cached")
        elif commit == "--current" or commit == "":
            pass  # No additional args for current changes
        else:
            cmd.append(f"{commit}^!")
        
        if pathspec:
            cmd.append("--")
            cmd.extend(pathspec)
        
        return self._run_git_command(cmd).strip()

    def parse_commit_list(self, revision: str) -> List[str]:
        """Parse a revision specification into a list of commits.
        
        Handles ranges like HEAD~3..HEAD, single commits, and special revisions.
        
        Parameters  
        ----------
        revision : str
            Git revision specification
            
        Returns
        -------
        List[str]
            List of commit hashes or special revision names
        """
        # Handle special revisions
        if revision in ("--current", "--cached", ""):
            return [revision or "--current"]
        
        # Handle commit ranges
        if ".." in revision:
            if "..." in revision:
                # Three-dot range (symmetric difference)
                left, right = revision.split("...", 1)
            else:
                # Two-dot range (commits reachable from right but not left)
                left, right = revision.split("..", 1)
            
            # Validate both endpoints
            for endpoint in [left, right]:
                if not self._is_valid_commit(endpoint):
                    raise ValueError(f"Invalid commit in range: {endpoint}")
            
            # Get commit list for the range
            cmd = ["git", "rev-list", "--reverse", revision]
            output = self._run_git_command(cmd).strip()
            if output:
                commits = output.split('\n')
                # For ranges, also include the left endpoint if it's not included
                if left not in commits and self._is_valid_commit(left):
                    commits.insert(0, left)
                return commits
            else:
                return []
        
        # Single commit
        if self._is_valid_commit(revision):
            return [revision]
        else:
            raise ValueError(f"Invalid revision: {revision}")

    def _is_valid_commit(self, commit: str) -> bool:
        """Check if a commit reference is valid.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
            
        Returns
        -------
        bool
            True if commit is valid
        """
        if commit in ("--current", "--cached"):
            return True
        
        cmd = ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"]
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return result.returncode == 0


# Backward compatibility alias
GitHistory = GitRepository