#!/usr/bin/env python3
"""
Demo script to show test isolation is working correctly.

This script:
1. Records the current state of the project directory
2. Runs several tests with the new fixtures
3. Verifies that no temporary files were left behind
4. Shows that tests run in isolated temporary directories
"""

import os
import subprocess
import sys
from pathlib import Path

def get_directory_state(path):
    """Get a set of all files and directories in a path."""
    try:
        result = set()
        for root, dirs, files in os.walk(path):
            root_path = Path(root)
            for d in dirs:
                result.add(str(root_path / d))
            for f in files:
                result.add(str(root_path / f))
        return result
    except Exception as e:
        print(f"Error scanning directory {path}: {e}")
        return set()

def main():
    project_dir = Path("/home/founder3/code/github/giv-cli/giv_py")
    
    print("🔍 Test Directory Isolation Demo")
    print("=" * 50)
    
    # Record initial state
    print(f"📂 Scanning project directory: {project_dir}")
    initial_state = get_directory_state(project_dir)
    print(f"   Initial file count: {len(initial_state)}")
    
    # Run tests with new fixtures
    test_commands = [
        # Test updated fixtures
        "python -m pytest tests/test_config.py -v --tb=short",
        "python -m pytest tests/test_git_utils.py::TestGitHistory::test_get_diff_current -v --tb=short", 
        "python -m pytest tests/test_git_utils.py::TestGitHistory::test_get_diff_cached -v --tb=short",
        "python -m pytest tests/test_lib_output.py::TestWriteOutputToFile::test_write_output_overwrite_mode -v --tb=short",
        "python -m pytest tests/test_commands_integration.py::TestConfigCommandIsolated -v --tb=short",
    ]
    
    print(f"\n🧪 Running {len(test_commands)} test commands...")
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"   [{i}/{len(test_commands)}] {cmd.split()[-2:]}")
        result = subprocess.run(
            cmd.split(), 
            cwd=project_dir, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ Test failed: {result.stderr}")
            return 1
        else:
            # Count passed tests from output
            lines = result.stdout.split('\n')
            for line in lines:
                if " passed in " in line:
                    print(f"   ✅ {line.strip()}")
                    break
    
    # Check final state
    print(f"\n🔍 Scanning project directory after tests...")
    final_state = get_directory_state(project_dir)
    print(f"   Final file count: {len(final_state)}")
    
    # Compare states
    added_files = final_state - initial_state
    removed_files = initial_state - final_state
    
    print(f"\n📊 Results:")
    print(f"   Files added: {len(added_files)}")
    print(f"   Files removed: {len(removed_files)}")
    
    if added_files:
        print("   Added files:")
        for f in sorted(added_files)[:10]:  # Show first 10
            print(f"     + {f}")
        if len(added_files) > 10:
            print(f"     ... and {len(added_files) - 10} more")
    
    if removed_files:
        print("   Removed files:")
        for f in sorted(removed_files)[:10]:  # Show first 10
            print(f"     - {f}")
        if len(removed_files) > 10:
            print(f"     ... and {len(removed_files) - 10} more")
    
    # Filter out expected changes (like __pycache__, .pyc files)
    unexpected_added = []
    for f in added_files:
        if not any(pattern in f for pattern in ['__pycache__', '.pyc', '.pytest_cache']):
            unexpected_added.append(f)
    
    print(f"\n🎯 Test Isolation Assessment:")
    if not unexpected_added:
        print("   ✅ PASS: No unexpected files left in project directory")
        print("   ✅ Tests are properly isolated and clean up after themselves")
        return 0
    else:
        print(f"   ❌ FAIL: {len(unexpected_added)} unexpected files found")
        print("   Some tests may not be properly isolated")
        return 1

if __name__ == "__main__":
    sys.exit(main())
