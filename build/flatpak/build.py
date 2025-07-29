"""
Flatpak package builder for giv CLI.

Creates Flatpak package for Linux distribution.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir, replace_template_vars
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir, replace_template_vars


class FlatpakBuilder:
    """Builds Flatpak package for Linux distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Flatpak builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
    
    def build_package(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build Flatpak package.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/flatpak/)
            
        Returns:
            Path to generated flatpak manifest
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / "flatpak"
            
        print(f"🔨 Building Flatpak package for version {version}")
        
        ensure_dir(output_dir)
        
        # Create Flatpak manifest
        manifest = {
            "app-id": "com.github.giv-cli.giv",
            "runtime": "org.freedesktop.Platform",
            "runtime-version": "23.08",
            "sdk": "org.freedesktop.Sdk",
            "command": "giv",
            "modules": [
                {
                    "name": "giv",
                    "buildsystem": "simple",
                    "build-commands": [
                        "install -D giv /app/bin/giv"
                    ],
                    "sources": [
                        {
                            "type": "file",
                            "url": self.config.get_github_release_url(version, "giv-linux-x86_64"),
                            "dest-filename": "giv"
                        }
                    ]
                }
            ]
        }
        
        # Write manifest
        manifest_path = output_dir / "com.github.giv-cli.giv.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Copy binary for local building
        binary_src = self.config.dist_dir / "giv-linux-x86_64"
        if binary_src.exists():
            binary_dest = output_dir / "giv"
            shutil.copy2(binary_src, binary_dest)
            binary_dest.chmod(0o755)
        else:
            print("⚠️  Linux binary not found for Flatpak package")
        
        print(f"📦 Flatpak package: {manifest_path.name}")
        return manifest_path
    
    def validate_package(self, manifest_path: Path) -> bool:
        """
        Validate Flatpak package.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if package is valid
        """
        print("🔍 Validating Flatpak package...")
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check required fields
            required_fields = ["app-id", "runtime", "runtime-version", "sdk", "command", "modules"]
            for field in required_fields:
                if field not in manifest:
                    print(f"❌ Missing required field in manifest: {field}")
                    return False
            
            print("✅ Flatpak package is valid")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in manifest: {e}")
            return False
        except Exception as e:
            print(f"❌ Package validation failed: {e}")
            return False
    
    def build_flatpak(self, manifest_path: Path) -> bool:
        """
        Build flatpak package using flatpak-builder.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if build successful
        """
        print("🔨 Building flatpak with flatpak-builder...")
        
        try:
            build_dir = manifest_path.parent / "build"
            cmd = [
                "flatpak-builder",
                "--install-deps-from=flathub",
                "--force-clean",
                str(build_dir),
                str(manifest_path)
            ]
            subprocess.run(
                cmd, 
                cwd=manifest_path.parent,
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Flatpak build completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Flatpak build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        except FileNotFoundError:
            print("⚠️  flatpak-builder command not found, skipping build")
            return True


def main():
    """CLI interface for Flatpak builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Flatpak package")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for package")
    parser.add_argument("--validate", action="store_true", help="Validate package only")
    parser.add_argument("--build", action="store_true", help="Build flatpak package")
    
    args = parser.parse_args()
    
    try:
        builder = FlatpakBuilder()
        
        if args.validate:
            # Find existing manifest to validate
            output_dir = args.output_dir or (builder.config.dist_dir / "flatpak")
            manifest_path = output_dir / "com.github.giv-cli.giv.json"
            
            if manifest_path.exists():
                valid = builder.validate_package(manifest_path)
                sys.exit(0 if valid else 1)
            else:
                print("No manifest found to validate")
                sys.exit(1)
        
        # Build package
        manifest_path = builder.build_package(args.version, args.output_dir)
        
        if not manifest_path.exists():
            print("❌ No package was built")
            sys.exit(1)
        
        # Validate package
        try:
            builder.validate_package(manifest_path)
        except Exception as e:
            print(f"⚠️  Package validation skipped: {e}")
        
        # Build flatpak if requested
        if args.build:
            if not builder.build_flatpak(manifest_path):
                sys.exit(1)
        
        print("✅ Flatpak package build completed successfully")
        
    except Exception as e:
        print(f"❌ Flatpak package build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
