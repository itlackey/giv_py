"""
Git repository validation and root detection utilities.

This module provides functionality to validate Git repositories and automatically
navigate to the repository root directory, as specified in the application requirements.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Exception raised when repository validation fails."""
    pass


def find_repository_root() -> Path:
    """Find the Git repository root directory.
    
    Uses 'git rev-parse --show-toplevel' to find the repository root.
    This works from any subdirectory within a Git repository.
    
    Returns
    -------
    Path
        Absolute path to the repository root directory
        
    Raises
    ------
    RepositoryError
        If not executed from within a Git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            # Parse git error message for better user feedback
            error_msg = result.stderr.strip().lower()
            if "not a git repository" in error_msg:
                raise RepositoryError(
                    "Error: Not in a Git repository. "
                    "Please run this command from within a Git repository or one of its subdirectories."
                )
            else:
                raise RepositoryError(f"Git error: {result.stderr.strip()}")
        
        repo_root = result.stdout.strip()
        if not repo_root:
            raise RepositoryError("Unable to determine Git repository root")
            
        return Path(repo_root).resolve()
        
    except FileNotFoundError:
        raise RepositoryError(
            "Error: Git command not found. Please ensure Git is installed and available in your PATH."
        )
    except Exception as e:
        raise RepositoryError(f"Unexpected error finding repository root: {e}")


def validate_and_change_to_repo_root() -> Path:
    """Validate Git repository and change to repository root directory.
    
    This function implements the core repository requirement from the specification:
    1. Validates execution environment (check for Git repository)
    2. Detects Git repository root using 'git rev-parse --show-toplevel'
    3. Changes working directory to repository root
    
    Returns
    -------
    Path
        Absolute path to the repository root directory
        
    Raises
    ------
    RepositoryError
        If not executed from within a Git repository or if navigation fails
    SystemExit
        Exits with code 1 on repository validation failure
    """
    try:
        # Find repository root
        repo_root = find_repository_root()
        
        # Change to repository root
        original_cwd = Path.cwd()
        os.chdir(repo_root)
        
        logger.debug(f"Changed working directory from {original_cwd} to {repo_root}")
        
        return repo_root
        
    except RepositoryError as e:
        logger.error(str(e))
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Failed to change to repository root: {e}"
        logger.error(error_msg)
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)


def is_git_repository(path: Optional[Path] = None) -> bool:
    """Check if a directory is within a Git repository.
    
    Parameters
    ----------
    path : Optional[Path]
        Directory to check. Defaults to current working directory.
        
    Returns
    -------
    bool
        True if within a Git repository, False otherwise
    """
    if path is None:
        path = Path.cwd()
        
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def get_repository_info() -> dict[str, str]:
    """Get repository information for debugging and version display.
    
    Returns
    -------
    dict[str, str]
        Dictionary containing repository information
    """
    info = {}
    
    try:
        # Repository root
        repo_root = find_repository_root()
        info["root"] = str(repo_root)
        
        # Current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()
        
        # Remote URL (if available)
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            info["remote"] = result.stdout.strip()
            
    except Exception as e:
        logger.debug(f"Could not get repository info: {e}")
        
    return info
