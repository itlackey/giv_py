#!/usr/bin/env python3
"""
Publishing system for giv CLI.

Publishes packages to various package managers and repositories.
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add build directory to path
sys.path.append(str(Path(__file__).parent))

from core.config import BuildConfig
from core.version_manager import VersionManager


class UnifiedPublisher:
    """Unified publisher for all giv CLI packages."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize unified publisher."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Import builders/publishers
        self.publishers = {}
        self._load_publishers()
    
    def _load_publishers(self):
        """Load all available publishers."""
        try:
            from pypi import PyPIBuilder
            self.publishers['pypi'] = PyPIBuilder
        except ImportError as e:
            print(f"⚠️  PyPI publisher not available: {e}")
    
    def publish_pypi(self, test: bool = False) -> bool:
        """
        Publish to PyPI or Test PyPI.
        
        Args:
            test: Whether to publish to Test PyPI
            
        Returns:
            True if successful
        """
        if 'pypi' not in self.publishers:
            print("❌ PyPI publisher not available")
            return False
        
        try:
            builder = self.publishers['pypi'](self.config)
            
            # Find existing packages in dist/
            packages = {}
            for sdist_file in self.config.dist_dir.glob("*.tar.gz"):
                packages["sdist"] = sdist_file
            for wheel_file in self.config.dist_dir.glob("*.whl"):
                packages["wheel"] = wheel_file
            
            if not packages:
                print("❌ No PyPI packages found to publish")
                return False
            
            print(f"📦 Found packages: {list(packages.keys())}")
            
            if test:
                return builder.upload_to_test_pypi(packages)
            else:
                return builder.upload_to_pypi(packages)
                
        except Exception as e:
            print(f"❌ PyPI publish failed: {e}")
            return False
    
    def publish_github_release(self, version: Optional[str] = None) -> bool:
        """
        Create GitHub release with binaries.
        
        Args:
            version: Version to release (auto-detected if None)
            
        Returns:
            True if successful
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        print(f"🚀 Creating GitHub release for version {version}")
        
        # This would use GitHub CLI or API
        # For now, just show what would be uploaded
        release_files = []
        
        # Find binaries
        for platform_info in self.config.platforms.values():
            binary_path = self.config.dist_dir / platform_info["binary_name"]
            if binary_path.exists():
                release_files.append(binary_path)
        
        # Find packages
        for pkg_file in self.config.dist_dir.glob("*.tar.gz"):
            release_files.append(pkg_file)
        for pkg_file in self.config.dist_dir.glob("*.whl"):
            release_files.append(pkg_file)
        
        if release_files:
            print("📦 Files to include in release:")
            for file_path in release_files:
                print(f"  - {file_path.name}")
            
            # TODO: Implement actual GitHub release creation
            print("⚠️  GitHub release creation not yet implemented")
            print("   Use: gh release create v{version} {files}")
            return True
        else:
            print("❌ No files found for GitHub release")
            return False
    
    def show_status(self) -> None:
        """Show current publishing status."""
        version = self.version_manager.get_build_version()
        
        print(f"📊 Publishing Status for giv CLI version {version}")
        print("=" * 50)
        
        # Check what's built
        print("\n🔨 Built Assets:")
        
        # Binaries
        binary_count = 0
        for platform, platform_info in self.config.platforms.items():
            binary_path = self.config.dist_dir / platform_info["binary_name"]
            if binary_path.exists():
                print(f"  ✅ {platform}: {binary_path.name}")
                binary_count += 1
            else:
                print(f"  ❌ {platform}: Not built")
        
        # PyPI packages
        pypi_packages = []
        for sdist_file in self.config.dist_dir.glob("*.tar.gz"):
            pypi_packages.append(f"sdist: {sdist_file.name}")
        for wheel_file in self.config.dist_dir.glob("*.whl"):
            pypi_packages.append(f"wheel: {wheel_file.name}")
        
        if pypi_packages:
            print("  ✅ PyPI packages:")
            for pkg in pypi_packages:
                print(f"    - {pkg}")
        else:
            print("  ❌ PyPI packages: Not built")
        
        # Package manager configs
        print("\n📦 Package Manager Configs:")
        
        homebrew_formula = self.config.dist_dir / "giv.rb"
        if homebrew_formula.exists():
            print(f"  ✅ Homebrew: {homebrew_formula.name}")
        else:
            print("  ❌ Homebrew: Not built")
        
        scoop_manifest = self.config.dist_dir / "giv.json"
        if scoop_manifest.exists():
            print(f"  ✅ Scoop: {scoop_manifest.name}")
        else:
            print("  ❌ Scoop: Not built")
        
        npm_package = self.config.dist_dir / "npm"
        if npm_package.exists():
            print(f"  ✅ NPM: {npm_package.name}/")
        else:
            print("  ❌ NPM: Not built")
        
        snap_package = self.config.dist_dir / "snap"
        if snap_package.exists():
            print(f"  ✅ Snap: {snap_package.name}/")
        else:
            print("  ❌ Snap: Not built")
        
        flatpak_package = self.config.dist_dir / "flatpak"
        if flatpak_package.exists():
            print(f"  ✅ Flatpak: {flatpak_package.name}/")
        else:
            print("  ❌ Flatpak: Not built")
        
        print(f"\n📈 Summary:")
        print(f"  Binaries: {binary_count}/{len(self.config.platforms)} platforms")
        print(f"  PyPI packages: {len(pypi_packages)} files")
        print(f"  Version: {version}")


def main():
    """CLI interface for unified publisher."""
    parser = argparse.ArgumentParser(description="Publishing system for giv CLI")
    parser.add_argument("command", nargs="?", choices=["pypi", "test-pypi", "github", "all", "status"], 
                       help="Publishing command")
    parser.add_argument("--version", help="Version to publish (auto-detected if not provided)")
    
    args = parser.parse_args()
    
    try:
        publisher = UnifiedPublisher()
        
        if args.command == "status" or args.command is None:
            publisher.show_status()
            return
        
        if args.command == "pypi":
            success = publisher.publish_pypi(test=False)
            sys.exit(0 if success else 1)
        
        elif args.command == "test-pypi":
            success = publisher.publish_pypi(test=True)
            sys.exit(0 if success else 1)
        
        elif args.command == "github":
            success = publisher.publish_github_release(args.version)
            sys.exit(0 if success else 1)
        
        elif args.command == "all":
            print("🚀 Publishing to all channels...")
            
            # Publish to Test PyPI first
            print("\n1. Publishing to Test PyPI...")
            test_success = publisher.publish_pypi(test=True)
            
            if test_success:
                print("\n2. Creating GitHub release...")
                github_success = publisher.publish_github_release(args.version)
                
                if github_success:
                    print("\n3. Publishing to PyPI...")
                    pypi_success = publisher.publish_pypi(test=False)
                    
                    if pypi_success:
                        print("✅ All publishing completed successfully")
                    else:
                        print("❌ PyPI publishing failed")
                        sys.exit(1)
                else:
                    print("❌ GitHub release failed")
                    sys.exit(1)
            else:
                print("❌ Test PyPI publishing failed")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Publishing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
