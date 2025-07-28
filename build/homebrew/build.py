"""
Homebrew formula builder for giv CLI.

Generates Homebrew formulas that reference binary releases.
"""
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Optional

from ..core.config import BuildConfig
from ..core.version_manager import VersionManager


class HomebrewBuilder:
    """Builds Homebrew formula for binary distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Homebrew builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "giv.rb"
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def generate_formula(self, version: str, binary_paths: Dict[str, Path]) -> str:
        """
        Generate Homebrew formula with binary checksums.
        
        Args:
            version: Version string
            binary_paths: Dictionary mapping platform-arch to binary path
            
        Returns:
            Generated formula content
        """
        # Read template
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Calculate checksums for each binary
        checksums = {}
        for platform_arch, binary_path in binary_paths.items():
            if binary_path.exists():
                checksum = self.calculate_sha256(binary_path)
                checksums[platform_arch.upper().replace("-", "_") + "_SHA256"] = checksum
        
        # Replace template variables
        replacements = {
            "{{VERSION}}": version,
            **{f"{{{{{key}}}}}": value for key, value in checksums.items()}
        }
        
        formula = template
        for placeholder, value in replacements.items():
            formula = formula.replace(placeholder, value)
        
        return formula
    
    def build_formula(self, version: Optional[str] = None, binary_paths: Optional[Dict[str, Path]] = None) -> Path:
        """
        Build Homebrew formula.
        
        Args:
            version: Version string (auto-detected if not provided)
            binary_paths: Binary paths (auto-detected if not provided)
            
        Returns:
            Path to generated formula
        """
        if version is None:
            version = self.version_manager.get_version()
        
        if binary_paths is None:
            # Auto-detect binary paths
            binary_paths = {}
            dist_dir = self.config.get_dist_dir(version)
            
            for platform_dir in dist_dir.iterdir():
                if platform_dir.is_dir() and "-" in platform_dir.name:
                    platform_arch = platform_dir.name
                    binary_name = self.config.get_binary_name(*platform_arch.split("-", 1))
                    binary_path = platform_dir / binary_name
                    
                    if binary_path.exists():
                        binary_paths[platform_arch] = binary_path
        
        print(f"Building Homebrew formula for version {version}")
        print(f"Binary paths: {list(binary_paths.keys())}")
        
        # Generate formula
        formula_content = self.generate_formula(version, binary_paths)
        
        # Output directory
        output_dir = self.config.get_dist_dir(version) / "homebrew"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write formula
        formula_path = output_dir / "giv.rb"
        with open(formula_path, 'w') as f:
            f.write(formula_content)
        
        print(f"✓ Homebrew formula generated: {formula_path}")
        return formula_path
    
    def test_formula(self, formula_path: Path) -> bool:
        """
        Test Homebrew formula syntax.
        
        Args:
            formula_path: Path to formula file
            
        Returns:
            True if formula is valid
        """
        try:
            # Check if brew command is available
            subprocess.run(["brew", "--version"], capture_output=True, check=True)
            
            # Test formula syntax
            result = subprocess.run(
                ["brew", "ruby", "-c", f"load '{formula_path}'"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Homebrew formula syntax is valid")
                return True
            else:
                print(f"✗ Homebrew formula syntax error: {result.stderr}")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: brew command not available, skipping formula validation")
            return True  # Assume valid if we can't test
    
    def create_tap_structure(self, version: str, formula_path: Path) -> Path:
        """
        Create Homebrew tap directory structure.
        
        Args:
            version: Version string
            formula_path: Path to formula file
            
        Returns:
            Path to tap directory
        """
        tap_dir = self.config.get_dist_dir(version) / "homebrew-tap"
        tap_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Formula directory
        formula_dir = tap_dir / "Formula"
        formula_dir.mkdir(exist_ok=True)
        
        # Copy formula to tap directory
        tap_formula_path = formula_dir / "giv.rb"
        import shutil
        shutil.copy2(formula_path, tap_formula_path)
        
        # Create tap README
        readme_content = f"""# Homebrew Tap for giv CLI

This is the official Homebrew tap for the giv CLI tool.

## Installation

```bash
brew tap giv-cli/tap
brew install giv
```

## About

giv is a Git history AI assistant CLI tool that generates commit messages,
changelogs, release notes, and announcements using AI.

- Homepage: https://github.com/giv-cli/giv-py
- Version: {version}
"""
        
        with open(tap_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Homebrew tap structure created: {tap_dir}")
        return tap_dir


def main():
    """CLI interface for Homebrew builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Homebrew formula for giv CLI")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--test", action="store_true", help="Test formula syntax")
    parser.add_argument("--create-tap", action="store_true", help="Create tap directory structure")
    
    args = parser.parse_args()
    
    builder = HomebrewBuilder()
    
    # Build formula
    formula_path = builder.build_formula(args.version)
    
    # Test formula
    if args.test:
        builder.test_formula(formula_path)
    
    # Create tap structure
    if args.create_tap:
        version = args.version or builder.version_manager.get_version()
        builder.create_tap_structure(version, formula_path)


if __name__ == "__main__":
    main()