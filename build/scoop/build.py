"""
Scoop manifest builder for giv CLI.

Generates Scoop manifests that reference Windows binary releases.
"""
import json
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir, calculate_sha256
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir, calculate_sha256


class ScoopBuilder:
    """Builds Scoop manifest for Windows binary distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Scoop builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "giv.json"
    
    def build_manifest(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build Scoop manifest.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to generated manifest
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir
            
        print(f"Building Scoop manifest for version {version}")
        
        ensure_dir(output_dir)
        
        # Find Windows binary
        binary_path = output_dir / "giv-windows-x86_64.exe"
        
        if not binary_path.exists():
            raise FileNotFoundError(f"Windows binary not found: {binary_path}")
        
        # Calculate checksum
        checksum = calculate_sha256(binary_path)
        
        # Create manifest
        manifest = {
            "version": version,
            "description": self.config.description,
            "homepage": self.config.homepage,
            "license": self.config.license,
            "url": self.config.get_github_release_url(version, binary_path.name),
            "hash": checksum,
            "bin": binary_path.name,
            "shortcuts": [
                [binary_path.name, "giv"]
            ],
            "checkver": {
                "github": self.config.repository
            },
            "autoupdate": {
                "url": f"{self.config.repository}/releases/download/v$version/{binary_path.name}"
            }
        }
        
        # Write manifest
        manifest_path = output_dir / "giv.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)
        
        print(f"Package: Scoop manifest: {manifest_path.name}")
        return manifest_path
    
    def validate_manifest(self, manifest_path: Path) -> bool:
        """
        Validate Scoop manifest.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if manifest is valid
        """
        print("Validating Validating Scoop manifest...")
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Basic validation
            required_fields = ["version", "url", "hash", "bin"]
            for field in required_fields:
                if field not in manifest:
                    print(f"ERROR: Missing required field: {field}")
                    return False
            
            print("SUCCESS: Scoop manifest is valid")
            return True
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in manifest: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Manifest validation failed: {e}")
            return False


def main():
    """CLI interface for Scoop builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Scoop manifest")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for manifest")
    parser.add_argument("--validate", action="store_true", help="Validate manifest only")
    
    args = parser.parse_args()
    
    try:
        builder = ScoopBuilder()
        
        if args.validate:
            # Find existing manifest to validate
            output_dir = args.output_dir or builder.config.dist_dir
            manifest_path = output_dir / "giv.json"
            
            if manifest_path.exists():
                valid = builder.validate_manifest(manifest_path)
                sys.exit(0 if valid else 1)
            else:
                print("No manifest found to validate")
                sys.exit(1)
        
        # Build manifest
        manifest_path = builder.build_manifest(args.version, args.output_dir)
        
        if not manifest_path.exists():
            print("ERROR: No manifest was built")
            sys.exit(1)
        
        # Validate manifest
        try:
            builder.validate_manifest(manifest_path)
        except Exception as e:
            print(f"WARNING:  Manifest validation skipped: {e}")
        
        print("SUCCESS: Scoop manifest build completed successfully")
        
    except Exception as e:
        print(f"ERROR: Scoop manifest build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
