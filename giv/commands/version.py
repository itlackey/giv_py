"""
Version command implementation.

This module implements the version command that displays version information
and system details.
"""
from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

from .. import __version__
from ..config import ConfigManager
from .base import BaseCommand


class VersionCommand(BaseCommand):
    """Show version information and system details."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize version command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager)
    
    def run(self) -> int:
        """Execute the version command.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        verbose = getattr(self.args, 'verbose', 0) > 0
        
        if verbose:
            return self._show_detailed_version()
        else:
            return self._show_simple_version()
    
    def _show_simple_version(self) -> int:
        """Show simple version information."""
        print(f"giv {__version__}")
        return 0
    
    def _show_detailed_version(self) -> int:
        """Show detailed version and system information."""
        print(f"giv {__version__}")
        print()
        print("System Information:")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Platform: {platform.system()} {platform.release()}")
        print(f"  Architecture: {platform.machine()}")
        
        # Show installation location
        try:
            import giv
            install_path = Path(giv.__file__).parent.parent
            print(f"  Installation: {install_path}")
        except Exception:
            print("  Installation: Unknown")
        
        # Show configuration location
        giv_home = Path.cwd() / ".giv"
        if giv_home.exists():
            print(f"  Project config: {giv_home}")
        
        user_config = Path.home() / ".giv" / "config"
        if user_config.exists():
            print(f"  User config: {user_config}")
        
        # Show Git repository status
        try:
            from ..lib.repository import get_repository_info, is_git_repository
            if is_git_repository():
                repo_info = get_repository_info()
                repo_root = repo_info.get("root", "Unknown")
                current_branch = repo_info.get("branch", "Unknown")
                print(f"  Git repository: {repo_root}")
                print(f"  Current branch: {current_branch}")
                if "remote" in repo_info:
                    print(f"  Remote origin: {repo_info['remote']}")
            else:
                print("  Git repository: Not in a Git repository")
        except Exception as e:
            print(f"  Git repository: Unable to determine ({e})")
        
        # Show cache information
        cache_dir = Path.cwd() / ".giv" / "cache"
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*-summary.md"))
            print(f"  Cached summaries: {len(cache_files)}")
        else:
            print("  Cached summaries: 0")
        
        return 0