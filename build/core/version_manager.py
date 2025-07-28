"""
Version management utilities for the build system.

Handles version detection, validation, and manipulation for building
and releasing giv CLI binaries.
"""
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from packaging import version as packaging_version


class VersionManager:
    """Manages version information for builds and releases."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize version manager."""
        self.project_root = project_root or self._find_project_root()
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path.cwd()
        
        while current != current.parent:
            if (current / "pyproject.toml").exists() and (current / "giv").exists():
                return current
            current = current.parent
        
        raise RuntimeError("Could not find project root directory")
    
    def get_version_from_package(self) -> str:
        """Extract version from package __init__.py."""
        init_file = self.project_root / "giv" / "__init__.py"
        
        if not init_file.exists():
            raise RuntimeError(f"Package __init__.py not found: {init_file}")
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Look for __version__ = "x.y.z" pattern
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)
        
        raise RuntimeError("Could not extract version from __init__.py")
    
    def get_version_from_pyproject(self) -> str:
        """Extract version from pyproject.toml."""
        pyproject_file = self.project_root / "pyproject.toml"
        
        if not pyproject_file.exists():
            raise RuntimeError(f"pyproject.toml not found: {pyproject_file}")
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # Look for version = "x.y.z" pattern in [tool.poetry] section
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if version_match:
            return version_match.group(1)
        
        raise RuntimeError("Could not extract version from pyproject.toml")
    
    def get_version_from_git(self) -> Optional[str]:
        """Get version from git tags."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--exact-match"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            tag = result.stdout.strip()
            # Remove 'v' prefix if present
            if tag.startswith('v'):
                tag = tag[1:]
            return tag
        except subprocess.CalledProcessError:
            return None
    
    def get_version(self, source: str = "auto") -> str:
        """
        Get version from specified source.
        
        Args:
            source: Version source - "auto", "package", "pyproject", or "git"
        
        Returns:
            Version string
        """
        if source == "auto":
            # Try git first (for exact releases), then pyproject.toml (for development)
            git_version = self.get_version_from_git()
            if git_version:
                return git_version
            return self.get_version_from_pyproject()
        
        elif source == "package":
            return self.get_version_from_package()
        
        elif source == "pyproject":
            return self.get_version_from_pyproject()
        
        elif source == "git":
            git_version = self.get_version_from_git()
            if git_version is None:
                raise RuntimeError("No git tag found for current commit")
            return git_version
        
        else:
            raise ValueError(f"Unknown version source: {source}")
    
    def validate_version(self, version_string: str) -> bool:
        """Validate that version string is a valid semantic version."""
        try:
            packaging_version.Version(version_string)
            return True
        except packaging_version.InvalidVersion:
            return False
    
    def parse_version(self, version_string: str) -> Tuple[int, int, int, Optional[str]]:
        """
        Parse version string into components.
        
        Returns:
            Tuple of (major, minor, patch, prerelease)
        """
        if not self.validate_version(version_string):
            raise ValueError(f"Invalid version string: {version_string}")
        
        version_obj = packaging_version.Version(version_string)
        
        major = version_obj.major
        minor = version_obj.minor
        micro = version_obj.micro
        
        # Handle pre-release
        prerelease = None
        if version_obj.pre:
            prerelease = f"{version_obj.pre[0]}{version_obj.pre[1]}"
        
        return major, minor, micro, prerelease
    
    def bump_version(self, current_version: str, bump_type: str) -> str:
        """
        Bump version according to semantic versioning.
        
        Args:
            current_version: Current version string
            bump_type: "major", "minor", or "patch"
        
        Returns:
            New version string
        """
        major, minor, patch, prerelease = self.parse_version(current_version)
        
        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
    
    def is_prerelease(self, version_string: str) -> bool:
        """Check if version is a pre-release."""
        if not self.validate_version(version_string):
            return False
        
        version_obj = packaging_version.Version(version_string)
        return version_obj.is_prerelease
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        v1 = packaging_version.Version(version1)
        v2 = packaging_version.Version(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    
    def update_package_version(self, new_version: str) -> None:
        """Update version in package __init__.py."""
        if not self.validate_version(new_version):
            raise ValueError(f"Invalid version string: {new_version}")
        
        init_file = self.project_root / "giv" / "__init__.py"
        
        if not init_file.exists():
            raise RuntimeError(f"Package __init__.py not found: {init_file}")
        
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Update __version__ line
        new_content = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        
        with open(init_file, 'w') as f:
            f.write(new_content)
    
    def update_pyproject_version(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        if not self.validate_version(new_version):
            raise ValueError(f"Invalid version string: {new_version}")
        
        pyproject_file = self.project_root / "pyproject.toml"
        
        if not pyproject_file.exists():
            raise RuntimeError(f"pyproject.toml not found: {pyproject_file}")
        
        with open(pyproject_file, 'r') as f:
            content = f.read()
        
        # Update version line in [tool.poetry] section
        new_content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content
        )
        
        with open(pyproject_file, 'w') as f:
            f.write(new_content)
    
    def sync_versions(self) -> str:
        """Ensure all version sources are synchronized."""
        package_version = self.get_version_from_package()
        pyproject_version = self.get_version_from_pyproject()
        
        if package_version != pyproject_version:
            print(f"Version mismatch detected:")
            print(f"  Package: {package_version}")
            print(f"  pyproject.toml: {pyproject_version}")
            
            # Use package version as source of truth
            print(f"Updating pyproject.toml to match package version: {package_version}")
            self.update_pyproject_version(package_version)
            return package_version
        
        return package_version


if __name__ == "__main__":
    vm = VersionManager()
    
    print("Version Information:")
    print("=" * 30)
    
    try:
        package_version = vm.get_version_from_package()
        print(f"Package version: {package_version}")
    except RuntimeError as e:
        print(f"Package version: Error - {e}")
    
    try:
        pyproject_version = vm.get_version_from_pyproject()
        print(f"pyproject.toml version: {pyproject_version}")
    except RuntimeError as e:
        print(f"pyproject.toml version: Error - {e}")
    
    git_version = vm.get_version_from_git()
    if git_version:
        print(f"Git tag version: {git_version}")
    else:
        print("Git tag version: No exact tag match")
    
    print()
    current_version = vm.get_version()
    print(f"Current version (auto): {current_version}")
    
    if vm.validate_version(current_version):
        major, minor, patch, prerelease = vm.parse_version(current_version)
        print(f"Parsed: {major}.{minor}.{patch}" + (f"-{prerelease}" if prerelease else ""))
        print(f"Is prerelease: {vm.is_prerelease(current_version)}")