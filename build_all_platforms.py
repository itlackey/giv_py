#!/usr/bin/env python3
"""
Multi-platform binary builder for giv CLI.

This script builds binaries for multiple platforms when run in CI.
For local development, use the simple build_binary.py script.
"""
import platform
import subprocess
import sys
from pathlib import Path


PLATFORMS = [
    ("linux", "x86_64"),
    ("macos", "x86_64"),
    ("macos", "arm64"),
    ("windows", "x86_64"),
]


def build_for_platform(target_platform: str, target_arch: str):
    """Build binary for a specific platform."""
    # For now, we can only build for the current platform
    current_system = platform.system().lower()
    current_machine = platform.machine().lower()
    
    if current_system == "darwin":
        current_system = "macos"
    if current_machine in ("x86_64", "amd64"):
        current_machine = "x86_64"
    elif current_machine in ("aarch64", "arm64"):
        current_machine = "arm64"
    
    if target_platform != current_system or target_arch != current_machine:
        print(f"⚠️  Cannot cross-compile {target_platform}-{target_arch} on {current_system}-{current_machine}")
        return False
    
    # Define paths
    project_root = Path(__file__).parent
    main_script = project_root / "giv" / "__main__.py"
    templates_dir = project_root / "giv" / "templates"
    dist_dir = project_root / "dist"
    
    # Create dist directory if it doesn't exist
    dist_dir.mkdir(exist_ok=True)
    
    # Define binary name
    binary_name = f"giv-{target_platform}-{target_arch}"
    if target_platform == "windows":
        binary_name += ".exe"
    
    print(f"Building {binary_name}...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", binary_name,
        "--distpath", str(dist_dir),
        "--collect-submodules", "giv",
        "--add-data", f"{templates_dir}:giv/templates",
        "--hidden-import", "giv.cli",
        "--hidden-import", "giv.config", 
        "--hidden-import", "requests",
        "--hidden-import", "click",
        "--hidden-import", "packaging",
        str(main_script)
    ]
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True, cwd=project_root)
        print(f"✅ Binary built successfully: {dist_dir / binary_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
        return False


def main():
    """Build binaries for all supported platforms."""
    if len(sys.argv) > 1 and sys.argv[1] == "--current-only":
        # Build only for current platform
        from build_binary import build_binary
        return build_binary()
    
    success_count = 0
    total_count = len(PLATFORMS)
    
    for platform_name, arch in PLATFORMS:
        if build_for_platform(platform_name, arch):
            success_count += 1
    
    print(f"\n📊 Build Summary: {success_count}/{total_count} successful")
    
    if success_count == 0:
        print("❌ All builds failed")
        return False
    elif success_count < total_count:
        print("⚠️  Some builds failed")
        return False
    else:
        print("✅ All builds successful")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
