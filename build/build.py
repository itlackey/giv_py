#!/usr/bin/env python3
"""
Unified build system for giv CLI.

Coordinates building of binaries and packages for all platforms and package managers.
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add build directory to path
sys.path.append(str(Path(__file__).parent))

from core.config import BuildConfig
from core.version_manager import VersionManager
from core.utils import ensure_dir


class UnifiedBuilder:
    """Unified builder for all giv CLI packages."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize unified builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Import builders
        self.builders = {}
        self._load_builders()
    
    def _load_builders(self):
        """Load all available builders."""
        try:
            from pypi import PyPIBuilder
            self.builders['pypi'] = PyPIBuilder
        except ImportError as e:
            print(f"⚠️  PyPIBuilder not available: {e}")
        
        try:
            from homebrew.build import HomebrewBuilder
            self.builders['homebrew'] = HomebrewBuilder
        except ImportError as e:
            print(f"⚠️  HomebrewBuilder not available: {e}")
        
        try:
            from scoop.build import ScoopBuilder
            self.builders['scoop'] = ScoopBuilder
        except ImportError as e:
            print(f"⚠️  ScoopBuilder not available: {e}")
        
        try:
            from npm.build import NPMBuilder
            self.builders['npm'] = NPMBuilder
        except ImportError as e:
            print(f"⚠️  NPMBuilder not available: {e}")
        
        try:
            from snap.build import SnapBuilder
            self.builders['snap'] = SnapBuilder
        except ImportError as e:
            print(f"⚠️  SnapBuilder not available: {e}")
        
        try:
            from flatpak.build import FlatpakBuilder
            self.builders['flatpak'] = FlatpakBuilder
        except ImportError as e:
            print(f"⚠️  FlatpakBuilder not available: {e}")
    
    def build_binaries(self, platforms: Optional[List[str]] = None) -> Dict[str, Path]:
        """
        Build binaries for specified platforms.
        
        Args:
            platforms: List of platforms to build for (all supported if None)
            
        Returns:
            Dictionary mapping platform to binary path
        """
        if platforms is None:
            platforms = list(self.config.platforms.keys())
        
        print("🔨 Building binaries...")
        
        binaries = {}
        
        # For now, use the simple binary builder for current platform only
        from pathlib import Path
        import subprocess
        
        # Build current platform binary
        build_script = self.config.project_root / "build" / "build_binary.py"
        if build_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(build_script)],
                    cwd=self.config.project_root,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # Find the built binary
                for platform, platform_info in self.config.platforms.items():
                    binary_path = self.config.dist_dir / platform_info["binary_name"]
                    if binary_path.exists():
                        binaries[platform] = binary_path
                        print(f"✅ Built binary: {binary_path.name}")
                        break
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Binary build failed: {e}")
                if e.stdout:
                    print("STDOUT:", e.stdout)
                if e.stderr:
                    print("STDERR:", e.stderr)
        
        return binaries
    
    def build_packages(self, package_types: Optional[List[str]] = None, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build packages for specified package managers.
        
        Args:
            package_types: List of package types to build (all available if None)
            version: Version to build (auto-detected if None)
            
        Returns:
            Dictionary mapping package type to package path
        """
        if package_types is None:
            package_types = list(self.builders.keys())
        
        if version is None:
            version = self.version_manager.get_build_version()
        
        print(f"📦 Building packages for version {version}...")
        
        packages = {}
        
        for package_type in package_types:
            if package_type not in self.builders:
                print(f"⚠️  Builder not available for {package_type}")
                continue
            
            try:
                builder_class = self.builders[package_type]
                builder = builder_class(self.config)
                
                print(f"\n🔨 Building {package_type} package...")
                
                if package_type == 'pypi':
                    result = builder.build_packages(version)
                    if result:
                        packages[package_type] = result
                elif hasattr(builder, 'build_formula'):
                    # Homebrew
                    result = builder.build_formula(version)
                    packages[package_type] = result
                elif hasattr(builder, 'build_manifest'):
                    # Scoop
                    result = builder.build_manifest(version)
                    packages[package_type] = result
                elif hasattr(builder, 'build_package'):
                    # NPM, Snap, Flatpak
                    result = builder.build_package(version)
                    packages[package_type] = result
                
                print(f"✅ {package_type} package built successfully")
                
            except Exception as e:
                print(f"❌ Failed to build {package_type} package: {e}")
                continue
        
        return packages
    
    def build_all(self, version: Optional[str] = None) -> Dict[str, any]:
        """
        Build all binaries and packages.
        
        Args:
            version: Version to build (auto-detected if None)
            
        Returns:
            Dictionary with build results
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        print(f"🚀 Building all packages for giv CLI version {version}")
        
        # Ensure dist directory exists
        ensure_dir(self.config.dist_dir)
        
        # Build binaries first
        binaries = self.build_binaries()
        
        # Build packages
        packages = self.build_packages(version=version)
        
        results = {
            'version': version,
            'binaries': binaries,
            'packages': packages
        }
        
        # Summary
        print(f"\n✅ Build Summary:")
        print(f"Version: {version}")
        print(f"Binaries: {len(binaries)} built")
        print(f"Packages: {len(packages)} built")
        
        if binaries:
            print("\nBinaries:")
            for platform, path in binaries.items():
                print(f"  - {platform}: {path.name}")
        
        if packages:
            print("\nPackages:")
            for pkg_type, path in packages.items():
                if isinstance(path, dict):
                    print(f"  - {pkg_type}: {len(path)} files")
                    for sub_type, sub_path in path.items():
                        print(f"    - {sub_type}: {sub_path.name}")
                else:
                    print(f"  - {pkg_type}: {path.name}")
        
        return results


def main():
    """CLI interface for unified builder."""
    parser = argparse.ArgumentParser(description="Unified build system for giv CLI")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--binaries-only", action="store_true", help="Build binaries only")
    parser.add_argument("--packages-only", action="store_true", help="Build packages only") 
    parser.add_argument("--package-types", nargs="+", help="Specific package types to build")
    parser.add_argument("--platforms", nargs="+", help="Specific platforms to build for")
    parser.add_argument("--list-builders", action="store_true", help="List available builders")
    
    args = parser.parse_args()
    
    try:
        builder = UnifiedBuilder()
        
        if args.list_builders:
            print("Available builders:")
            for name in builder.builders.keys():
                print(f"  - {name}")
            return
        
        if args.binaries_only:
            binaries = builder.build_binaries(args.platforms)
            print(f"✅ Built {len(binaries)} binaries")
        elif args.packages_only:
            packages = builder.build_packages(args.package_types, args.version)
            print(f"✅ Built {len(packages)} packages")
        else:
            results = builder.build_all(args.version)
            print("✅ Build completed successfully")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
