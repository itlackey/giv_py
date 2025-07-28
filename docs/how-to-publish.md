# How to Build and Publish GIV CLI Binaries

This guide explains how to build and publish the `giv` CLI tool as cross-platform binaries using the Python-based build system.

## Overview

The build system creates self-contained binary executables for multiple platforms:
- **Linux** - x86_64 and ARM64 architectures
- **macOS** - Intel and Apple Silicon architectures  
- **Windows** - x86_64 architecture
- **PyPI** - Python package distribution
- **GitHub Releases** - Direct binary downloads

## Build Architecture

The build system uses modern Python tooling:

- **Poetry**: Dependency management and virtual environments
- **PyInstaller**: Python to binary compilation
- **GitHub Actions**: Automated CI/CD pipeline
- **build.py**: Main build orchestrator
- **publish.py**: Publishing automation

## Prerequisites

### Required Tools
- **Python 3.8+** - For running build scripts
- **Poetry** - Dependency management (`pip install poetry`)
- **Git** - Version control
- **PyInstaller** - Binary compilation (installed via Poetry)

### Platform-Specific Build Requirements

**Linux/macOS:**
- Standard development tools (build-essential, Xcode tools)
- No additional requirements

**Windows:**
- Visual Studio Build Tools or Visual Studio Community
- Windows SDK

**Cross-compilation:**
- GitHub Actions runners (automated)
- Docker for Linux builds on other platforms

### Authentication Setup
Set environment variables for publishing:

```bash
# PyPI publishing
export PYPI_API_TOKEN="your-pypi-token"

# GitHub releases
export GITHUB_TOKEN="your-github-token"

# Optional: TestPyPI for testing
export TEST_PYPI_API_TOKEN="your-test-pypi-token"
```

## Quick Start

### 1. Setup Development Environment
```bash
# Clone repository
git clone https://github.com/giv-cli/giv-py.git
cd giv-py

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Build Binaries
```bash
# Build for current platform
./build/build.py binaries

# Test the build
poetry run pytest

# Run type checking and linting
poetry run mypy giv/ tests/
poetry run black giv/ tests/
poetry run flake8 giv/ tests/
```

### 3. Publish Release
```bash
# Full release process
./build/build.py release

# Or step by step:
./build/build.py binaries    # Build binaries
poetry run pytest           # Run tests
./build/publish.py all       # Publish to all channels
```

## Build System Details

### Available Build Commands

The `build.py` script provides several automation commands:

```bash
# Development commands
./build/build.py status         # Check build system status
./build/build.py binaries       # Build binaries for current platform
./build/build.py packages       # Build PyPI packages
./build/build.py release        # Complete release process
./build/build.py clean          # Clean build artifacts

# Publishing commands  
./build/publish.py pypi         # Publish to PyPI
./build/publish.py pypi --test  # Publish to TestPyPI
./build/publish.py github       # Create GitHub release
./build/publish.py all          # Publish to all channels
```

### Build Configuration

Build settings are configured in `build/core/config.py`:

```python
# Core build configuration
class BuildConfig:
    PACKAGE_NAME = "giv"
    SUPPORTED_PLATFORMS = [
        "linux-x86_64", "linux-arm64",
        "darwin-x86_64", "darwin-arm64", 
        "windows-x86_64"
    ]
    BINARY_NAME_FORMAT = "giv-{platform}-{arch}"
```

## Detailed Workflow

### Step 1: Binary Compilation

Binaries are compiled using PyInstaller:
```bash
# Build for current platform
./build/build.py binaries

# Build for specific platforms
./build/build.py binaries --platforms linux-x86_64,darwin-arm64

# Build all supported platforms
./build/build.py binaries --all-platforms
```

### Step 2: Package Generation

#### Build Package Manager Configurations
```bash
# Build Homebrew formula
python build/homebrew/build.py

# Build Scoop manifest
python build/scoop/build.py

# Build PyPI packages
python build/pypi/build.py
```

Built artifacts are stored in `./dist/` organized by platform and package type.

### Step 3: Binary Testing

The build system includes automated testing of compiled binaries:

#### Test Built Binaries
```bash
# Test binary functionality
python build/pyinstaller/binary_builder.py --test

# Test all platform binaries (if available)
python build/pyinstaller/build_all_platforms.py --test
```

#### Validation Process
- Binary execution test (--version, --help)
- Core functionality verification
- Dependency validation
- Size and performance checks

#### Understanding Test Results
```bash
========================================
BINARY VALIDATION SUMMARY  
========================================
Platform: linux-x86_64
Binary: ./dist/giv-linux-x86_64
Size: 15.2 MB
Tests: PASSED
========================================
```

### Step 4: Publishing

#### Publish to All Channels
```bash
# Publish complete release
./build/publish.py all

# Publish to specific channels
./build/publish.py pypi
./build/publish.py github
./build/publish.py package-managers
```

#### Publishing Process
1. **PyPI**: Upload Python package to PyPI
2. **GitHub**: Create release with binary attachments
3. **Package Managers**: Update Homebrew/Scoop configurations
4. **Verification**: Validate all uploads succeeded

#### Publishing Options
```bash
./build/publish.py [COMMAND] [OPTIONS]

Commands:
  status              Show publishing status
  pypi               Publish to PyPI
  pypi --test        Publish to TestPyPI
  github             Create GitHub release
  package-managers   Update package manager configs
  all                Publish to all channels

Options:
  --dry-run          Show what would be published
  --verbose          Enable verbose output
```

### Step 5: Verification

After publishing, verify packages are available:

```bash
# Test PyPI installation  
pip install giv
giv --version

# Test binary download
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64
chmod +x giv
./giv --version

# Test Homebrew (when available)
brew install giv-cli/tap/giv
giv --version
```

## Distribution Channels

### Binary Downloads (GitHub Releases)
- **Build**: PyInstaller creates platform-specific binaries
- **Validation**: Tests binary execution and core functionality
- **Publish**: Uploaded to GitHub releases as attachments
- **Installation**: Direct download and execution

### PyPI Package  
- **Build**: Creates wheel and source distribution
- **Validation**: Tests package installation and import
- **Publish**: Uploads to pypi.org using twine
- **Installation**: `pip install giv`

### Homebrew Formula (macOS/Linux)
- **Build**: Generates formula with binary download
- **Validation**: Tests formula syntax and installation
- **Publish**: Updates tap repository with new formula
- **Installation**: `brew install giv-cli/tap/giv`

### Scoop Manifest (Windows)
- **Build**: Creates manifest with binary download
- **Validation**: Tests manifest syntax
- **Publish**: Updates bucket repository
- **Installation**: `scoop install giv`

## Troubleshooting

### Build Failures
```bash
# Check build status
./build/build.py status

# Build with verbose output
./build/build.py binaries --verbose

# Test individual components
python build/pyinstaller/binary_builder.py --test
```

### Binary Compilation Issues
```bash
# Check platform support
python build/core/platform_detector.py

# Test PyInstaller directly
poetry run pyinstaller build/pyinstaller/giv.spec

# Check dependencies
poetry install --verbose
```

### Publishing Failures
```bash
# Test publishing in dry-run mode
./build/publish.py all --dry-run

# Check individual channels
./build/publish.py pypi --test
./build/publish.py github --dry-run

# Verify authentication
echo $PYPI_API_TOKEN | cut -c1-10  # Check token exists
gh auth status  # Check GitHub authentication
```

### Common Issues

1. **PyInstaller not found**: Run `poetry install` to install dependencies
2. **Platform not supported**: Check `build/core/platform_detector.py` output
3. **Binary too large**: Ensure UPX is installed for compression
4. **Cross-compilation fails**: Use GitHub Actions for other platforms
5. **Authentication failures**: Set required environment variables
6. **Version conflicts**: Check if version already exists on PyPI/GitHub

## CI/CD Integration

The Python-based build system integrates with GitHub Actions for automated builds:

```yaml
# GitHub Actions example (.github/workflows/build-binaries.yml)
name: Build Binaries
on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        include:
          - platform: linux
            arch: x86_64
            runner: ubuntu-latest
          - platform: darwin
            arch: arm64
            runner: macos-latest
          - platform: windows
            arch: x86_64
            runner: windows-latest
    
    runs-on: ${{ matrix.runner }}
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python and Poetry
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      run: pipx install poetry
    
    - name: Install dependencies
      run: poetry install
    
    - name: Build binary
      run: poetry run python build/pyinstaller/binary_builder.py
    
    - name: Upload binary
      uses: actions/upload-artifact@v3
      with:
        name: giv-${{ matrix.platform }}-${{ matrix.arch }}
        path: dist/giv-*
```

**Benefits for CI/CD:**
- Native Python tooling integration
- Cross-platform matrix builds
- Automated binary compilation
- Direct GitHub integration

## Directory Structure

```
build/
├── README.md                          # Build system documentation
├── build.py                           # Main build orchestrator
├── publish.py                         # Main publishing orchestrator
│
├── core/                              # Core infrastructure
│   ├── __init__.py
│   ├── config.py                      # Build configuration
│   ├── platform_detector.py          # Platform detection
│   └── version_manager.py            # Version management
│
├── pyinstaller/                       # Binary compilation
│   ├── __init__.py
│   ├── binary_builder.py             # PyInstaller wrapper
│   ├── build_all_platforms.py        # Cross-platform builds
│   └── giv.spec                      # PyInstaller spec
│
├── pypi/                             # PyPI packages
│   ├── build.py
│   └── publish.py
│
├── homebrew/                         # Homebrew formula
│   ├── build.py
│   ├── giv.rb
│   └── giv.local.rb
│
├── scoop/                            # Scoop manifest
│   ├── build.py
│   └── giv.json
│
└── [other package managers...]

dist/                                 # Built artifacts
├── giv-linux-x86_64                 # Platform binaries
├── giv-darwin-arm64
├── giv-windows-x86_64.exe
└── packages/                         # Package manager files
```

**Key Features:**
- **Python-native**: All scripts written in Python
- **Modular design**: Separate modules for each component
- **Cross-platform**: Builds on native platforms or GitHub Actions
- **Binary-focused**: Primary distribution via compiled binaries

## Best Practices

1. **Test binaries before publishing**: Use `--test` flags to validate functionality
2. **Use dry-run mode**: Test publishing with `--dry-run` flag first
3. **Use semantic versioning**: Follow semver for version numbers  
4. **Keep authentication secure**: Use environment variables for tokens/passwords
5. **Cross-platform testing**: Use GitHub Actions for multi-platform validation
6. **Document changes**: Update changelogs and release notes
7. **Monitor package repositories**: Verify successful publication
8. **Automate builds**: Use GitHub Actions for consistent cross-platform builds
9. **Check dependencies**: Run `poetry install` to ensure all tools are available
10. **Version control**: Tag releases and maintain clean git history

## Support

For build system issues:
- Check build system status: `./build/build.py status`
- Review Poetry dependencies: `poetry check`
- Verify platform support: `python build/core/platform_detector.py`
- Check authentication environment variables are set
- Test individual components with `--test` or `--dry-run` flags
- Review GitHub Actions logs for automated builds
- Consult package manager documentation for publishing issues