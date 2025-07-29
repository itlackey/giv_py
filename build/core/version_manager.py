"""
Version management for the giv build system.
"""
import re
import subprocess
from pathlib import Path
from typing import Optional


class VersionManager:
    """Manages version information for builds."""
    
    def __init__(self, project_root: Path):
        """Initialize version manager."""
        self.project_root = Path(project_root)
        self.pyproject_path = self.project_root / "pyproject.toml"
        
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
            
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
            
        # Extract version from pyproject.toml
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            raise ValueError("Version not found in pyproject.toml")
            
        return match.group(1)
        
    def get_git_version(self) -> Optional[str]:
        """Get version from git tags."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            # Remove 'v' prefix if present
            if version.startswith('v'):
                version = version[1:]
            return version
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
            
    def get_git_commit(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
            
    def is_git_dirty(self) -> bool:
        """Check if git working directory is dirty."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
            
    def get_build_version(self, include_git: bool = True) -> str:
        """
        Get version for building.
        
        Args:
            include_git: Whether to include git info for dev versions
            
        Returns:
            Version string suitable for building
        """
        base_version = self.get_current_version()
        
        if not include_git:
            return base_version
            
        git_version = self.get_git_version()
        git_commit = self.get_git_commit()
        
        # If git version matches current version and working dir is clean, use base version
        if git_version == base_version and not self.is_git_dirty():
            return base_version
            
        # Otherwise, create development version
        dev_version = base_version
        if git_commit:
            dev_version += f"+{git_commit}"
            if self.is_git_dirty():
                dev_version += ".dirty"
                
        return dev_version
        
    def update_version(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
            
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
            
        # Update version in pyproject.toml
        updated_content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content
        )
        
        if updated_content == content:
            raise ValueError("Version field not found in pyproject.toml")
            
        with open(self.pyproject_path, 'w') as f:
            f.write(updated_content)
            
    def is_release_version(self, version: Optional[str] = None) -> bool:
        """Check if version is a release version (not dev/pre-release)."""
        if version is None:
            version = self.get_current_version()
            
        # Release versions don't contain +, -, alpha, beta, rc, dev
        return not re.search(r'[+\-]|alpha|beta|rc|dev', version.lower())
