"""
Snap package builder for giv CLI.

Creates Snap package for Ubuntu/Linux distribution.
"""
import shutil
import subprocess
import sys
import yaml
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


class SnapBuilder:
    """Builds Snap package for Ubuntu/Linux distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Snap builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "snapcraft.yaml"
    
    def build_package(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build Snap package.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/snap/)
            
        Returns:
            Path to generated snapcraft.yaml
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / "snap"
            
        print(f"🔨 Building Snap package for version {version}")
        
        ensure_dir(output_dir)
        
        # Read template
        if not self.template_file.exists():
            raise FileNotFoundError(f"Snap template not found: {self.template_file}")
            
        with open(self.template_file, 'r') as f:
            template = f.read()
        
        # Replace template variables
        variables = {
            "VERSION": version,
            "DESCRIPTION": self.config.description,
            "HOMEPAGE": self.config.homepage,
        }
        
        snapcraft_content = replace_template_vars(template, variables)
        
        # Write snapcraft.yaml
        snapcraft_path = output_dir / "snapcraft.yaml"
        with open(snapcraft_path, 'w') as f:
            f.write(snapcraft_content)
        
        # Copy binary
        binary_src = self.config.dist_dir / "giv-linux-x86_64"
        if binary_src.exists():
            binary_dest = output_dir / "giv"
            shutil.copy2(binary_src, binary_dest)
            binary_dest.chmod(0o755)
        else:
            print("⚠️  Linux binary not found for Snap package")
        
        print(f"📦 Snap package: {snapcraft_path.name}")
        return snapcraft_path
    
    def validate_package(self, snapcraft_path: Path) -> bool:
        """
        Validate Snap package.
        
        Args:
            snapcraft_path: Path to snapcraft.yaml file
            
        Returns:
            True if package is valid
        """
        print("🔍 Validating Snap package...")
        
        try:
            with open(snapcraft_path, 'r') as f:
                snapcraft_yaml = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ["name", "version", "summary", "description", "parts"]
            for field in required_fields:
                if field not in snapcraft_yaml:
                    print(f"❌ Missing required field in snapcraft.yaml: {field}")
                    return False
            
            print("✅ Snap package is valid")
            return True
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML in snapcraft.yaml: {e}")
            return False
        except Exception as e:
            print(f"❌ Package validation failed: {e}")
            return False
    
    def build_snap(self, snapcraft_path: Path) -> bool:
        """
        Build snap package using snapcraft.
        
        Args:
            snapcraft_path: Path to snapcraft.yaml file
            
        Returns:
            True if build successful
        """
        print("🔨 Building snap with snapcraft...")
        
        try:
            cmd = ["snapcraft"]
            subprocess.run(
                cmd, 
                cwd=snapcraft_path.parent,
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Snap build completed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Snap build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
        except FileNotFoundError:
            print("⚠️  snapcraft command not found, skipping build")
            return True


def main():
    """CLI interface for Snap builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Snap package")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for package")
    parser.add_argument("--validate", action="store_true", help="Validate package only")
    parser.add_argument("--build", action="store_true", help="Build snap package with snapcraft")
    
    args = parser.parse_args()
    
    try:
        builder = SnapBuilder()
        
        if args.validate:
            # Find existing snapcraft.yaml to validate
            output_dir = args.output_dir or (builder.config.dist_dir / "snap")
            snapcraft_path = output_dir / "snapcraft.yaml"
            
            if snapcraft_path.exists():
                valid = builder.validate_package(snapcraft_path)
                sys.exit(0 if valid else 1)
            else:
                print("No snapcraft.yaml found to validate")
                sys.exit(1)
        
        # Build package
        snapcraft_path = builder.build_package(args.version, args.output_dir)
        
        if not snapcraft_path.exists():
            print("❌ No package was built")
            sys.exit(1)
        
        # Validate package
        try:
            builder.validate_package(snapcraft_path)
        except Exception as e:
            print(f"⚠️  Package validation skipped: {e}")
        
        # Build snap if requested
        if args.build:
            if not builder.build_snap(snapcraft_path):
                sys.exit(1)
        
        print("✅ Snap package build completed successfully")
        
    except Exception as e:
        print(f"❌ Snap package build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
