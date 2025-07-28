#!/usr/bin/env python3
"""
Publishing orchestrator for giv CLI.

Handles publishing to various distribution channels including PyPI,
GitHub releases, and package managers.
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add build directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import BuildConfig
from core.version_manager import VersionManager
from pypi.build import PyPIBuilder
from homebrew.build import HomebrewBuilder
from scoop.build import ScoopBuilder


class PublishOrchestrator:
    """Main publishing orchestrator for all giv CLI distribution channels."""
    
    def __init__(self):
        """Initialize publishing orchestrator."""
        self.config = BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Publishers
        self.pypi_builder = PyPIBuilder(self.config)
        self.homebrew_builder = HomebrewBuilder(self.config)
        self.scoop_builder = ScoopBuilder(self.config)
    
    def publish_pypi(self, version: Optional[str] = None, test_only: bool = False) -> bool:
        """
        Publish to PyPI or Test PyPI.
        
        Args:
            version: Version to publish (auto-detected if not provided)
            test_only: Publish to Test PyPI only
            
        Returns:
            True if successful
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Publishing to {'Test ' if test_only else ''}PyPI...")
        
        # Build packages
        packages = self.pypi_builder.build_packages(version)
        if not packages:
            print("No packages to publish")
            return False
        
        # Validate packages
        if not self.pypi_builder.validate_packages(packages):
            print("Package validation failed")
            return False
        
        # Upload packages
        if test_only:
            return self.pypi_builder.upload_to_test_pypi(packages)
        else:
            return self.pypi_builder.upload_to_pypi(packages)
    
    def update_package_managers(self, version: Optional[str] = None) -> Dict[str, bool]:
        """
        Update package manager configurations.
        
        Args:
            version: Version to update (auto-detected if not provided)
            
        Returns:
            Dictionary mapping package manager to success status
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Updating package manager configurations for version {version}")
        
        results = {}
        
        # Update Homebrew formula
        try:
            formula_path = self.homebrew_builder.build_formula(version)
            if self.homebrew_builder.test_formula(formula_path):
                self.homebrew_builder.create_tap_structure(version, formula_path)
                results["homebrew"] = True
                print("✓ Homebrew formula updated")
            else:
                results["homebrew"] = False
                print("✗ Homebrew formula validation failed")
        except Exception as e:
            print(f"✗ Homebrew formula update failed: {e}")
            results["homebrew"] = False
        
        # Update Scoop manifest
        try:
            manifest_path = self.scoop_builder.build_manifest(version)
            if self.scoop_builder.validate_manifest(manifest_path):
                self.scoop_builder.create_bucket_structure(version, manifest_path)
                self.scoop_builder.generate_chocolatey_nuspec(version)
                results["scoop"] = True
                print("✓ Scoop manifest updated")
            else:
                results["scoop"] = False
                print("✗ Scoop manifest validation failed")
        except Exception as e:
            print(f"✗ Scoop manifest update failed: {e}")
            results["scoop"] = False
        
        return results
    
    def create_github_release(self, version: Optional[str] = None, draft: bool = False) -> bool:
        """
        Create GitHub release with binaries and package configs.
        
        Args:
            version: Version to release (auto-detected if not provided)
            draft: Create as draft release
            
        Returns:
            True if successful
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Creating GitHub release for version {version}")
        
        try:
            import subprocess
            
            # Check if gh CLI is available
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
            
            # Prepare release assets
            assets_dir = self.config.get_dist_dir(version)
            asset_files = []
            
            # Find binary files
            for platform_dir in assets_dir.iterdir():
                if platform_dir.is_dir() and "-" in platform_dir.name:
                    for binary_file in platform_dir.iterdir():
                        if binary_file.is_file() and binary_file.name.startswith("giv-"):
                            asset_files.append(str(binary_file))
            
            # Find package config files
            for package_dir in ["homebrew-tap", "scoop-bucket", "chocolatey"]:
                package_path = assets_dir / package_dir
                if package_path.exists():
                    for file_path in package_path.rglob("*"):
                        if file_path.is_file():
                            asset_files.append(str(file_path))
            
            if not asset_files:
                print("No release assets found")
                return False
            
            # Create release
            cmd = [
                "gh", "release", "create", f"v{version}",
                "--title", f"giv CLI v{version}",
                "--generate-notes",
            ]
            
            if draft:
                cmd.append("--draft")
            
            # Add asset files
            cmd.extend(asset_files)
            
            result = subprocess.run(cmd, cwd=self.config.project_root)
            
            if result.returncode == 0:
                print(f"✓ GitHub release created: v{version}")
                return True
            else:
                print(f"✗ GitHub release creation failed")
                return False
                
        except subprocess.CalledProcessError:
            print("Error: GitHub CLI (gh) not available")
            return False
        except Exception as e:
            print(f"Error creating GitHub release: {e}")
            return False
    
    def publish_all(self, version: Optional[str] = None, test_pypi: bool = False, 
                   draft_release: bool = False) -> Dict[str, bool]:
        """
        Publish to all distribution channels.
        
        Args:
            version: Version to publish (auto-detected if not provided)
            test_pypi: Use Test PyPI instead of PyPI
            draft_release: Create draft GitHub release
            
        Returns:
            Dictionary mapping channel to success status
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Publishing giv CLI v{version} to all channels")
        print("=" * 50)
        
        results = {}
        
        # Publish to PyPI
        print("\\n1. Publishing to PyPI...")
        try:
            results["pypi"] = self.publish_pypi(version, test_pypi)
        except Exception as e:
            print(f"PyPI publishing failed: {e}")
            results["pypi"] = False
        
        # Update package managers
        print("\\n2. Updating package managers...")
        try:
            package_results = self.update_package_managers(version)
            results.update(package_results)
        except Exception as e:
            print(f"Package manager updates failed: {e}")
            results["homebrew"] = False
            results["scoop"] = False
        
        # Create GitHub release
        print("\\n3. Creating GitHub release...")
        try:
            results["github"] = self.create_github_release(version, draft_release)
        except Exception as e:
            print(f"GitHub release creation failed: {e}")
            results["github"] = False
        
        # Print summary
        print(f"\\nPublish Summary for v{version}:")
        print("=" * 40)
        for channel, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {channel}")
        
        return results
    
    def status(self, version: Optional[str] = None) -> None:
        """
        Show publishing status for a version.
        
        Args:
            version: Version to check (current if not provided)
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Publishing Status for v{version}")
        print("=" * 40)
        
        # Check if version exists in distribution directory
        dist_dir = self.config.get_dist_dir(version)
        if not dist_dir.exists():
            print("No build artifacts found for this version")
            return
        
        # Check binaries
        print("Binaries:")
        binary_count = 0
        for platform_dir in dist_dir.iterdir():
            if platform_dir.is_dir() and "-" in platform_dir.name:
                for binary_file in platform_dir.iterdir():
                    if binary_file.is_file() and binary_file.name.startswith("giv-"):
                        size_mb = binary_file.stat().st_size / (1024 * 1024)
                        print(f"  ✓ {platform_dir.name}: {binary_file.name} ({size_mb:.1f} MB)")
                        binary_count += 1
        
        if binary_count == 0:
            print("  No binaries found")
        
        # Check PyPI packages
        pypi_dir = dist_dir / "pypi"
        if pypi_dir.exists():
            print("\\nPyPI Packages:")
            for package_file in pypi_dir.iterdir():
                if package_file.is_file():
                    print(f"  ✓ {package_file.name}")
        
        # Check package manager configs
        print("\\nPackage Manager Configs:")
        for pm_name in ["homebrew-tap", "scoop-bucket", "chocolatey"]:
            pm_dir = dist_dir / pm_name
            if pm_dir.exists():
                print(f"  ✓ {pm_name}")
            else:
                print(f"  ✗ {pm_name}")


def main():
    """CLI interface for publishing orchestrator."""
    parser = argparse.ArgumentParser(
        description="Publish giv CLI to distribution channels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s pypi                         # Publish to PyPI
  %(prog)s pypi --test                  # Publish to Test PyPI
  %(prog)s package-managers             # Update package manager configs
  %(prog)s github                       # Create GitHub release
  %(prog)s all                          # Publish to all channels
  %(prog)s status                       # Show publishing status
        """
    )
    
    parser.add_argument("--version", help="Version to publish (auto-detected if not provided)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Publishing commands")
    
    # PyPI command
    pypi_parser = subparsers.add_parser("pypi", help="Publish to PyPI")
    pypi_parser.add_argument("--test", action="store_true", help="Publish to Test PyPI")
    
    # Package managers command
    pm_parser = subparsers.add_parser("package-managers", help="Update package manager configs")
    
    # GitHub command
    github_parser = subparsers.add_parser("github", help="Create GitHub release")
    github_parser.add_argument("--draft", action="store_true", help="Create draft release")
    
    # All command
    all_parser = subparsers.add_parser("all", help="Publish to all channels")
    all_parser.add_argument("--test-pypi", action="store_true", help="Use Test PyPI")
    all_parser.add_argument("--draft", action="store_true", help="Create draft GitHub release")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show publishing status")
    
    args = parser.parse_args()
    
    # Default to status if no command provided
    if not args.command:
        args.command = "status"
    
    orchestrator = PublishOrchestrator()
    
    try:
        if args.command == "pypi":
            success = orchestrator.publish_pypi(args.version, args.test)
            return 0 if success else 1
        
        elif args.command == "package-managers":
            results = orchestrator.update_package_managers(args.version)
            return 0 if all(results.values()) else 1
        
        elif args.command == "github":
            success = orchestrator.create_github_release(args.version, args.draft)
            return 0 if success else 1
        
        elif args.command == "all":
            results = orchestrator.publish_all(args.version, args.test_pypi, args.draft)
            return 0 if all(results.values()) else 1
        
        elif args.command == "status":
            orchestrator.status(args.version)
            return 0
        
        else:
            parser.print_help()
            return 1
    
    except KeyboardInterrupt:
        print("\\nPublishing interrupted by user")
        return 1
    except Exception as e:
        print(f"\\nPublishing failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())