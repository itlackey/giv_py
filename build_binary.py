#!/usr/bin/env python3
"""
Simplified binary builder for giv CLI.

This script replaces the complex build system with a simple PyInstaller-based approach.
"""
import platform
import subprocess
import sys
from pathlib import Path


def get_platform_info():
    """Get platform and architecture information."""
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
    
    return system, arch


def build_binary():
    """Build the binary using PyInstaller."""
    # Get platform info
    system, arch = get_platform_info()
    
    # Define paths
    project_root = Path(__file__).parent
    main_script = project_root / "giv" / "__main__.py"
    templates_dir = project_root / "giv" / "templates"
    dist_dir = project_root / "dist"
    
    # Create dist directory if it doesn't exist
    dist_dir.mkdir(exist_ok=True)
    
    # Define binary name
    binary_name = f"giv-{system}-{arch}"
    if system == "windows":
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
        "--hidden-import", "giv.git_utils",
        "--hidden-import", "giv.llm_utils",
        "--hidden-import", "giv.template_utils",
        "--hidden-import", "giv.output_utils",
        "--hidden-import", "giv.project_metadata",
        "--hidden-import", "giv.markdown_utils",
        "--hidden-import", "requests",
        "--hidden-import", "click",
        "--hidden-import", "packaging",
        "--hidden-import", "importlib.metadata",
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


if __name__ == "__main__":
    success = build_binary()
    sys.exit(0 if success else 1)
