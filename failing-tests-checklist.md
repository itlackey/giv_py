# Failing Tests Checklist

## Analysis Summary

The failing tests in `test_lib_metadata.py` reveal a fundamental architectural mismatch between the test expectations and the actual implementation:

- **Tests expect**: Instance-based API with `ProjectMetadata(project_root)` constructor and instance methods
- **Implementation provides**: Static method-based API with `ProjectMetadata.get_version()`, `ProjectMetadata.get_title()`, etc.
- **Working directory**: Tests expect to work with arbitrary project directories, but the application always runs from the git repository root directory

## Root Cause

The `ProjectMetadata` class is designed as a utility class with static methods that:
1. Has no `__init__` method that accepts parameters
2. Works from the git repository root directory (the application automatically changes to the repository root on startup and exits if not in a git repository)
3. Uses `commit="--current"` to read from filesystem instead of git when testing

## Issues Found

### 1. Constructor Issues (24 failing tests)
**Problem**: Tests call `ProjectMetadata(project_root)` but the class has no constructor that accepts parameters.

**Error**: `TypeError: ProjectMetadata() takes no arguments`

**Tests affected**:
- All tests in `TestProjectMetadataVersionDetection` class (6 tests)
- All tests in `TestProjectMetadataTitleDetection` class (6 tests) 
- All tests in `TestProjectMetadataFileFormats` class (3 tests)
- All tests in `TestProjectMetadataErrorHandling` class (4 tests)
- All tests in `TestProjectMetadataVersionFormatting` class (2 tests)
- All tests in `TestProjectMetadataIntegration` class (3 tests)

### 2. Static Method Test Issues (2 failing tests)
**Problem**: Tests incorrectly patch `__init__` method and treat mocks as pytest fixtures.

**Error**: `fixture 'mock_init' not found`

**Tests affected**:
- `test_static_get_version`
- `test_static_get_title`

## Correction Steps

### Step 1: Fix Instance-Based Tests (24 tests)

For all tests that currently use `ProjectMetadata(project_root)`:

1. **Use git repositories for testing**: Create proper git repositories in test directories and initialize them
2. **Use static methods**: Replace `metadata.get_version()` with `ProjectMetadata.get_version(commit="--current")`
3. **Use commit parameter**: Use `commit="--current"` to read from filesystem instead of git

Since the application automatically changes to the git repository root on startup, tests should create proper git repositories and run within them.

**Example transformation**:
```python
# OLD (failing):
def test_get_version_from_cargo_toml(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        cargo_file = project_root / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "test-project"
version = "0.5.2"
edition = "2021"
""")
        metadata = ProjectMetadata(project_root)
        version = metadata.get_version()
        assert version == "0.5.2"

# NEW (correct):
def test_get_version_from_cargo_toml(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=project_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project_root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=project_root, check=True)
        
        cargo_file = project_root / "Cargo.toml"
        cargo_file.write_text("""
[package]
name = "test-project"
version = "0.5.2"
edition = "2021"
""")
        
        with working_directory(project_root):  # Application will work from repository root
            version = ProjectMetadata.get_version(commit="--current")
            assert version == "0.5.2"
```

### Step 2: Fix Static Method Tests (2 tests)

For the static method tests in `TestProjectMetadataStaticMethods`:

1. **Remove __init__ patches**: Remove `@patch.object(ProjectMetadata, '__init__', lambda x: None)`
2. **Fix method signatures**: Remove mock parameters from method signatures
3. **Use correct patching**: Keep only the actual method patches

**Example transformation**:
```python
# OLD (failing):
@patch.object(ProjectMetadata, '__init__', lambda x: None)
@patch.object(ProjectMetadata, 'get_version', return_value="1.2.3")
def test_static_get_version(self, mock_get_version, mock_init):
    version = ProjectMetadata.get_version()
    assert version == "1.2.3"

# NEW (correct):
@patch.object(ProjectMetadata, 'get_version', return_value="1.2.3")
def test_static_get_version(self, mock_get_version):
    version = ProjectMetadata.get_version()
    assert version == "1.2.3"
```

### Step 3: Create Working Directory Context Manager

Add a utility context manager to `conftest.py` or test utilities to properly handle git repository testing:

```python
from contextlib import contextmanager
import os
import subprocess

@contextmanager
def working_directory(path):
    """Context manager to temporarily change working directory for git repository testing."""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
```

### Step 4: Update Test Imports

Ensure tests import the context manager:
```python
from .conftest import working_directory  # or wherever it's defined
```

## Implementation Verification

After making these changes:

1. **Test the fixes**: Run `pytest tests/test_lib_metadata.py -v` to verify all tests pass
2. **Check integration**: Ensure the static method interface works correctly with the rest of the codebase
3. **Validate behavior**: Confirm that `commit="--current"` properly reads from the filesystem

## Expected Outcome

After implementing these corrections:
- All 26 failing tests should pass
- Tests will correctly use the static method interface that matches the actual implementation
- Tests will work with git repositories and the application's behavior of running from the repository root
- The static method tests will properly mock only the necessary methods

## Notes

- The current implementation correctly follows the static method pattern used throughout the codebase
- This is a test issue, not an implementation bug
- The `commit="--current"` parameter is the key to making filesystem-based testing work
- The application automatically changes to the git repository root directory on startup and exits if not in a git repository
- Tests should create proper git repositories and work within that context
