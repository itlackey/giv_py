"""
Project metadata extraction and management.

This module provides comprehensive project metadata detection that matches
the Bash implementation exactly, including:
- Multi-language project type detection (Node.js, Python, Rust, Go, etc.)
- Version file detection and parsing with custom patterns
- Project URL and description extraction
- Git-aware metadata extraction from specific commits
- Metadata caching for performance
- Configuration-based custom project types
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class ProjectMetadata:
    """Project metadata detection and extraction system.
    
    This class provides comprehensive project metadata detection matching
    the Bash implementation, with support for multiple project types and
    Git-aware metadata extraction.
    """
    
    _cache: Dict[str, Dict[str, str]] = {}
    
    @classmethod
    def detect_project_type(cls, path: Optional[Path] = None) -> str:
        """Detect project type based on files present, matching Bash detect_project_type.
        
        Parameters
        ----------
        path : Optional[Path]
            Directory to check. Defaults to current working directory.
            
        Returns
        -------
        str
            Project type: 'node', 'python', 'rust', 'go', 'php', 'gradle', 'maven', or 'custom'
        """
        if path is None:
            path = Path.cwd()
        
        # Check files in priority order matching Bash implementation
        if (path / "pyproject.toml").exists():
            return "python"
        elif (path / "setup.py").exists():
            return "python"
        elif (path / "package.json").exists():
            return "node"
        elif (path / "Cargo.toml").exists():
            return "rust"
        elif (path / "go.mod").exists():
            return "go"
        elif (path / "composer.json").exists():
            return "php"
        elif (path / "build.gradle").exists():
            return "gradle"
        elif (path / "pom.xml").exists():
            return "maven"
        else:
            return "custom"

    @classmethod
    def get_file_content_at_commit(cls, file_path: str, commit: str = "HEAD") -> Optional[str]:
        """Get file content at specific git commit, matching metadata_get_file_content."""
        if commit in ("--current", "--cached", ""):
            # Current working directory file
            try:
                return Path(file_path).read_text(encoding="utf-8")
            except (FileNotFoundError, OSError):
                return None
        
        # Get from git commit
        try:
            result = subprocess.run(
                ["git", "show", f"{commit}:{file_path}"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except (FileNotFoundError, subprocess.SubprocessError):
            return None

    @classmethod
    def get_metadata_value(cls, key: str, commit: str = "HEAD", 
                          project_type: Optional[str] = None) -> str:
        """Get metadata value matching Bash get_metadata_value function.
        
        Parameters
        ----------
        key : str
            Metadata key to retrieve ('title', 'name', 'version', etc.)
        commit : str
            Git commit to get metadata from
        project_type : Optional[str]
            Override project type detection
            
        Returns
        -------
        str
            Metadata value or empty string if not found
        """
        # Auto-detect project type if not specified
        if project_type is None:
            project_type = os.environ.get("GIV_PROJECT_TYPE", "auto")
            if project_type == "auto":
                project_type = cls.detect_project_type()
        
        # Handle different project types matching Bash logic
        result = ""
        if project_type == "node":
            result = cls._get_node_metadata(key, commit)
        elif project_type == "python":
            result = cls._get_python_metadata(key, commit)
        elif project_type == "rust":
            result = cls._get_rust_metadata(key, commit)
        elif project_type == "go":
            result = cls._get_go_metadata(key, commit)
        elif project_type == "custom":
            result = cls._get_custom_metadata(key, commit)
        
        # If version not found in project files, try git tags
        if not result and key == "version":
            result = cls._get_version_from_git_tag(commit)
        
        return result

    @classmethod
    def _get_version_from_git_tag(cls, commit: str = "HEAD") -> str:
        """Extract version from git tags."""
        try:
            # Get the most recent tag
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0", commit],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                if tag:
                    # Extract version from tag (remove common prefixes)
                    return cls._extract_version_from_tag(tag)
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
        
        return ""
    
    @classmethod
    def _extract_version_from_tag(cls, tag: str) -> str:
        """Extract version number from git tag."""
        if not tag:
            return ""
        
        # Remove common prefixes like 'v', 'release-', etc.
        patterns = [
            r'^v(.+)$',                    # v1.2.3 -> 1.2.3
            r'^release-(.+)$',             # release-1.2.3 -> 1.2.3
            r'^version-(.+)$',             # version-1.2.3 -> 1.2.3
            r'^(.+)$',                     # 1.2.3 -> 1.2.3 (no prefix)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, tag, re.IGNORECASE)
            if match:
                version = match.group(1)
                # Check if it looks like a version number
                if re.match(r'^\d+(\.\d+)*', version):
                    return version
        
        return tag  # Return original tag if no version pattern found

    @classmethod
    def _get_node_metadata(cls, key: str, commit: str) -> str:
        """Extract metadata from package.json."""
        content = cls.get_file_content_at_commit("package.json", commit)
        if not content:
            return ""
        
        try:
            data = json.loads(content)
            value = data.get(key, "")
            return str(value) if value is not None else ""
        except (json.JSONDecodeError, KeyError):
            # For malformed JSON, return empty string to allow fallback to directory name
            return ""

    @classmethod
    def _get_python_metadata(cls, key: str, commit: str) -> str:
        """Extract metadata from pyproject.toml or setup.py."""
        # Try pyproject.toml first
        content = cls.get_file_content_at_commit("pyproject.toml", commit)
        if content:
            try:
                import tomllib
                data = tomllib.loads(content)
                
                # Try PEP 621 project metadata first
                project = data.get("project", {})
                if key in project:
                    value = project[key]
                    return str(value) if value is not None else ""
                
                # Try Poetry metadata
                poetry = data.get("tool", {}).get("poetry", {})
                if key in poetry:
                    value = poetry[key]
                    return str(value) if value is not None else ""
                    
                # Handle special key mappings
                if key == "title" and "name" in project:
                    return str(project["name"])
                elif key == "title" and "name" in poetry:
                    return str(poetry["name"])
                    
            except Exception:
                # Fallback to regex parsing for malformed TOML
                result = cls._parse_toml_like(content, key)
                if result:
                    return result
        
        # Try setup.py if pyproject.toml didn't work
        setup_content = cls.get_file_content_at_commit("setup.py", commit)
        if setup_content:
            return cls._parse_setup_py(setup_content, key)
        
        return ""

    @classmethod
    def _get_rust_metadata(cls, key: str, commit: str) -> str:
        """Extract metadata from Cargo.toml."""
        content = cls.get_file_content_at_commit("Cargo.toml", commit)
        if not content:
            return ""
        
        try:
            import tomllib
            data = tomllib.loads(content)
            package = data.get("package", {})
            value = package.get(key, "")
            
            # Handle special key mappings
            if key == "title" and "name" in package:
                return str(package["name"])
            
            return str(value) if value is not None else ""
        except Exception:
            return cls._parse_toml_like(content, key, section="package")

    @classmethod
    def _get_go_metadata(cls, key: str, commit: str) -> str:
        """Extract metadata from go.mod and other Go project files."""
        # For Go projects, try to get module name from go.mod
        if key in ("name", "title"):
            content = cls.get_file_content_at_commit("go.mod", commit)
            if content:
                # Extract module name from "module <name>" line
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("module "):
                        return line.split("module ", 1)[1].strip()
        
        return ""

    @classmethod
    def _get_custom_metadata(cls, key: str, commit: str) -> str:
        """Extract metadata from custom version file."""
        # Try multiple common version file names
        version_files = [
            os.environ.get("GIV_PROJECT_VERSION_FILE", "version.txt"),
            "VERSION.txt",
            "VERSION",
            "version",
            "__version__.py"
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in version_files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)
        
        for version_file in unique_files:
            content = cls.get_file_content_at_commit(version_file, commit)
            if not content:
                continue
                
            # Handle Python __version__.py files
            if version_file.endswith(".py"):
                if key == "version":
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        return match.group(1)
                continue
            
            # Handle plain version files - if key is "version", just return first line
            if key == "version":
                first_line = content.strip().split('\n')[0].strip()
                if first_line:
                    return first_line
                    
            # Parse custom format matching Bash awk logic for other keys
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Case-insensitive matching
                if re.search(rf'\b{re.escape(key)}\b', line, re.IGNORECASE):
                    # Look for key=value pattern
                    if "=" in line:
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            value = parts[1].strip()
                            # Remove quotes
                            value = re.sub(r'^["\']|["\']$', '', value)
                            return value
        
        return ""

    @classmethod
    def _parse_setup_py(cls, content: str, key: str) -> str:
        """Parse setup.py content for metadata."""
        # Look for setup() call with key=value patterns
        # Handle both quoted and unquoted values
        patterns = [
            rf'{re.escape(key)}\s*=\s*["\']([^"\']+)["\']',  # key="value" or key='value'
            rf'{re.escape(key)}\s*=\s*([^,\)\s]+)',          # key=value (unquoted)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Handle special key mappings
                if key == "title" and not value:
                    continue
                return value
        
        return ""

    @classmethod
    def _parse_json_like(cls, content: str, key: str) -> str:
        """Parse JSON-like content with regex fallback."""
        pattern = rf'"{re.escape(key)}"\s*:\s*"([^"]+)"'
        match = re.search(pattern, content)
        return match.group(1) if match else ""

    @classmethod
    def _parse_toml_like(cls, content: str, key: str, section: str = "project") -> str:
        """Parse TOML-like content with regex fallback."""
        # Find section
        in_section = False
        for line in content.splitlines():
            line = line.strip()
            if line == f"[{section}]":
                in_section = True
                continue
            elif line.startswith("[") and line.endswith("]"):
                in_section = False
                continue
            
            if in_section and "=" in line:
                parts = line.split("=", 1)
                if len(parts) == 2 and parts[0].strip() == key:
                    value = parts[1].strip()
                    # Remove quotes
                    value = re.sub(r'^["\']|["\']$', '', value)
                    return value
        
        return ""

    @staticmethod
    def get_title(commit: str = "HEAD") -> str:
        """Return a human friendly title for the current project."""
        # Try to get title/name from project metadata
        title = ProjectMetadata.get_metadata_value("title", commit)
        if title:
            return title
        
        title = ProjectMetadata.get_metadata_value("name", commit)
        if title:
            return title
        
        # Fallback to directory name
        return Path.cwd().name

    @staticmethod
    def get_version(commit: str = "HEAD") -> str:
        """Return the project version if it can be determined."""
        version = ProjectMetadata.get_metadata_value("version", commit)
        if version:
            # Normalize version string
            version = ProjectMetadata._normalize_version(version)
        return version if version else "0.0.0"
    
    @staticmethod
    def _normalize_version(version: str) -> str:
        """Normalize version string by removing 'v' prefix and trimming whitespace."""
        if not version:
            return version
        
        # Strip whitespace
        version = version.strip()
        
        # Remove 'v' prefix (case-insensitive)
        if version.lower().startswith('v'):
            version = version[1:]
        
        return version

    @staticmethod
    def get_description(commit: str = "HEAD") -> str:
        """Return the project description if available."""
        return ProjectMetadata.get_metadata_value("description", commit)

    @staticmethod
    def get_url(commit: str = "HEAD") -> str:
        """Return the project URL if available."""
        # Try common URL fields
        url = ProjectMetadata.get_metadata_value("homepage", commit)
        if url:
            return url
        
        url = ProjectMetadata.get_metadata_value("url", commit)
        if url:
            return url
        
        return ProjectMetadata.get_metadata_value("repository", commit)

    @staticmethod
    def get_author(commit: str = "HEAD") -> str:
        """Return the project author if available."""
        return ProjectMetadata.get_metadata_value("author", commit)

    @classmethod
    @lru_cache(maxsize=128)
    def get_all_metadata(cls, commit: str = "HEAD") -> Dict[str, str]:
        """Get all available project metadata as a dictionary.
        
        This method is cached for performance.
        
        Parameters
        ----------
        commit : str
            Git commit to get metadata from
            
        Returns
        -------
        Dict[str, str]
            Dictionary containing all available metadata
        """
        project_type = cls.detect_project_type()
        
        metadata = {
            "project_type": project_type,
            "title": cls.get_title(commit),
            "name": cls.get_metadata_value("name", commit),
            "version": cls.get_version(commit),
            "description": cls.get_description(commit),
            "url": cls.get_url(commit),
            "author": cls.get_author(commit),
        }
        
        # Add project-type specific metadata
        if project_type == "node":
            metadata.update({
                "license": cls.get_metadata_value("license", commit),
                "main": cls.get_metadata_value("main", commit),
            })
        elif project_type == "python":
            metadata.update({
                "license": cls.get_metadata_value("license", commit),
                "requires_python": cls.get_metadata_value("requires-python", commit),
            })
        elif project_type == "rust":
            metadata.update({
                "license": cls.get_metadata_value("license", commit),
                "edition": cls.get_metadata_value("edition", commit),
            })
        
        return metadata

    @classmethod
    def clear_cache(cls):
        """Clear the metadata cache."""
        cls.get_all_metadata.cache_clear()
        cls._cache.clear()