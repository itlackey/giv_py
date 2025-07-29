"""
NPM package builder for giv CLI.

Creates NPM package for Node.js distribution.
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir, copy_files
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir, copy_files


class NPMBuilder:
    """Builds NPM package for Node.js distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize NPM builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
    
    def build_package(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build NPM package.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/npm/)
            
        Returns:
            Path to generated package directory
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / "npm"
            
        print(f"🔨 Building NPM package for version {version}")
        
        ensure_dir(output_dir)
        
        # Create package.json
        package_json = {
            "name": "giv",
            "version": version,
            "description": self.config.description,
            "bin": {"giv": "bin/giv"},
            "files": [
                "bin/",
                "lib/",
                "README.md"
            ],
            "keywords": [
                "git",
                "cli", 
                "ai",
                "changelog",
                "history",
                "assistant",
                "release"
            ],
            "repository": self.config.repository,
            "homepage": self.config.homepage,
            "license": self.config.license,
            "preferGlobal": True,
            "engines": {
                "node": ">=12.0.0"
            }
        }
        
        # Write package.json
        package_json_path = output_dir / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Create bin directory and copy binary
        bin_dir = output_dir / "bin"
        ensure_dir(bin_dir)
        
        # Find appropriate binary based on platform
        for platform in ["linux-x86_64", "darwin-x86_64", "darwin-arm64"]:
            binary_path = self.config.dist_dir / f"giv-{platform}"
            if binary_path.exists():
                # Copy binary
                dest_binary = bin_dir / "giv"
                shutil.copy2(binary_path, dest_binary)
                # Make executable
                dest_binary.chmod(0o755)
                break
        else:
            print("⚠️  No binary found for NPM package")
        
        # Copy README
        readme_src = self.config.project_root / "README.md"
        if readme_src.exists():
            shutil.copy2(readme_src, output_dir / "README.md")
        
        print(f"📦 NPM package: {output_dir.name}")
        return output_dir
    
    def validate_package(self, package_dir: Path) -> bool:
        """
        Validate NPM package.
        
        Args:
            package_dir: Path to package directory
            
        Returns:
            True if package is valid
        """
        print("🔍 Validating NPM package...")
        
        try:
            # Check package.json exists and is valid
            package_json_path = package_dir / "package.json"
            if not package_json_path.exists():
                print("❌ package.json not found")
                return False
            
            with open(package_json_path, 'r') as f:
                package_json = json.load(f)
            
            # Check required fields
            required_fields = ["name", "version", "bin"]
            for field in required_fields:
                if field not in package_json:
                    print(f"❌ Missing required field in package.json: {field}")
                    return False
            
            # Check binary exists
            bin_path = package_dir / "bin" / "giv"
            if not bin_path.exists():
                print("❌ Binary not found in bin/giv")
                return False
            
            print("✅ NPM package is valid")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in package.json: {e}")
            return False
        except Exception as e:
            print(f"❌ Package validation failed: {e}")
            return False


def main():
    """CLI interface for NPM builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build NPM package")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for package")
    parser.add_argument("--validate", action="store_true", help="Validate package only")
    
    args = parser.parse_args()
    
    try:
        builder = NPMBuilder()
        
        if args.validate:
            # Find existing package to validate
            output_dir = args.output_dir or (builder.config.dist_dir / "npm")
            
            if output_dir.exists():
                valid = builder.validate_package(output_dir)
                sys.exit(0 if valid else 1)
            else:
                print("No package found to validate")
                sys.exit(1)
        
        # Build package
        package_dir = builder.build_package(args.version, args.output_dir)
        
        if not package_dir.exists():
            print("❌ No package was built")
            sys.exit(1)
        
        # Validate package
        try:
            builder.validate_package(package_dir)
        except Exception as e:
            print(f"⚠️  Package validation skipped: {e}")
        
        print("✅ NPM package build completed successfully")
        
    except Exception as e:
        print(f"❌ NPM package build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
