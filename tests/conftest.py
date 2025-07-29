"""
Pytest configuration and fixtures for giv CLI tests.

This module provides shared test fixtures and configuration for testing
the Python implementation of giv CLI. It includes utilities for:
- Setting up isolated test environments
- Creating mock git repositories
- Managing test configurations
- Comparing output with Bash implementation
"""
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Dict
import subprocess
import pytest

from giv.config import ConfigManager


@contextmanager
def change_directory(path: Path):
    """Context manager to temporarily change working directory for git repository testing."""
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def git_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository with realistic project structure."""
    repo_dir = temp_dir / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    
    # Create realistic project structure
    (repo_dir / "package.json").write_text("""{
  "name": "test-project",
  "version": "1.2.0",
  "description": "A test project for integration testing",
  "main": "index.js",
  "scripts": {
    "test": "echo 'test'"
  }
}""")
    
    (repo_dir / "README.md").write_text("""# Test Project

This is a test project for integration testing.

## Features

- Feature A
- Feature B
""")
    
    (repo_dir / "CHANGELOG.md").write_text("""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2023-01-01
- Initial release
""")
    
    # Create some source files
    src_dir = repo_dir / "src"
    src_dir.mkdir()
    
    (src_dir / "index.js").write_text("""console.log('Hello, world!');

function add(a, b) {
    return a + b;
}

module.exports = { add };
""")
    
    (src_dir / "utils.js").write_text("""function formatDate(date) {
    return date.toISOString().split('T')[0];
}

module.exports = { formatDate };
""")
    
    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)
    
    yield repo_dir


@pytest.fixture
def config_manager(temp_dir: Path) -> ConfigManager:
    """Create a ConfigManager with isolated test configuration."""
    config_dir = temp_dir / ".giv"
    config_dir.mkdir()
    
    config_file = config_dir / "config"
    config_file.write_text("""# Test configuration
api.url=https://api.example.test
api.key=test-key-12345
temperature=0.7
max_tokens=4096
""")
    
    return ConfigManager(config_path=config_file)


@pytest.fixture
def giv_home(temp_dir: Path) -> Generator[Path, None, None]:
    """Set up isolated GIV_HOME environment."""
    giv_home = temp_dir / ".giv"
    giv_home.mkdir()
    
    # Set environment variable
    old_giv_home = os.environ.get("GIV_HOME")
    os.environ["GIV_HOME"] = str(giv_home)
    
    try:
        yield giv_home
    finally:
        if old_giv_home is not None:
            os.environ["GIV_HOME"] = old_giv_home
        else:
            os.environ.pop("GIV_HOME", None)


@pytest.fixture
def bash_giv_path() -> Path:
    """Path to the Bash giv implementation for compatibility testing."""
    # Assuming the Bash implementation is in the parent directory
    bash_path = Path(__file__).parent.parent.parent / "giv" / "src" / "giv.sh"
    if not bash_path.exists():
        pytest.skip("Bash giv implementation not found")
    return bash_path


class BashGivRunner:
    """Helper class to run Bash giv commands for comparison testing."""
    
    def __init__(self, bash_path: Path = None, work_dir: Path = None, cwd: Path = None):
        # Handle both old style (bash_path, work_dir) and new style (cwd=...)
        if bash_path is None:
            # Find bash giv path
            possible_paths = [
                Path("/home/founder3/code/github/giv-cli/giv/src/giv.sh"),
                Path("../giv/src/giv.sh"),
                Path("../../giv/src/giv.sh"),
            ]
            for path in possible_paths:
                if path.exists():
                    bash_path = path
                    break
            if bash_path is None:
                raise FileNotFoundError("Could not find bash giv.sh")
        
        self.bash_path = bash_path
        self.work_dir = cwd if cwd is not None else work_dir
        if self.work_dir is None:
            self.work_dir = Path.cwd()
    
    def run(self, args: list, **kwargs) -> subprocess.CompletedProcess:
        """Run a Bash giv command."""
        cmd = [str(self.bash_path)] + args
        return subprocess.run(
            cmd,
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            **kwargs
        )


@pytest.fixture
def bash_giv(bash_giv_path: Path, git_repo: Path) -> BashGivRunner:
    """Create a runner for Bash giv commands."""
    return BashGivRunner(bash_path=bash_giv_path, work_dir=git_repo)


class PythonGivRunner:
    """Helper class to run Python giv commands."""
    
    def __init__(self, work_dir: Path = None, cwd: Path = None):
        # Handle both work_dir and cwd arguments
        if work_dir is None and cwd is None:
            # Default to current directory if no arguments provided
            self.work_dir = Path.cwd()
        elif cwd is not None:
            self.work_dir = cwd
        else:
            self.work_dir = work_dir
    
    def run(self, args: list, **kwargs) -> subprocess.CompletedProcess:
        """Run a Python giv command."""
        # Import here to avoid circular imports
        from giv.main import main
        import sys
        from io import StringIO
        
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_cwd = os.getcwd()
        
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        try:
            os.chdir(self.work_dir)
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Run the command
            exit_code = main(args)
            
            return subprocess.CompletedProcess(
                args=args,
                returncode=exit_code,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue()
            )
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.chdir(old_cwd)


@pytest.fixture
def python_giv(git_repo: Path) -> PythonGivRunner:
    """Create a runner for Python giv commands."""
    return PythonGivRunner(git_repo)


def normalize_output(output: str) -> str:
    """Normalize output for comparison by removing timestamps, paths, etc."""
    import re
    
    # Remove absolute paths
    output = re.sub(r'/[^\s]+/', '<path>/', output)
    
    # Remove timestamps
    output = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<timestamp>', output)
    output = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '<timestamp>', output)
    
    # Remove commit hashes
    output = re.sub(r'\b[0-9a-f]{7,40}\b', '<commit>', output)
    
    # Normalize whitespace
    output = '\n'.join(line.rstrip() for line in output.splitlines())
    
    return output


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    # Store original values
    original_env = {}
    giv_vars = [var for var in os.environ if var.startswith('GIV_')]
    
    for var in giv_vars:
        original_env[var] = os.environ[var]
        del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


# Enhanced fixtures for improved test isolation

def setup_initial_repo_state(repo_dir: Path) -> None:
    """Setup consistent initial repository state for all tests."""
    # Create realistic project structure
    (repo_dir / "package.json").write_text("""{
  "name": "test-project",
  "version": "1.2.0",
  "description": "A test project for integration testing",
  "main": "index.js",
  "scripts": {
    "test": "echo 'test'"
  }
}""")
    
    (repo_dir / "README.md").write_text("""# Test Project

This is a test project for integration testing.

## Features

- Feature A
- Feature B
""")
    
    (repo_dir / "CHANGELOG.md").write_text("""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2023-01-01
- Initial release
""")
    
    # Create some source files
    src_dir = repo_dir / "src"
    src_dir.mkdir()
    
    (src_dir / "index.js").write_text("""console.log('Hello, world!');

function add(a, b) {
    return a + b;
}

module.exports = { add };
""")
    
    (src_dir / "utils.js").write_text("""function formatDate(date) {
    return date.toISOString().split('T')[0];
}

module.exports = { formatDate };
""")
    
    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)


def create_test_files(repo_dir: Path, files: Dict[str, str]) -> None:
    """Create test files with specified content."""
    for file_path, content in files.items():
        full_path = repo_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def commit_changes(repo_dir: Path, message: str) -> str:
    """Commit current changes and return commit hash."""
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", message], 
        cwd=repo_dir, 
        check=True,
        capture_output=True,
        text=True
    )
    
    # Get the commit hash
    hash_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=True
    )
    return hash_result.stdout.strip()


@pytest.fixture
def isolated_git_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """Create an isolated git repository with consistent history for each test.
    
    This fixture:
    - Creates a unique temporary Git repository for each test
    - Initializes it with consistent configuration and initial state
    - Changes to the repository directory for the test duration
    - Automatically restores the original directory on cleanup
    """
    repo_dir = temp_dir / "test_repo"
    repo_dir.mkdir()
    
    # Initialize git repo with consistent config
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    
    # Create consistent initial state
    setup_initial_repo_state(repo_dir)
    
    # Set as working directory for the test
    old_cwd = os.getcwd()
    os.chdir(repo_dir)
    
    try:
        yield repo_dir
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def working_directory(temp_dir: Path) -> Generator[Path, None, None]:
    """Change to a temporary directory for the duration of the test.
    
    This fixture:
    - Changes to a unique temporary directory for each test
    - Automatically restores the original directory on cleanup
    - Provides complete isolation from the project directory
    """
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        yield temp_dir
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def isolated_config_manager(temp_dir: Path) -> ConfigManager:
    """Create a ConfigManager completely isolated in temp directory.
    
    This fixture:
    - Creates a .giv directory in the temp directory
    - Sets up a test configuration file
    - Returns a ConfigManager instance pointing to the isolated config
    """
    config_dir = temp_dir / ".giv"
    config_dir.mkdir()
    
    config_file = config_dir / "config"
    config_file.write_text("""# Test configuration
api.url=https://api.example.test
api.key=test-key-12345
temperature=0.7
max_tokens=4096
""")
    
    return ConfigManager(config_path=config_file)


@pytest.fixture
def repo_with_changes(isolated_git_repo: Path) -> Path:
    """Create an isolated Git repository with unstaged changes."""
    # Add unstaged changes
    create_test_files(isolated_git_repo, {
        "src/new_file.js": "// New file\nconsole.log('new');",
        "modified_file.txt": "This file has been modified"
    })
    
    # Modify existing file
    with open(isolated_git_repo / "src" / "index.js", "a") as f:
        f.write("\n// Added line\n")
    
    return isolated_git_repo


@pytest.fixture
def repo_with_staged_changes(isolated_git_repo: Path) -> Path:
    """Create an isolated Git repository with staged changes."""
    # Add staged changes
    create_test_files(isolated_git_repo, {
        "src/staged.js": "// Staged file\nconsole.log('staged');",
        "staged_file.txt": "This file has been staged"
    })
    
    subprocess.run(["git", "add", "."], cwd=isolated_git_repo, check=True)
    
    return isolated_git_repo


@pytest.fixture
def repo_with_commits(isolated_git_repo: Path) -> Path:
    """Create an isolated Git repository with multiple commits."""
    # Create first additional commit
    create_test_files(isolated_git_repo, {
        "feature1.js": "// Feature 1\nconsole.log('feature1');",
    })
    commit_changes(isolated_git_repo, "Add feature 1")
    
    # Create second additional commit
    create_test_files(isolated_git_repo, {
        "feature2.js": "// Feature 2\nconsole.log('feature2');",
    })
    commit_changes(isolated_git_repo, "Add feature 2")
    
    return isolated_git_repo


# Parametrized fixtures for different test scenarios
@pytest.fixture(params=['empty', 'with_changes', 'with_staged'])
def git_repo_state(request, git_repo):
    """Create git repos in different states for testing."""
    if request.param == 'empty':
        # Already in initial state
        pass
    elif request.param == 'with_changes':
        # Add unstaged changes
        (git_repo / "src" / "new_file.js").write_text("// New file\nconsole.log('new');")
        with open(git_repo / "src" / "index.js", "a") as f:
            f.write("\n// Added line\n")
    elif request.param == 'with_staged':
        # Add staged changes
        (git_repo / "src" / "staged.js").write_text("// Staged file\nconsole.log('staged');")
        subprocess.run(["git", "add", "src/staged.js"], cwd=git_repo, check=True)
    
    return git_repo, request.param
