"""
Comprehensive tests for lib.metadata module.

Tests project metadata extraction including version detection,
title detection, and various project formats.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from giv.lib.metadata import ProjectMetadata
from conftest import change_directory


class TestProjectMetadataVersionDetection:
    """Test version detection from various sources."""

    def test_get_version_from_pyproject_toml(self):
        """Test version detection from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pyproject_file = project_root / "pyproject.toml"
            pyproject_file.write_text(
                """
[tool.poetry]
name = "test-project"
version = "1.2.3"
description = "Test project"
"""
            )

            # Change working directory to the test project
            original_cwd = Path.cwd()
            try:
                os.chdir(project_root)
                version = ProjectMetadata.get_version(commit="--current")
                assert version == "1.2.3"
            finally:
                os.chdir(original_cwd)

    def test_get_version_from_cargo_toml(self):
        """Test version detection from Cargo.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            cargo_file = project_root / "Cargo.toml"
            cargo_file.write_text(
                """
[package]
name = "test-project"
version = "0.5.2"
edition = "2021"
"""
            )

            with change_directory(
                project_root
            ):  # Application will work from repository root
                version = ProjectMetadata.get_version(commit="--current")
                assert version == "0.5.2"

    def test_get_version_from_version_txt(self):
        """Test version detection from VERSION.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            version_file = project_root / "VERSION.txt"
            version_file.write_text("4.2.1\n")

            with change_directory(project_root):
                version = ProjectMetadata.get_version(commit="--current")
                assert version == "4.2.1"

    def test_get_version_from_version_py(self):
        """Test version detection from __version__.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            version_file = project_root / "__version__.py"
            version_file.write_text('__version__ = "1.5.8"\n')

            with change_directory(project_root):
                version = ProjectMetadata.get_version(commit="--current")
                assert version == "1.5.8"

    def test_get_version_from_git_tag(self):
        """Test version detection from git tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            # Mock git command to return version tag
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v2.3.4\n"

                with change_directory(project_root):
                    version = ProjectMetadata.get_version(commit="--current")
                    assert version == "2.3.4"

    def test_get_version_precedence(self):
        """Test version detection precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            # Create multiple version sources
            (project_root / "pyproject.toml").write_text(
                """
[tool.poetry]
version = "1.0.0"
"""
            )
            (project_root / "package.json").write_text('{"version": "2.0.0"}')
            (project_root / "VERSION.txt").write_text("3.0.0")

            with change_directory(project_root):
                version = ProjectMetadata.get_version(commit="--current")
                # pyproject.toml should have highest precedence
                assert version == "1.0.0"

    def test_get_version_not_found(self):
        """Test version detection when no version found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            with change_directory(project_root):
                version = ProjectMetadata.get_version(commit="--current")
                assert version == "0.0.0"  # Default version


class TestProjectMetadataTitleDetection:
    """Test project title detection."""

    def test_get_title_from_pyproject_toml(self):
        """Test title detection from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            pyproject_file = project_root / "pyproject.toml"
            pyproject_file.write_text(
                """
[tool.poetry]
name = "awesome-project"
version = "1.0.0"
"""
            )

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                assert title == "awesome-project"

    def test_get_title_from_setup_py(self):
        """Test title detection from setup.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            setup_file = project_root / "setup.py"
            setup_file.write_text(
                """
setup(
    name="cool-tool",
    version="1.0.0",
)
"""
            )

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                assert title == "cool-tool"

    def test_get_title_from_package_json(self):
        """Test title detection from package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            package_file = project_root / "package.json"
            package_file.write_text('{"name": "web-app", "version": "1.0.0"}')

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                assert title == "web-app"

    def test_get_title_from_cargo_toml(self):
        """Test title detection from Cargo.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            cargo_file = project_root / "Cargo.toml"
            cargo_file.write_text(
                """
[package]
name = "rust-cli"
version = "1.0.0"
"""
            )

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                assert title == "rust-cli"

    def test_get_title_from_directory_name(self):
        """Test title detection from directory name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "my-project"
            project_root.mkdir()

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                assert title == "my-project"

    def test_get_title_precedence(self):
        """Test title detection precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "directory-name"
            project_root.mkdir()

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            # Create multiple title sources
            (project_root / "pyproject.toml").write_text(
                """
[tool.poetry]
name = "pyproject-name"
"""
            )
            (project_root / "package.json").write_text('{"name": "package-name"}')

            with change_directory(project_root):
                title = ProjectMetadata.get_title(commit="--current")
                # pyproject.toml should have highest precedence
                assert title == "pyproject-name"


class TestProjectMetadataStaticMethods:
    """Test static methods of ProjectMetadata."""

    @patch.object(ProjectMetadata, "get_version", return_value="1.2.3")
    def test_static_get_version(self, mock_get_version):
        """Test static get_version method."""
        version = ProjectMetadata.get_version()
        assert version == "1.2.3"

    @patch.object(ProjectMetadata, "get_title", return_value="test-project")
    def test_static_get_title(self, mock_get_title):
        """Test static get_title method."""
        title = ProjectMetadata.get_title()
        assert title == "test-project"


class TestProjectMetadataFileFormats:
    """Test parsing of different file formats."""

    def test_parse_pyproject_toml_complex(self):
        """Test parsing complex pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            pyproject_file = project_root / "pyproject.toml"
            pyproject_file.write_text(
                """
[build-system]
requires = ["poetry-core"]

[tool.poetry]
name = "complex-project"
version = "2.1.0"
description = "A complex project"
authors = ["Author <email@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"

[tool.other]
setting = "value"
"""
            )

            with change_directory(project_root):
                assert (
                    ProjectMetadata.get_title(commit="--current") == "complex-project"
                )
                assert ProjectMetadata.get_version(commit="--current") == "2.1.0"

    def test_parse_setup_py_complex(self):
        """Test parsing complex setup.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            setup_file = project_root / "setup.py"
            setup_file.write_text(
                """
from setuptools import setup, find_packages

setup(
    name="complex-setup",
    version="3.2.1",
    description="Complex setup.py example",
    long_description="Long description here",
    author="Author Name",
    author_email="author@example.com",
    packages=find_packages(),
    install_requires=[
        "requests",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "mycli=mypackage.cli:main",
        ],
    },
)
"""
            )

            with change_directory(project_root):
                assert ProjectMetadata.get_title(commit="--current") == "complex-setup"
                assert ProjectMetadata.get_version(commit="--current") == "3.2.1"

    def test_parse_package_json_complex(self):
        """Test parsing complex package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            package_file = project_root / "package.json"
            package_file.write_text(
                """
{
  "name": "complex-node-app",
  "version": "1.5.2",
  "description": "Complex Node.js application",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  },
  "keywords": ["node", "express", "app"],
  "author": "Developer Name",
  "license": "MIT"
}
"""
            )

            with change_directory(project_root):
                assert (
                    ProjectMetadata.get_title(commit="--current") == "complex-node-app"
                )
                assert ProjectMetadata.get_version(commit="--current") == "1.5.2"


class TestProjectMetadataErrorHandling:
    """Test error handling in metadata detection."""

    def test_malformed_pyproject_toml(self):
        """Test handling malformed pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            pyproject_file = project_root / "pyproject.toml"
            pyproject_file.write_text("malformed toml content [[[")

            with change_directory(project_root):
                # Should not crash, should use fallback
                version = ProjectMetadata.get_version(commit="--current")
                title = ProjectMetadata.get_title(commit="--current")

                assert version == "0.0.0"  # Default fallback
                assert title == project_root.name  # Directory name fallback

    def test_malformed_package_json(self):
        """Test handling malformed package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            package_file = project_root / "package.json"
            package_file.write_text('{"name": "test", invalid json}')

            with change_directory(project_root):
                # Should not crash, should use fallback
                version = ProjectMetadata.get_version(commit="--current")
                title = ProjectMetadata.get_title(commit="--current")

                assert version == "0.0.0"
                assert title == project_root.name

    def test_permission_error(self):
        """Test handling permission errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            with patch("pathlib.Path.read_text", side_effect=PermissionError()):
                with change_directory(project_root):
                    version = ProjectMetadata.get_version(commit="--current")
                    title = ProjectMetadata.get_title(commit="--current")

                    # Should use fallbacks
                    assert version == "0.0.0"
                    assert title == project_root.name

    def test_git_command_failure(self):
        """Test handling git command failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1  # Git command failed

                with change_directory(project_root):
                    version = ProjectMetadata.get_version(commit="--current")

                    assert version == "0.0.0"  # Should fallback


class TestProjectMetadataVersionFormatting:
    """Test version formatting and normalization."""

    def test_version_normalization(self):
        """Test version string normalization."""
        test_cases = [
            ("v1.2.3", "1.2.3"),  # Remove 'v' prefix
            ("1.2.3-alpha", "1.2.3-alpha"),  # Keep prerelease
            ("1.2.3+build.1", "1.2.3+build.1"),  # Keep build metadata
            ("  1.2.3  ", "1.2.3"),  # Trim whitespace
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            for input_version, expected_version in test_cases:
                version_file = project_root / "VERSION.txt"
                version_file.write_text(input_version)

                with change_directory(project_root):
                    version = ProjectMetadata.get_version(commit="--current")
                    assert version == expected_version

                version_file.unlink()  # Clean up for next test

    def test_git_tag_version_extraction(self):
        """Test extracting version from git tags."""
        test_cases = [
            ("v1.2.3", "1.2.3"),
            ("release-2.1.0", "2.1.0"),
            ("1.0.0-rc.1", "1.0.0-rc.1"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            for tag, expected_version in test_cases:
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0
                    mock_run.return_value.stdout = f"{tag}\n"

                    with change_directory(project_root):
                        version = ProjectMetadata.get_version(commit="--current")
                        assert version == expected_version


class TestProjectMetadataIntegration:
    """Test integration scenarios."""

    def test_real_project_structure(self):
        """Test with realistic project structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "giv-cli"
            project_root.mkdir()

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            # Create Python project structure
            (project_root / "pyproject.toml").write_text(
                """
[tool.poetry]
name = "giv-cli"
version = "1.0.0"
description = "Git commit message generator"

[tool.poetry.dependencies]
python = "^3.8"
"""
            )

            (project_root / "giv").mkdir()
            (project_root / "giv" / "__init__.py").write_text('__version__ = "1.0.0"')

            (project_root / "README.md").write_text("# giv-cli\n\nAwesome tool")

            with change_directory(project_root):
                assert ProjectMetadata.get_title(commit="--current") == "giv-cli"
                assert ProjectMetadata.get_version(commit="--current") == "1.0.0"

    def test_monorepo_structure(self):
        """Test with monorepo-style structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monorepo = Path(tmpdir) / "monorepo"
            monorepo.mkdir()

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=monorepo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=monorepo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=monorepo, check=True
            )

            # Root package.json
            (monorepo / "package.json").write_text(
                """
{
  "name": "monorepo-root",
  "version": "1.0.0",
  "private": true,
  "workspaces": ["packages/*"]
}
"""
            )

            # Sub-project
            subproject = monorepo / "packages" / "cli"
            subproject.mkdir(parents=True)
            (subproject / "package.json").write_text(
                """
{
  "name": "@monorepo/cli",
  "version": "2.1.0"
}
"""
            )

            # Test sub-project metadata
            with change_directory(subproject):
                assert ProjectMetadata.get_title(commit="--current") == "@monorepo/cli"
                assert ProjectMetadata.get_version(commit="--current") == "2.1.0"

    def test_metadata_caching(self):
        """Test that metadata is cached appropriately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=project_root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=project_root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=project_root,
                check=True,
            )

            version_file = project_root / "VERSION.txt"
            version_file.write_text("1.0.0")

            with change_directory(project_root):
                # First call
                version1 = ProjectMetadata.get_version(commit="--current")

                # Modify file
                version_file.write_text("2.0.0")

                # Second call - should not be cached for version files
                version2 = ProjectMetadata.get_version(commit="--current")

                assert version1 == "1.0.0"
                assert version2 == "2.0.0"
