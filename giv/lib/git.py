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
import time
import weakref
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@contextmanager
def performance_timer(operation: str, threshold_ms: float = 100) -> Generator[None, None, None]:
    """Context manager for performance monitoring.
    
    Logs operations that take longer than the threshold.
    
    Parameters
    ----------
    operation : str
        Name of the operation being timed
    threshold_ms : float
        Threshold in milliseconds above which to log warnings
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        if duration_ms > threshold_ms:
            logger.warning(f"Slow operation: {operation} took {duration_ms:.1f}ms")
        else:
            logger.debug(f"Performance: {operation} took {duration_ms:.1f}ms")


class PerformanceMetrics:
    """Simple performance metrics collection."""
    
    def __init__(self):
        self.metrics = {}
        self.call_counts = {}
    
    def record_duration(self, operation: str, duration_ms: float) -> None:
        """Record operation duration."""
        if operation not in self.metrics:
            self.metrics[operation] = []
            self.call_counts[operation] = 0
        
        self.metrics[operation].append(duration_ms)
        self.call_counts[operation] += 1
        
        # Keep only last 100 measurements to prevent memory growth
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        durations = self.metrics[operation]
        return {
            'count': self.call_counts[operation],
            'avg_ms': sum(durations) / len(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'recent_avg_ms': sum(durations[-10:]) / min(len(durations), 10)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get all performance statistics."""
        return {op: self.get_stats(op) for op in self.metrics.keys()}
    
    def clear(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.call_counts.clear()


class LimitedCache:
    """Memory-efficient cache with size and TTL limits."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """Initialize cache with size and time limits.
        
        Parameters
        ----------
        max_size : int
            Maximum number of cached items
        ttl_seconds : int
            Time-to-live for cached items in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}
        self._access_times = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get cached value if exists and not expired."""
        if key not in self._cache:
            return None
        
        # Check TTL
        current_time = time.time()
        if current_time - self._access_times[key] > self.ttl_seconds:
            # Expired, remove it
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
            return None
        
        # Update access time
        self._access_times[key] = current_time
        return self._cache[key]
    
    def set(self, key: str, value: str) -> None:
        """Set cached value, managing size limits."""
        current_time = time.time()
        
        # If at capacity, remove oldest items
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove oldest item
            oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            self._cache.pop(oldest_key, None)
            self._access_times.pop(oldest_key, None)
        
        self._cache[key] = value
        self._access_times[key] = current_time
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._access_times.clear()


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
        
        # Initialize memory-efficient caches
        self._diff_cache = LimitedCache(max_size=50, ttl_seconds=300)  # 5 min TTL
        self._metadata_cache = LimitedCache(max_size=200, ttl_seconds=600)  # 10 min TTL
        
        # Initialize performance metrics
        self._performance_metrics = PerformanceMetrics()

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
        # Create cache key for this diff request
        cache_key = f"{revision or 'current'}_{str(paths)}_{include_untracked}"
        
        # Check cache first for non-current revisions (current can change)
        if revision not in (None, "--current"):
            cached_diff = self._diff_cache.get(cache_key)
            if cached_diff is not None:
                return cached_diff
        
        # Get the main diff
        diff_output = self._get_tracked_diff(revision, paths)
        
        # For --current revision, always include untracked files to match Bash behavior
        if revision == "--current" or (revision is None and include_untracked):
            untracked_diff = self._get_untracked_diff(paths)
            if diff_output and untracked_diff:
                diff_output = f"{diff_output}\n{untracked_diff}"
            elif untracked_diff:
                diff_output = untracked_diff
        
        # Cache the result for non-current revisions
        if revision not in (None, "--current"):
            self._diff_cache.set(cache_key, diff_output)
        
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
    
    def get_diff_streaming(self, revision: Optional[str] = None, paths: Optional[List[str]] = None, 
                          include_untracked: bool = True, max_size_mb: int = 10):
        """Stream large diffs to avoid memory issues.
        
        For diffs larger than max_size_mb, this method yields chunks instead
        of loading the entire diff into memory.
        
        Parameters
        ----------
        revision : Optional[str]
            Git revision specification
        paths : Optional[List[str]]
            Path specifications to limit diff
        include_untracked : bool
            Whether to include untracked files
        max_size_mb : int
            Maximum size in MB before streaming
            
        Yields
        ------
        str
            Diff content chunks
        """
        import io
        
        # Build command for tracked diff
        cmd = ["git", "--no-pager", "diff", "--unified=3", "--no-prefix", "--color=never"]
        
        if revision == "--cached":
            cmd.append("--cached")
        elif revision == "--current" or revision is None:
            pass
        else:
            if ".." in revision:
                cmd.append(revision)
            else:
                cmd.append(f"{revision}^!")
        
        if paths:
            cmd.append("--")
            cmd.extend(paths)
        
        # Stream the diff output
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Read in chunks to avoid memory issues
            chunk_size = 8192  # 8KB chunks
            total_size = 0
            max_bytes = max_size_mb * 1024 * 1024
            
            while True:
                chunk = process.stdout.read(chunk_size)
                if not chunk:
                    break
                
                total_size += len(chunk.encode('utf-8'))
                if total_size > max_bytes:
                    logger.warning(f"Diff size exceeded {max_size_mb}MB, truncating")
                    yield chunk
                    yield "\n\n[... diff truncated due to size limit ...]\n"
                    break
                
                yield chunk
            
            process.wait()
            
        except Exception as e:
            logger.error(f"Streaming diff failed: {e}")
            # Fallback to regular diff
            yield self.get_diff(revision, paths, include_untracked)

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
        
        This optimized version uses batched Git commands to reduce subprocess overhead
        from 6+ individual calls to 2 batched calls.
        
        Parameters
        ----------
        commit : str
            Commit reference to get metadata for
            
        Returns
        -------
        Dict[str, str]
            Dictionary with keys: commit_id, date, message, project_title, version
        """
        try:
            # Use optimized batch command for commit-specific metadata
            batch_commands = [
                ["git", "show", "-s", "--format=%H", commit],       # commit_id
                ["git", "show", "-s", "--format=%h", commit],       # short_commit_id  
                ["git", "show", "-s", "--format=%ci", commit],      # date
                ["git", "show", "-s", "--format=%s", commit],       # message
                ["git", "show", "-s", "--format=%B", commit],       # message_body
                ["git", "show", "-s", "--format=%an", commit],      # author
                ["git", "branch", "--show-current"]                 # branch
            ]
            
            # Execute batch command
            results = self.batch_git_commands(batch_commands)
            
            # Extract date (YYYY-MM-DD format)
            date_str = results[2].split()[0] if results[2].split() else ""
            
            return {
                "commit_id": results[0].strip(),
                "short_commit_id": results[1].strip(),
                "date": date_str,
                "message": results[3].strip(),
                "message_body": results[4].strip(),
                "author": results[5].strip(),
                "branch": results[6].strip(),
            }
        except Exception as e:
            logger.warning(f"Batch metadata failed for {commit}, falling back to individual calls: {e}")
            # Fallback to original implementation
            return {
                "commit_id": self.get_commit_hash(commit),
                "short_commit_id": self.get_short_commit_hash(commit),
                "date": self.get_commit_date(commit),
                "message": self.get_commit_message(commit),
                "message_body": self.get_commit_message_body(commit),
                "author": self.get_commit_author(commit),
                "branch": self.get_current_branch(),
            }
    
    def build_batch_metadata(self, commits: List[str]) -> Dict[str, Dict[str, str]]:
        """Build metadata for multiple commits in a single batch operation.
        
        This method provides significant performance improvements when processing
        multiple commits by reducing subprocess overhead from N*6 calls to 2 calls.
        
        Parameters
        ----------
        commits : List[str]
            List of commit references
            
        Returns
        -------
        Dict[str, Dict[str, str]]
            Dictionary mapping commit -> metadata dict
        """
        if not commits:
            return {}
        
        try:
            # Build batch commands for all commits
            batch_commands = []
            
            # Get branch once (same for all commits)
            batch_commands.append(["git", "branch", "--show-current"])
            
            # Add commit-specific commands
            for commit in commits:
                batch_commands.extend([
                    ["git", "show", "-s", "--format=%H", commit],       # commit_id
                    ["git", "show", "-s", "--format=%h", commit],       # short_commit_id
                    ["git", "show", "-s", "--format=%ci", commit],      # date
                    ["git", "show", "-s", "--format=%s", commit],       # message
                    ["git", "show", "-s", "--format=%B", commit],       # message_body
                    ["git", "show", "-s", "--format=%an", commit],      # author
                ])
            
            # Execute all commands in one batch
            results = self.batch_git_commands(batch_commands)
            
            # Parse results
            branch = results[0].strip()
            metadata = {}
            
            # Process results for each commit (6 results per commit + 1 branch)
            for i, commit in enumerate(commits):
                start_idx = 1 + (i * 6)  # Skip branch result, then 6 results per commit
                
                # Extract date (YYYY-MM-DD format)
                date_str = results[start_idx + 2].split()[0] if results[start_idx + 2].split() else ""
                
                metadata[commit] = {
                    "commit_id": results[start_idx].strip(),
                    "short_commit_id": results[start_idx + 1].strip(),
                    "date": date_str,
                    "message": results[start_idx + 3].strip(),
                    "message_body": results[start_idx + 4].strip(),
                    "author": results[start_idx + 5].strip(),
                    "branch": branch,
                }
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Batch metadata failed, falling back to individual calls: {e}")
            # Fallback to individual calls
            metadata = {}
            for commit in commits:
                metadata[commit] = self.build_history_metadata(commit)
            return metadata

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
    
    def batch_git_commands(self, commands: List[List[str]]) -> List[str]:
        """Execute multiple Git commands efficiently in batch.
        
        This method reduces subprocess overhead by executing multiple Git
        commands in a single batch operation when possible.
        
        Parameters
        ----------
        commands : List[List[str]]
            List of Git command lists to execute
            
        Returns
        -------
        List[str]
            List of command outputs in the same order as input commands
        
        Examples
        --------
        >>> git = GitRepository()
        >>> commands = [
        ...     ["git", "rev-parse", "HEAD"],
        ...     ["git", "log", "--oneline", "-1"],
        ...     ["git", "status", "--porcelain"]
        ... ]
        >>> results = git.batch_git_commands(commands)
        """
        if not commands:
            return []
        
        # For now, implement simple batching by grouping compatible commands
        # Future optimization: Use git's built-in batch mode or persistent process
        results = []
        
        try:
            # Group read-only commands that can be batched
            read_only_commands = []
            other_commands = []
            
            for i, cmd in enumerate(commands):
                if self._is_read_only_command(cmd):
                    read_only_commands.append((i, cmd))
                else:
                    other_commands.append((i, cmd))
            
            # Execute read-only commands in batch when possible
            if read_only_commands:
                batch_results = self._execute_batch_read_only(read_only_commands)
                for (original_idx, _), result in zip(read_only_commands, batch_results):
                    results.extend([(original_idx, result)])
            
            # Execute other commands individually
            for original_idx, cmd in other_commands:
                result = self._run_git_command(cmd)
                results.append((original_idx, result))
            
            # Sort results by original order and extract values
            results.sort(key=lambda x: x[0])
            return [result for _, result in results]
            
        except Exception as e:
            logger.warning(f"Batch command execution failed: {e}")
            # Fallback to individual execution
            return [self._run_git_command(cmd) for cmd in commands]
    
    def _is_read_only_command(self, cmd: List[str]) -> bool:
        """Check if a Git command is read-only and safe for batching."""
        if len(cmd) < 2:
            return False
        
        read_only_ops = {
            'rev-parse', 'log', 'show', 'diff', 'status', 'ls-files',
            'branch', 'tag', 'remote', 'config', 'ls-tree', 'cat-file'
        }
        
        git_op = cmd[1] if cmd[0] == 'git' else cmd[0]
        return git_op in read_only_ops
    
    def _execute_batch_read_only(self, indexed_commands: List[tuple]) -> List[str]:
        """Execute multiple read-only commands efficiently."""
        results = []
        
        # Group commands by type for potential optimization
        commit_info_commands = []
        other_commands = []
        
        for idx_cmd in indexed_commands:
            _, cmd = idx_cmd
            if len(cmd) >= 3 and cmd[1] in ('show', 'rev-parse') and self._is_commit_info_command(cmd):
                commit_info_commands.append(idx_cmd)
            else:
                other_commands.append(idx_cmd)
        
        # Execute commit info commands in optimized batch
        if commit_info_commands:
            batch_results = self._execute_commit_info_batch(commit_info_commands)
            results.extend(batch_results)
        
        # Execute other commands individually
        for _, cmd in other_commands:
            result = self._run_git_command(cmd)
            results.append(result)
        
        return results

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
        
        # Get diff content with memory management
        diff_content = self._get_diff_for_history(commit, pathspec)
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

    def _is_commit_info_command(self, cmd: List[str]) -> bool:
        """Check if command is requesting commit information that can be batched."""
        if len(cmd) < 3:
            return False
        
        # Git show commands for commit info
        if cmd[1] == 'show' and '-s' in cmd and '--format=' in ' '.join(cmd):
            return True
        
        # Git rev-parse commands for commit hashes
        if cmd[1] == 'rev-parse' and any(arg for arg in cmd[2:] if not arg.startswith('-')):
            return True
        
        return False
    
    def _execute_commit_info_batch(self, indexed_commands: List[tuple]) -> List[str]:
        """Execute commit info commands in optimized batch."""
        results = []
        
        # Group by commit reference to maximize batching efficiency
        commit_groups = {}
        for idx_cmd in indexed_commands:
            _, cmd = idx_cmd
            commit_ref = self._extract_commit_ref(cmd)
            if commit_ref not in commit_groups:
                commit_groups[commit_ref] = []
            commit_groups[commit_ref].append(idx_cmd)
        
        # Execute each commit's info in a single batch command when possible
        for commit_ref, cmd_group in commit_groups.items():
            if len(cmd_group) >= 3:  # Only batch if we have multiple commands for same commit
                try:
                    batch_result = self._execute_single_commit_batch(commit_ref, cmd_group)
                    results.extend(batch_result)
                    continue
                except Exception as e:
                    logger.debug(f"Batch execution failed for {commit_ref}, falling back: {e}")
            
            # Fallback to individual execution
            for _, cmd in cmd_group:
                result = self._run_git_command(cmd)
                results.append(result)
        
        return results
    
    def _extract_commit_ref(self, cmd: List[str]) -> str:
        """Extract commit reference from Git command."""
        if len(cmd) < 3:
            return "HEAD"
        
        # For git show commands, commit is usually the last non-flag argument
        if cmd[1] == 'show':
            for arg in reversed(cmd[2:]):
                if not arg.startswith('-') and arg not in ('--format=%ci', '--format=%s', '--format=%B', '--format=%an'):
                    return arg
        
        # For git rev-parse commands
        if cmd[1] == 'rev-parse':
            for arg in cmd[2:]:
                if not arg.startswith('-'):
                    return arg.replace('^{commit}', '').replace('--short', '')
        
        return "HEAD"
    
    def _execute_single_commit_batch(self, commit_ref: str, cmd_group: List[tuple]) -> List[str]:
        """Execute multiple info requests for single commit in one command."""
        # Build a single git show command with multiple format specifiers
        format_parts = []
        cmd_mapping = []
        
        for idx_cmd in cmd_group:
            _, cmd = idx_cmd
            if 'show' in cmd and '--format=' in ' '.join(cmd):
                # Extract format specifier
                for arg in cmd:
                    if arg.startswith('--format='):
                        format_parts.append(arg.split('=', 1)[1])
                        cmd_mapping.append(('show', arg.split('=', 1)[1]))
                        break
            elif 'rev-parse' in cmd:
                if '--short' in cmd:
                    format_parts.append('%h')
                    cmd_mapping.append(('rev-parse', '--short'))
                else:
                    format_parts.append('%H')
                    cmd_mapping.append(('rev-parse', ''))
        
        if not format_parts:
            raise ValueError("No batchable formats found")
        
        # Create delimiter-separated format string
        delimiter = "|||GIV_DELIMITER|||"
        combined_format = delimiter.join(format_parts)
        
        # Execute single command
        batch_cmd = ["git", "show", "-s", f"--format={combined_format}", commit_ref]
        batch_output = self._run_git_command(batch_cmd)
        
        # Split results and return in original order
        if batch_output:
            split_results = batch_output.strip().split(delimiter)
            return split_results
        else:
            # Return empty results matching the expected count
            return [''] * len(cmd_group)
    
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
    
    def _get_diff_for_history(self, commit: str, pathspec: Optional[List[str]] = None, max_size_kb: int = 500) -> str:
        """Get diff content for history with size limits to prevent memory issues.
        
        Parameters
        ----------
        commit : str
            Commit reference
        pathspec : Optional[List[str]]
            Path specifications
        max_size_kb : int
            Maximum diff size in KB before truncation
            
        Returns
        -------
        str
            Diff content, potentially truncated
        """
        try:
            diff_content = self.get_diff(commit, pathspec, include_untracked=False)
            
            # Check size and truncate if necessary
            if len(diff_content.encode('utf-8')) > max_size_kb * 1024:
                lines = diff_content.splitlines()
                truncated_lines = []
                current_size = 0
                max_bytes = max_size_kb * 1024
                
                for line in lines:
                    line_bytes = len((line + '\n').encode('utf-8'))
                    if current_size + line_bytes > max_bytes:
                        truncated_lines.append("\n[... diff truncated due to size limit ...]")
                        break
                    truncated_lines.append(line)
                    current_size += line_bytes
                
                return '\n'.join(truncated_lines)
            
            return diff_content
            
        except Exception as e:
            logger.error(f"Failed to get diff for history: {e}")
            return f"Error getting diff: {e}"
    
    def clear_memory_caches(self) -> None:
        """Clear all in-memory caches to free memory."""
        if hasattr(self, '_diff_cache'):
            self._diff_cache.clear()
        if hasattr(self, '_metadata_cache'):
            self._metadata_cache.clear()
        logger.debug("Cleared Git repository memory caches")
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for Git operations.
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            Performance statistics grouped by operation type
        """
        return self._performance_metrics.get_all_stats()
    
    def clear_performance_stats(self) -> None:
        """Clear all collected performance statistics."""
        self._performance_metrics.clear()
        logger.debug("Cleared Git repository performance statistics")


# Backward compatibility alias
GitHistory = GitRepository