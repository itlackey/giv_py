"""
Core configuration for the giv build system.
"""
from pathlib import Path
from typing import Dict, List, Optional


class BuildConfig:
    """Configuration for building and packaging giv CLI."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize build configuration."""
        if project_root is None:
            # Auto-detect project root
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "pyproject.toml").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                raise RuntimeError("Could not find project root (pyproject.toml)")
        
        self.project_root = Path(project_root)
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.source_dir = self.project_root / "giv"
        self.templates_dir = self.source_dir / "templates"
        
        # Package information
        self.package_name = "giv"
        self.description = "Git history AI assistant CLI tool"
        self.homepage = "https://github.com/giv-cli/giv-py"
        self.repository = "https://github.com/giv-cli/giv-py"
        self.license = "MIT"
        self.author = "giv Development Team"
        self.author_email = "giv@example.com"
        
        # Build settings  
        self.python_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
        self.platforms = {
            "linux-x86_64": {
                "os": "linux",
                "arch": "x86_64",
                "binary_name": "giv-linux-x86_64",
                "supported": True
            },
            "linux-arm64": {
                "os": "linux", 
                "arch": "arm64",
                "binary_name": "giv-linux-arm64",
                "supported": True
            },
            "darwin-x86_64": {
                "os": "darwin",
                "arch": "x86_64", 
                "binary_name": "giv-macos-x86_64",
                "supported": True
            },
            "darwin-arm64": {
                "os": "darwin",
                "arch": "arm64",
                "binary_name": "giv-macos-arm64", 
                "supported": True
            },
            "windows-x86_64": {
                "os": "windows",
                "arch": "x86_64",
                "binary_name": "giv-windows-x86_64.exe",
                "supported": True
            }
        }
        
        # Output settings
        self.output_formats = ["binary", "wheel", "sdist", "homebrew", "scoop", "snap", "flatpak", "npm"]
        
    def get_binary_path(self, platform: str) -> Path:
        """Get path to binary for specified platform."""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")
        
        binary_name = self.platforms[platform]["binary_name"]
        return self.dist_dir / binary_name
        
    def get_package_files(self) -> Dict[str, List[Path]]:
        """Get list of files to include in packages."""
        return {
            "source": list(self.source_dir.rglob("*.py")),
            "templates": list(self.templates_dir.rglob("*.md")) if self.templates_dir.exists() else [],
            "docs": [self.project_root / "README.md"],
            "config": [self.project_root / "pyproject.toml"]
        }
        
    def get_github_release_url(self, version: str, filename: str) -> str:
        """Get GitHub release download URL."""
        return f"{self.repository}/releases/download/v{version}/{filename}"
        
    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variables for build."""
        return {
            "PACKAGE_NAME": self.package_name,
            "PROJECT_ROOT": str(self.project_root),
            "BUILD_DIR": str(self.build_dir),
            "DIST_DIR": str(self.dist_dir)
        }
