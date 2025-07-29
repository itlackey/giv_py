#!/usr/bin/env python3
"""
Main build orchestrator for giv CLI.

This script is a compatibility wrapper that uses the new simplified build system.
For direct binary building, use the build_binary.py script in the project root.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def build_binaries():
    """Build binary using the new simplified system."""
    project_root = Path(__file__).parent.parent
    build_script = project_root / "build_binary.py"
    
    if not build_script.exists():
        print("❌ build_binary.py not found. Make sure you're in the correct directory.")
        return False
    
    try:
        # Use Poetry to run the build script
        subprocess.run([
            sys.executable, "-m", "poetry", "run", "build-binary"
        ], cwd=project_root, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        # Fallback to direct Python execution
        try:
            subprocess.run([
                sys.executable, str(build_script)
            ], cwd=project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed with exit code {e.returncode}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build giv CLI artifacts")
    parser.add_argument("target", choices=["binaries"], 
                       help="Build target (only 'binaries' supported)")
    
    args = parser.parse_args()
    
    if args.target == "binaries":
        print("🔨 Building binaries using simplified build system...")
        success = build_binaries()
        if success:
            print("✅ Build completed successfully!")
            print("📁 Binary located in: dist/")
        else:
            print("❌ Build failed!")
        return success
    
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)