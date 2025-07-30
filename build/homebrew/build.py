"""
Homebrew formula builder for giv CLI.

Generates Homebrew formulas that reference binary releases.
"""
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir, calculate_sha256, replace_template_vars
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir, calculate_sha256, replace_template_vars


class HomebrewBuilder:
    """Builds Homebrew formula for binary distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Homebrew builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "giv.rb"
    
    def build_formula(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build Homebrew formula.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to generated formula
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir
            
        print(f"Building Homebrew formula for version {version}")
        
        ensure_dir(output_dir)
        
        # Read template
        if not self.template_file.exists():
            raise FileNotFoundError(f"Homebrew template not found: {self.template_file}")
            
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Find binary files and calculate checksums - always look in main dist directory
        binary_path = self.config.dist_dir / "giv-macos-x86_64"
        arm_binary_path = self.config.dist_dir / "giv-macos-arm64"
        
        variables = {
            "VERSION": version,
            "HOMEPAGE": self.config.homepage,
            "DESCRIPTION": self.config.description,
        }
        
        # Add checksums if binaries exist
        if binary_path.exists():
            variables["MACOS_X86_64_SHA256"] = calculate_sha256(binary_path)
            variables["MACOS_X86_64_URL"] = self.config.get_github_release_url(version, binary_path.name)
        
        if arm_binary_path.exists():
            variables["MACOS_ARM64_SHA256"] = calculate_sha256(arm_binary_path)
            variables["MACOS_ARM64_URL"] = self.config.get_github_release_url(version, arm_binary_path.name)
        
        # Replace template variables
        formula_content = replace_template_vars(template, variables)
        
        # Write formula
        formula_path = output_dir / "giv.rb"
        with open(formula_path, 'w') as f:
            f.write(formula_content)
        
        print(f"Package: Homebrew formula: {formula_path.name}")
        return formula_path
    
    def validate_formula(self, formula_path: Path) -> bool:
        """
        Validate Homebrew formula syntax.
        
        Args:
            formula_path: Path to formula file
            
        Returns:
            True if formula is valid
        """
        print("Validating Validating Homebrew formula...")
        
        try:
            cmd = ["brew", "style", str(formula_path)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("SUCCESS: Homebrew formula syntax is valid")
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Homebrew formula validation failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        except FileNotFoundError:
            print("WARNING:  brew command not found, skipping validation")
            return True

    def create_tap_structure(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Create Homebrew tap directory structure.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to tap directory
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / version
        
        # Create tap structure: homebrew-tap/Formula/
        tap_dir = output_dir / "homebrew-tap"
        formula_dir = tap_dir / "Formula"
        ensure_dir(formula_dir)
        
        # Build and place formula in tap structure
        formula_path = self.build_formula(version, formula_dir)
        
        # Create README for tap
        readme_content = f"""# Homebrew Tap for giv CLI

This is the official Homebrew tap for giv CLI version {version}.

## Installation

```bash
brew tap giv-cli/tap
brew install giv
```

## Updating

```bash
brew update
brew upgrade giv
```
"""
        readme_path = tap_dir / "README.md"
        readme_path.write_text(readme_content)
        
        print(f"Created Homebrew tap structure at: {tap_dir}")
        return tap_dir


def main():
    """CLI interface for Homebrew builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Homebrew formula")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for formula")
    parser.add_argument("--validate", action="store_true", help="Validate formula only")
    parser.add_argument("--create-tap", action="store_true", help="Create Homebrew tap structure")
    
    args = parser.parse_args()
    
    try:
        builder = HomebrewBuilder()
        
        if args.create_tap:
            # Create Homebrew tap structure
            tap_dir = builder.create_tap_structure(args.version, args.output_dir)
            print(f"SUCCESS: Homebrew tap created at {tap_dir}")
            return
        
        if args.validate:
            # Find existing formula to validate
            output_dir = args.output_dir or builder.config.dist_dir
            formula_path = output_dir / "giv.rb"
            
            if formula_path.exists():
                valid = builder.validate_formula(formula_path)
                sys.exit(0 if valid else 1)
            else:
                print("No formula found to validate")
                sys.exit(1)
        
        # Build formula
        formula_path = builder.build_formula(args.version, args.output_dir)
        
        if not formula_path.exists():
            print("ERROR: No formula was built")
            sys.exit(1)
        
        # Validate formula (optional)
        try:
            builder.validate_formula(formula_path)
        except Exception as e:
            print(f"WARNING:  Formula validation skipped: {e}")
        
        print("SUCCESS: Homebrew formula build completed successfully")
        
    except Exception as e:
        print(f"ERROR: Homebrew formula build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
