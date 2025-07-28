"""
PyPI package builder for giv CLI.

Builds Python source distributions and wheels for PyPI distribution.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

from ..core.config import BuildConfig
from ..core.version_manager import VersionManager


class PyPIBuilder:
    """Builds PyPI packages (source distribution and wheel)."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize PyPI builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
    
    def check_dependencies(self) -> None:
        """Check that required tools are available."""
        missing = []
        
        # Check build tools
        try:
            import build
        except ImportError:
            missing.append("build")
        
        try:
            import twine
        except ImportError:
            missing.append("twine")
        
        if missing:
            raise RuntimeError(f"Missing required dependencies: {', '.join(missing)}")
    
    def build_source_distribution(self, version: str) -> Path:
        """
        Build source distribution (sdist).
        
        Args:
            version: Version to build
            
        Returns:
            Path to built sdist
        """
        print(f"Building source distribution for version {version}")
        
        # Ensure version is correct in all files
        self.version_manager.sync_versions()
        
        # Build directory
        dist_dir = self.config.get_dist_dir(version) / "pypi"
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Build command
        cmd = [
            sys.executable, "-m", "build",
            "--sdist",
            "--outdir", str(dist_dir),
            str(self.config.project_root)
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.config.project_root)
            
            # Find the built sdist
            sdist_files = list(dist_dir.glob("*.tar.gz"))
            if not sdist_files:
                raise RuntimeError("Source distribution not found after build")
            
            sdist_path = sdist_files[0]
            print(f"✓ Built source distribution: {sdist_path}")
            return sdist_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to build source distribution: {e}")
    
    def build_wheel(self, version: str) -> Path:
        """
        Build wheel distribution.
        
        Args:
            version: Version to build
            
        Returns:
            Path to built wheel
        """
        print(f"Building wheel for version {version}")
        
        # Ensure version is correct in all files
        self.version_manager.sync_versions()
        
        # Build directory
        dist_dir = self.config.get_dist_dir(version) / "pypi"
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Build command
        cmd = [
            sys.executable, "-m", "build",
            "--wheel",
            "--outdir", str(dist_dir),
            str(self.config.project_root)
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.config.project_root)
            
            # Find the built wheel
            wheel_files = list(dist_dir.glob("*.whl"))
            if not wheel_files:
                raise RuntimeError("Wheel not found after build")
            
            wheel_path = wheel_files[0]
            print(f"✓ Built wheel: {wheel_path}")
            return wheel_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to build wheel: {e}")
    
    def build_packages(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build both source distribution and wheel.
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Dictionary mapping package type to package path
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Building PyPI packages for version {version}")
        
        # Check dependencies
        self.check_dependencies()
        
        results = {}
        
        # Build source distribution
        try:
            sdist_path = self.build_source_distribution(version)
            results["sdist"] = sdist_path
        except Exception as e:
            print(f"Warning: Failed to build source distribution: {e}")
        
        # Build wheel
        try:
            wheel_path = self.build_wheel(version)
            results["wheel"] = wheel_path
        except Exception as e:
            print(f"Warning: Failed to build wheel: {e}")
        
        return results
    
    def validate_packages(self, packages: Dict[str, Path]) -> bool:
        """
        Validate built packages using twine.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if all packages are valid
        """
        print("Validating PyPI packages...")
        
        valid = True
        for package_type, package_path in packages.items():
            try:
                cmd = [sys.executable, "-m", "twine", "check", str(package_path)]
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✓ {package_type}: {package_path.name}")
            except subprocess.CalledProcessError as e:
                print(f"✗ {package_type}: {package_path.name} - {e}")
                valid = False
        
        return valid
    
    def upload_to_test_pypi(self, packages: Dict[str, Path]) -> bool:
        """
        Upload packages to Test PyPI.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if upload successful
        """
        print("Uploading to Test PyPI...")
        
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
            print("✓ Upload to Test PyPI successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Upload to Test PyPI failed: {e}")
            return False
    
    def upload_to_pypi(self, packages: Dict[str, Path]) -> bool:
        """
        Upload packages to PyPI.
        
        Args:
            packages: Dictionary mapping package type to package path
            
        Returns:
            True if upload successful
        """
        print("Uploading to PyPI...")
        
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
            print("✓ Upload to PyPI successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Upload to PyPI failed: {e}")
            return False


def main():
    """CLI interface for PyPI builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build and publish PyPI packages")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--build-only", action="store_true", help="Build packages only")
    parser.add_argument("--test-pypi", action="store_true", help="Upload to Test PyPI")
    parser.add_argument("--pypi", action="store_true", help="Upload to PyPI")
    parser.add_argument("--validate", action="store_true", help="Validate packages only")
    
    args = parser.parse_args()
    
    builder = PyPIBuilder()
    
    if args.validate:
        # Validate existing packages
        version = args.version or builder.version_manager.get_version()
        dist_dir = builder.config.get_dist_dir(version) / "pypi"
        
        packages = {}
        for sdist_file in dist_dir.glob("*.tar.gz"):
            packages["sdist"] = sdist_file
        for wheel_file in dist_dir.glob("*.whl"):
            packages["wheel"] = wheel_file
        
        if packages:
            valid = builder.validate_packages(packages)
            sys.exit(0 if valid else 1)
        else:
            print("No packages found to validate")
            sys.exit(1)
    
    # Build packages
    packages = builder.build_packages(args.version)
    
    if not packages:
        print("No packages were built")
        sys.exit(1)
    
    # Validate packages
    if not builder.validate_packages(packages):
        print("Package validation failed")
        sys.exit(1)
    
    if args.build_only:
        print("Build completed successfully")
        return
    
    # Upload packages
    if args.test_pypi:
        if not builder.upload_to_test_pypi(packages):
            sys.exit(1)
    
    if args.pypi:
        if not builder.upload_to_pypi(packages):
            sys.exit(1)
    
    print("PyPI build and publish completed successfully")


if __name__ == "__main__":
    main()