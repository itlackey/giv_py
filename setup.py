#!/usr/bin/env python3
"""
Setup script for PyPI publishing and distribution management.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def check_prerequisites():
    """Check that all required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    required_tools = ['poetry', 'git']
    missing_tools = []
    
    for tool in required_tools:
        result = run_command(f"which {tool}", check=False)
        if result.returncode != 0:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing required tools: {', '.join(missing_tools)}")
        print("Please install them before continuing.")
        return False
    
    print("✅ All prerequisites satisfied")
    return True


def run_tests():
    """Run the test suite to ensure everything works."""
    print("🧪 Running test suite...")
    
    result = run_command("poetry run pytest", check=False)
    if result.returncode != 0:
        print("❌ Tests failed. Please fix issues before publishing.")
        return False
    
    print("✅ All tests passed")
    return True


def check_git_status():
    """Ensure git repository is clean."""
    print("📋 Checking git status...")
    
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("❌ Git repository has uncommitted changes:")
        print(result.stdout)
        print("Please commit or stash changes before publishing.")
        return False
    
    print("✅ Git repository is clean")
    return True


def bump_version(version_type='patch'):
    """Bump the version number."""
    print(f"📈 Bumping version ({version_type})...")
    
    result = run_command(f"poetry version {version_type}")
    if result.returncode != 0:
        print("❌ Failed to bump version")
        return False
    
    # Get the new version
    result = run_command("poetry version --short")
    new_version = result.stdout.strip()
    
    print(f"✅ Version bumped to {new_version}")
    return new_version


def build_package():
    """Build the package for distribution."""
    print("🔨 Building package...")
    
    # Clean previous builds
    run_command("rm -rf dist/", check=False)
    
    result = run_command("poetry build")
    if result.returncode != 0:
        print("❌ Failed to build package")
        return False
    
    print("✅ Package built successfully")
    return True


def publish_to_pypi(test=False):
    """Publish the package to PyPI."""
    repository = "testpypi" if test else "pypi"
    print(f"🚀 Publishing to {'Test ' if test else ''}PyPI...")
    
    cmd = f"poetry publish"
    if test:
        cmd += " --repository testpypi"
    
    result = run_command(cmd)
    if result.returncode != 0:
        print(f"❌ Failed to publish to {repository}")
        return False
    
    print(f"✅ Package published to {repository}")
    return True


def create_git_tag(version):
    """Create and push a git tag for the release."""
    print(f"🏷️ Creating git tag v{version}...")
    
    # Create tag
    run_command(f"git tag -a v{version} -m 'Release v{version}'")
    
    # Push tag
    result = run_command("git push origin --tags")
    if result.returncode != 0:
        print("❌ Failed to push git tag")
        return False
    
    print(f"✅ Git tag v{version} created and pushed")
    return True


def main():
    """Main setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PyPI setup and publishing script")
    parser.add_argument(
        "action",
        choices=["check", "test", "build", "publish", "publish-test", "release"],
        help="Action to perform"
    )
    parser.add_argument(
        "--version-type",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Version bump type for release"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    if args.action == "check":
        print("🔍 Running pre-publish checks...")
        if not check_prerequisites():
            sys.exit(1)
        if not args.skip_tests and not run_tests():
            sys.exit(1)
        if not check_git_status():
            sys.exit(1)
        print("✅ All checks passed!")
    
    elif args.action == "test":
        if not run_tests():
            sys.exit(1)
    
    elif args.action == "build":
        if not build_package():
            sys.exit(1)
    
    elif args.action == "publish-test":
        if not check_prerequisites():
            sys.exit(1)
        if not args.skip_tests and not run_tests():
            sys.exit(1)
        if not build_package():
            sys.exit(1)
        if not publish_to_pypi(test=True):
            sys.exit(1)
        print("✅ Test publication completed!")
    
    elif args.action == "publish":
        if not check_prerequisites():
            sys.exit(1)
        if not args.skip_tests and not run_tests():
            sys.exit(1)
        if not build_package():
            sys.exit(1)
        if not publish_to_pypi(test=False):
            sys.exit(1)
        print("✅ Publication completed!")
    
    elif args.action == "release":
        print("🚀 Starting full release process...")
        
        if not check_prerequisites():
            sys.exit(1)
        if not args.skip_tests and not run_tests():
            sys.exit(1)
        if not check_git_status():
            sys.exit(1)
        
        # Bump version
        new_version = bump_version(args.version_type)
        if not new_version:
            sys.exit(1)
        
        # Commit version bump
        run_command("git add pyproject.toml")
        run_command(f"git commit -m 'Bump version to {new_version}'")
        run_command("git push")
        
        # Build and publish
        if not build_package():
            sys.exit(1)
        if not publish_to_pypi():
            sys.exit(1)
        
        # Create git tag
        if not create_git_tag(new_version):
            sys.exit(1)
        
        print(f"🎉 Release v{new_version} completed successfully!")
        print(f"📦 Package is now available on PyPI")
        print(f"🏷️ Git tag v{new_version} has been created")


if __name__ == "__main__":
    main()
