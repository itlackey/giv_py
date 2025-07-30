#!/usr/bin/env python3
"""
Ultra-simplified binary builder for giv CLI.
Uses PyInstaller with minimal configuration - relies on auto-detection.
"""
import platform
import subprocess
import sys
from pathlib import Path


def get_binary_name():
    """Get platform-specific binary name."""
    system = platform.system().lower()
    if system == "darwin":
        system = "macos"
    
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        arch = machine
    
    binary_name = f"giv-{system}-{arch}"
    if system == "windows":
        binary_name += ".exe"
    
    return binary_name


def build_binary():
    """Build binary with minimal PyInstaller configuration."""
    project_root = Path(__file__).parent.parent
    main_script = project_root / "giv" / "__main__.py"
    templates_dir = project_root / "giv" / "templates"
    dist_dir = project_root / "dist"
    
    # Create dist directory
    dist_dir.mkdir(exist_ok=True)
    
    binary_name = get_binary_name()
    print(f"Building {binary_name}...")
    
    # Minimal PyInstaller command - let it auto-detect what it can
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", binary_name,
        "--distpath", str(dist_dir),
        "--add-data", f"{templates_dir}:giv/templates",
        "--collect-submodules", "giv",  # This handles most imports automatically
        str(main_script)
    ]
    
    try:
        subprocess.run(cmd, check=True, cwd=project_root)
        print(f"Binary built successfully: {dist_dir / binary_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code: {e.returncode}")
        return False


def main():
    """Entry point for Poetry script."""
    success = build_binary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
