#!/usr/bin/env python3
"""
Main build orchestrator for giv CLI.

This script replaces the Bash-based build system with a Python-based
approach that builds cross-platform binaries and packages.

https://crushingcode.nisrulz.com/blog/cross-compilation-adventures/cross-compilation-adventures-python/
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add build directory to path so we can import build modules
build_dir = Path(__file__).parent
sys.path.insert(0, str(build_dir))

# Import build modules
try:
    from core.config import BuildConfig
    from core.platform_detector import PlatformDetector
    from core.version_manager import VersionManager
    from pyinstaller.binary_builder import BinaryBuilder
    from pyinstaller.build_all_platforms import CrossPlatformBuilder
except ImportError as e:
    print(f"Error importing build modules: {e}")
    print("Make sure you're running this script from the project root or build directory")
    sys.exit(1)


class BuildOrchestrator:
    """Main build orchestrator for all giv CLI artifacts."""
    
    def __init__(self):
        """Initialize build orchestrator."""
        self.config = BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        self.platform_detector = PlatformDetector()
        self.binary_builder = BinaryBuilder(self.config)
        self.cross_platform_builder = CrossPlatformBuilder(self.config)
    
    def build_binaries(self, version: Optional[str] = None, platforms: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Build binaries for specified platforms.
        
        Args:
            version: Version to build (auto-detected if not provided)
            platforms: List of platform-arch targets (all if not provided)
            
        Returns:
            Dictionary mapping platform-arch to binary path
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Building binaries for version {version}")
        
        if platforms:
            # Build specific platforms
            results = {}
            for platform_target in platforms:
                try:
                    if "-" not in platform_target:
                        raise ValueError(f"Invalid platform target format: {platform_target}")
                    
                    platform_name, arch = platform_target.split("-", 1)
                    binary_path = self.binary_builder._build_binary(version, platform_name, arch)
                    
                    if self.binary_builder.test_binary(binary_path):
                        results[platform_target] = binary_path
                    else:
                        print(f"Warning: Binary for {platform_target} failed tests")
                        
                except Exception as e:
                    print(f"Error building {platform_target}: {e}")
                    continue
            
            return results
        else:
            # Build all available platforms
            return self.cross_platform_builder.build_all_methods(version)
    
    def build_packages(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build packages for distribution (PyPI, etc.).
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Dictionary mapping package type to package path
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Building packages for version {version}")
        
        results = {}
        
        # Build Python source distribution and wheel
        try:
            from pypi.build import PyPIBuilder
            pypi_builder = PyPIBuilder(self.config)
            pypi_results = pypi_builder.build_packages(version)
            results.update(pypi_results)
        except ImportError:
            print("Warning: PyPI builder not available")
        except Exception as e:
            print(f"Error building PyPI packages: {e}")
        
        return results
    
    def create_release_artifacts(self, version: Optional[str] = None) -> Path:
        """
        Create complete release artifacts including binaries and packages.
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Path to release artifacts directory
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Creating release artifacts for version {version}")
        print("=" * 50)
        
        # Build binaries
        print("\\n1. Building binaries...")
        binaries = self.build_binaries(version)
        
        # Build packages
        print("\\n2. Building packages...")
        packages = self.build_packages(version)
        
        # Create release assets
        print("\\n3. Creating release assets...")
        assets_dir = self.cross_platform_builder.create_release_assets(version, binaries)
        
        # Copy packages to assets directory
        for package_type, package_path in packages.items():
            dest_path = assets_dir / package_path.name
            if package_path != dest_path:
                import shutil
                shutil.copy2(package_path, dest_path)
        
        print(f"\\n✓ Release artifacts ready in: {assets_dir}")
        
        # Print summary
        print(f"\\nRelease Summary for v{version}:")
        print("=" * 40)
        print(f"Binaries: {len(binaries)}")
        for platform_arch in sorted(binaries.keys()):
            print(f"  ✓ {platform_arch}")
        
        print(f"Packages: {len(packages)}")
        for package_type in sorted(packages.keys()):
            print(f"  ✓ {package_type}")
        
        return assets_dir
    
    def clean(self, version: Optional[str] = None) -> None:
        """
        Clean build artifacts.
        
        Args:
            version: Specific version to clean (all if not provided)
        """
        if version:
            # Clean specific version
            version_dir = self.config.get_dist_dir(version)
            if version_dir.exists():
                import shutil
                shutil.rmtree(version_dir)
                print(f"✓ Cleaned build artifacts for version {version}")
            else:
                print(f"No build artifacts found for version {version}")
        else:
            # Clean all build artifacts
            if self.config.dist_root.exists():
                import shutil
                shutil.rmtree(self.config.dist_root)
                print("✓ Cleaned all build artifacts")
            
            if self.config.temp_root.exists():
                import shutil
                shutil.rmtree(self.config.temp_root)
                print("✓ Cleaned temporary files")
    
    def status(self) -> None:
        """Show build system status and capabilities."""
        print("Build System Status")
        print("=" * 30)
        
        # Version information
        try:
            version = self.version_manager.get_version()
            print(f"Current Version: {version}")
        except Exception as e:
            print(f"Version Detection: Error - {e}")
        
        print()
        
        # Platform information
        self.platform_detector.print_platform_info()
        
        # Build directories
        print("Build Directories:")
        print(f"  Project Root: {self.config.project_root}")
        print(f"  Build Root: {self.config.build_root}")
        print(f"  Dist Root: {self.config.dist_root}")
        print(f"  Temp Root: {self.config.temp_root}")
        print()
        
        # Existing artifacts
        if self.config.dist_root.exists():
            versions = [d.name for d in self.config.dist_root.iterdir() if d.is_dir()]
            if versions:
                print(f"Built Versions: {', '.join(sorted(versions))}")
            else:
                print("Built Versions: None")
        else:
            print("Built Versions: None")


def main():
    """CLI interface for build orchestrator."""
    parser = argparse.ArgumentParser(
        description="Build giv CLI binaries and packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s binaries                     # Build binaries for all platforms
  %(prog)s binaries --platforms linux-x86_64,darwin-arm64
  %(prog)s packages                     # Build packages (PyPI, etc.)
  %(prog)s release                      # Build complete release artifacts
  %(prog)s clean                        # Clean all build artifacts
  %(prog)s status                       # Show build system status
        """
    )
    
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Build commands")
    
    # Binaries command
    binaries_parser = subparsers.add_parser("binaries", help="Build binaries")
    binaries_parser.add_argument("--platforms", help="Comma-separated list of platform-arch targets")
    binaries_parser.add_argument("--test", action="store_true", help="Test built binaries")
    binaries_parser.add_argument("--optimize", action="store_true", help="Optimize binaries")
    
    # Packages command
    packages_parser = subparsers.add_parser("packages", help="Build packages")
    
    # Release command
    release_parser = subparsers.add_parser("release", help="Build complete release artifacts")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean build artifacts")
    clean_parser.add_argument("--version", help="Clean specific version only")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show build system status")
    
    args = parser.parse_args()
    
    # Default to status if no command provided
    if not args.command:
        args.command = "status"
    
    orchestrator = BuildOrchestrator()
    
    try:
        if args.command == "binaries":
            platforms = None
            if args.platforms:
                platforms = [p.strip() for p in args.platforms.split(",")]
            
            results = orchestrator.build_binaries(args.version, platforms)
            
            if args.test:
                print("\\nTesting binaries...")
                for platform_arch, binary_path in results.items():
                    print(f"Testing {platform_arch}...")
                    orchestrator.binary_builder.test_binary(binary_path)
            
            if args.optimize:
                print("\\nOptimizing binaries...")
                for platform_arch, binary_path in results.items():
                    print(f"Optimizing {platform_arch}...")
                    orchestrator.binary_builder.optimize_binary(binary_path)
        
        elif args.command == "packages":
            orchestrator.build_packages(args.version)
        
        elif args.command == "release":
            orchestrator.create_release_artifacts(args.version)
        
        elif args.command == "clean":
            orchestrator.clean(args.version)
        
        elif args.command == "status":
            orchestrator.status()
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\\nBuild interrupted by user")
        return 1
    except Exception as e:
        print(f"\\nBuild failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())