"""
Build system configuration management.

Centralizes all build configuration including package metadata,
platform definitions, and build paths.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
import platform


class BuildConfig:
    """Central configuration for the build system."""
    
    # Package metadata
    PACKAGE_NAME = "giv"
    DESCRIPTION = "Git history AI assistant CLI tool"
    MAINTAINER = "giv Development Team <giv@example.com>"
    LICENSE = "MIT"
    REPOSITORY = "https://github.com/giv-cli/giv-py"
    
    # Docker configuration
    DOCKER_IMAGE = "giv-cli/giv"
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize build configuration."""
        self.project_root = project_root or self._find_project_root()
        self.build_root = self.project_root / "build"
        self.dist_root = self.project_root / "dist"
        self.temp_root = self.project_root / ".tmp"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path.cwd()
        
        while current != current.parent:
            if (current / "pyproject.toml").exists() and (current / "giv").exists():
                return current
            current = current.parent
        
        raise RuntimeError("Could not find project root directory")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.build_root,
            self.dist_root,
            self.temp_root,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_version(self) -> str:
        """Extract version from pyproject.toml since __init__.py uses importlib.metadata."""
        pyproject_file = self.project_root / "pyproject.toml"
        
        if not pyproject_file.exists():
            raise RuntimeError(f"pyproject.toml not found: {pyproject_file}")
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # Look for version = "x.y.z" pattern in [tool.poetry] section
        import re
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)
        
        raise RuntimeError("Could not extract version from pyproject.toml")
    
    @property
    def supported_platforms(self) -> Dict[str, List[str]]:
        """Get supported platforms and architectures."""
        return {
            "linux": ["x86_64", "arm64"],
            "darwin": ["x86_64", "arm64"],  # macOS
            "windows": ["x86_64"],
        }
    
    @property
    def current_platform(self) -> str:
        """Get current platform name."""
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "windows"
        else:
            return "linux"
    
    @property
    def current_architecture(self) -> str:
        """Get current architecture."""
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            return "x86_64"
        elif machine in ["arm64", "aarch64"]:
            return "arm64"
        else:
            raise RuntimeError(f"Unsupported architecture: {machine}")
    
    def get_binary_name(self, platform_name: str, arch: str) -> str:
        """Get binary name for platform and architecture."""
        if platform_name == "windows":
            return "giv.exe"
        else:
            return "giv"
    
    def get_platform_binary_name(self, platform_name: str, arch: str) -> str:
        """Get platform-specific binary name for releases."""
        if platform_name == "windows":
            return f"giv-{platform_name}-{arch}.exe"
        else:
            return f"giv-{platform_name}-{arch}"
    
    def get_dist_dir(self, version: str) -> Path:
        """Get distribution directory for a specific version."""
        return self.dist_root / version
    
    def get_platform_dist_dir(self, version: str, platform_name: str, arch: str) -> Path:
        """Get platform-specific distribution directory."""
        return self.get_dist_dir(version) / f"{platform_name}-{arch}"


def get_build_config() -> BuildConfig:
    """Get the global build configuration instance."""
    return BuildConfig()