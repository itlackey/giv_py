"""
PyPI package builder for giv CLI.

Builds Python source distributions and wheels for PyPI distribution.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir


class PyPIBuilder:
    """Builds PyPI packages (source distribution and wheel)."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize PyPI builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
    
    def build_packages(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Build both source distribution and wheel using Poetry.
        
        Args:
            version: Version to build (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Dictionary mapping package type to package path
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir
            
        print(f"🔨 Building PyPI packages for version {version}")
        
        ensure_dir(output_dir)
        
        # Use Poetry to build packages
        cmd = ["poetry", "build", "--output", str(output_dir)]
        
        try:
            subprocess.run(
                cmd, 
                cwd=self.config.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Poetry build completed")
            
            # Find built packages
            results = {}
            
            # Look for wheel
            wheel_files = list(output_dir.glob("*.whl"))
            if wheel_files:
                results["wheel"] = wheel_files[-1]  # Get most recent
                print(f"📦 Wheel: {results['wheel'].name}")
            
            # Look for source distribution
            sdist_files = list(output_dir.glob("*.tar.gz"))
            if sdist_files:
                results["sdist"] = sdist_files[-1]  # Get most recent
                print(f"📦 Source dist: {results['sdist'].name}")
            
            if not results:
                raise RuntimeError("No packages were built")
                
            return results
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Poetry build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            raise RuntimeError(f"Failed to build packages: {e}")
    
    def validate_packages(self, packages: Dict[str, Path]) -> bool:
        """
        Validate built packages using twine.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if all packages are valid
        """
        print("🔍 Validating PyPI packages...")
        
        package_paths = list(packages.values())
        if not package_paths:
            print("No packages to validate")
            return False
        
        try:
            cmd = [sys.executable, "-m", "twine", "check"] + [str(p) for p in package_paths]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ All packages passed validation")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Package validation failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    def upload_to_test_pypi(self, packages: Dict[str, Path]) -> bool:
        """
        Upload packages to Test PyPI.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if upload successful
        """
        print("🚀 Uploading to Test PyPI...")
        
        package_paths = list(packages.values())
        if not package_paths:
            print("No packages to upload")
            return False
        
        cmd = [
            sys.executable, "-m", "twine", "upload",
            "--repository", "testpypi",
            "--non-interactive"
        ] + [str(p) for p in package_paths]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Upload to Test PyPI successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload to Test PyPI failed: {e}")
            return False
    
    def upload_to_pypi(self, packages: Dict[str, Path]) -> bool:
        """
        Upload packages to PyPI.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if upload successful
        """
        print("🚀 Uploading to PyPI...")
        
        package_paths = list(packages.values())
        if not package_paths:
            print("No packages to upload")
            return False
        
        cmd = [
            sys.executable, "-m", "twine", "upload",
            "--non-interactive"
        ] + [str(p) for p in package_paths]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Upload to PyPI successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Upload to PyPI failed: {e}")
            return False


def main():
    """CLI interface for PyPI builder."""
    parser = argparse.ArgumentParser(description="Build and publish PyPI packages")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--build-only", action="store_true", help="Build packages only")
    parser.add_argument("--test-pypi", action="store_true", help="Upload to Test PyPI")
    parser.add_argument("--pypi", action="store_true", help="Upload to PyPI")
    parser.add_argument("--validate", action="store_true", help="Validate packages only")
    parser.add_argument("--output-dir", type=Path, help="Output directory for packages")
    
    args = parser.parse_args()
    
    try:
        builder = PyPIBuilder()
        
        if args.validate:
            # Find existing packages to validate
            output_dir = args.output_dir or builder.config.dist_dir
            packages = {}
            
            for sdist_file in output_dir.glob("*.tar.gz"):
                packages["sdist"] = sdist_file
            for wheel_file in output_dir.glob("*.whl"):
                packages["wheel"] = wheel_file
            
            if packages:
                valid = builder.validate_packages(packages)
                sys.exit(0 if valid else 1)
            else:
                print("No packages found to validate")
                sys.exit(1)
        
        # Build packages
        packages = builder.build_packages(args.version, args.output_dir)
        
        if not packages:
            print("❌ No packages were built")
            sys.exit(1)
        
        # Validate packages (skip if twine not available)
        try:
            if not builder.validate_packages(packages):
                print("❌ Package validation failed")
                # Don't exit - validation is optional for build-only
        except Exception as e:
            print(f"⚠️  Package validation skipped: {e}")
        
        if args.build_only:
            print("✅ Build completed successfully")
            return
        
        # Upload packages
        if args.test_pypi:
            if not builder.upload_to_test_pypi(packages):
                sys.exit(1)
        elif args.pypi:
            if not builder.upload_to_pypi(packages):
                sys.exit(1)
        
        print("✅ PyPI build and publish completed successfully")
        
    except Exception as e:
        print(f"❌ PyPI build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()