# How to Build and Publish GIV CLI Binaries

This guide explains how to build and publish the `giv` CLI tool as cross-platform binaries using the automated GitHub Actions workflows.

## Overview

The build system creates self-contained binary executables for multiple platforms:
- **Linux** - x86_64 and ARM64 architectures
- **macOS** - Intel and Apple Silicon architectures  
- **Windows** - x86_64 architecture
- **PyPI** - Python package distribution
- **Package Managers** - Homebrew, Scoop, Chocolatey

## Automated Release Process

Publishing releases is fully automated through GitHub Actions. The process is triggered by creating and pushing a Git tag:

### 1. Create and Push Release Tag
```bash
# Tag the current commit with version
git tag v1.2.3
git push origin v1.2.3
```

### 2. Automated Workflow Execution
The release tag triggers the `.github/workflows/release.yml` workflow which:

1. **Builds binaries** for all platforms (Linux x86_64/ARM64, macOS Intel/ARM64, Windows x86_64)
2. **Generates checksums** (SHA256) for all binaries
3. **Creates package manager configurations** (Homebrew formula, Scoop manifest)
4. **Publishes to PyPI** (both main and test repositories)
5. **Creates GitHub release** with all assets attached

### 3. Build Matrix Execution

The system uses parallel matrix builds:

```yaml
# Platform matrix for binary builds
matrix:
  include:
    - platform: linux
      arch: x86_64
      runner: ubuntu-latest
    - platform: linux  
      arch: arm64
      runner: ubuntu-latest  # Cross-compilation
    - platform: macos
      arch: x86_64
      runner: macos-13       # Intel runner
    - platform: macos
      arch: arm64
      runner: macos-latest   # Apple Silicon runner
    - platform: windows
      arch: x86_64
      runner: windows-latest
```

## Build Architecture

The build system uses modern Python tooling with automation:

- **Poetry**: Dependency management and virtual environments
- **PyInstaller**: Python to binary compilation
- **GitHub Actions**: Automated CI/CD pipeline
- **Cross-compilation**: ARM64 Linux builds on x86_64
- **Checksums**: SHA256 verification for all binaries

## Manual Development Builds

For local development and testing:

### Prerequisites
- **Python 3.8+** - For running build scripts
- **Poetry** - Dependency management (`pip install poetry`)
- **Git** - Version control

### Local Binary Building
```bash
# Install dependencies
poetry install

# Build binary for current platform
poetry run python build/build_binary.py

# Binary created as giv-{platform}-{arch}[.exe]
```

### Development Testing
```bash
# Run tests
poetry run pytest

# Run specific test categories  
poetry run pytest -m unit
poetry run pytest -m integration

# Build and test binary
poetry run python build/build_binary.py
./giv-linux-x86_64 --version
```

## Repository Secrets Configuration

The automated workflows require these repository secrets:

```bash
# PyPI publishing
PYPI_API_TOKEN="your-pypi-token"

# GitHub releases (automatically provided)
GITHUB_TOKEN="automatically-provided-by-github"

# Optional: TestPyPI for testing
TEST_PYPI_API_TOKEN="your-test-pypi-token"
```

### Required Secrets Setup in GitHub

1. **PYPI_API_TOKEN**: Create token at https://pypi.org/manage/account/token/
2. **TEST_PYPI_API_TOKEN**: Create token at https://test.pypi.org/manage/account/token/
3. **GITHUB_TOKEN**: Automatically provided by GitHub Actions

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

### 2. Local Development and Testing
```bash
# Build for current platform
poetry run python build/build_binary.py

# Run comprehensive tests
poetry run pytest

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration

# Type checking and linting
poetry run mypy giv/ tests/
poetry run black giv/ tests/
poetry run flake8 giv/ tests/
```

### 3. Automated Release Process
```bash
# Create and push a release tag
git tag v1.2.3
git push origin v1.2.3

# GitHub Actions automatically:
# 1. Builds binaries for all platforms
# 2. Runs comprehensive test suite
# 3. Generates checksums
# 4. Creates package manager configurations
# 5. Publishes to PyPI
# 6. Creates GitHub release with assets
```

## GitHub Actions Workflows

### Build Workflows

The project uses specialized workflows for different purposes:

#### 1. **CI Build (build-ci.yml)**
- **Trigger**: Pull requests, pushes to main
- **Platforms**: Linux/macOS/Windows x86_64 only  
- **Purpose**: Fast feedback for development
- **Features**: Dependency caching, test execution

#### 2. **Binary Build (build-binaries.yml)** 
- **Trigger**: Called by release workflow
- **Platforms**: All supported platforms including ARM64
- **Purpose**: Production binary compilation
- **Features**: Cross-compilation, checksum generation

#### 3. **Release (release.yml)**
- **Trigger**: Git tag creation (v*.*.*)
- **Purpose**: Complete release automation
- **Outputs**: Binaries, packages, GitHub release

### Workflow Features

```yaml
# Cross-compilation setup (Linux ARM64)
- name: Setup cross-compilation
  run: |
    sudo apt-get update
    sudo apt-get install -y gcc-aarch64-linux-gnu
    echo "CC=aarch64-linux-gnu-gcc" >> $GITHUB_ENV

# Binary naming convention
binary_name: giv-${{ matrix.platform }}-${{ matrix.arch }}${{ matrix.platform == 'windows' && '.exe' || '' }}

# Checksum generation
- name: Generate checksums
  run: |
    cd dist/
    # Use cross-platform checksum command
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum * > checksums.sha256
    else
      shasum -a 256 * > checksums.sha256
    fi
```

## Build System Architecture

### Binary Compilation

The build system uses PyInstaller with optimized settings:

```python
# build/build_binary.py core functionality
def build_binary():
    """Build platform-specific binary."""
    binary_name = get_binary_name()
    
    # PyInstaller configuration
    command = [
        "pyinstaller",
        "--onefile",          # Single executable
        "--name", binary_name, 
        "--distpath", "dist/",
        "giv/__main__.py"     # Entry point
    ]
    
    subprocess.run(command, check=True)
```

### Package Manager Integration

Package managers are updated automatically during releases:

```python
# build/homebrew/build.py - Homebrew tap creation
def create_tap_structure(tap_dir):
    """Create Homebrew tap directory structure."""
    formula_dir = tap_dir / "Formula"
    formula_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate formula file
    generate_formula(formula_dir / "giv.rb")

# build/scoop/build.py - Scoop bucket creation  
def create_bucket_structure(bucket_dir):
    """Create Scoop bucket structure."""
    bucket_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate manifest
    generate_manifest(bucket_dir / "giv.json")
```

## Release Process Details

### Automated Release Steps

When a tag is pushed, the release workflow executes these steps:

#### 1. **Preparation**
- Checkout code with full history
- Setup Python and Poetry
- Install dependencies
- Validate project configuration

#### 2. **Binary Compilation**
- Matrix build across all platforms
- Cross-compilation for ARM64 Linux
- PyInstaller optimization
- Binary verification testing

#### 3. **Package Generation**
- Homebrew formula with tap structure
- Scoop manifest with bucket structure  
- Chocolatey package specification
- PyPI wheel and source distributions

#### 4. **Publishing**
- Upload to PyPI (main repository)
- Upload to TestPyPI (for testing)
- Create GitHub release with assets
- Generate and attach checksums

#### 5. **Validation**
- Verify all uploads completed
- Test download URLs
- Validate package manager integrations

### Binary Testing and Validation

Each compiled binary undergoes automated validation:

```bash
# Validation tests run by GitHub Actions
./giv-{platform}-{arch} --version    # Version check
./giv-{platform}-{arch} --help       # Help output
./giv-{platform}-{arch} config view  # Config functionality
```

#### Test Matrix Results
The release process validates binaries across platforms:

```
========================================
BINARY VALIDATION SUMMARY  
========================================
✅ Linux x86_64   - giv-linux-x86_64    (14.8 MB)
✅ Linux ARM64    - giv-linux-arm64     (14.9 MB)  
✅ macOS Intel    - giv-macos-x86_64    (15.1 MB)
✅ macOS ARM64    - giv-macos-arm64     (14.7 MB)
✅ Windows x86_64 - giv-windows-x86_64  (15.3 MB)
========================================
All binaries validated successfully.
```

## Troubleshooting

### Common Release Issues

#### 1. **Tag Creation Problems**
```bash
# Ensure tag follows version pattern
git tag -l | grep v1.2.3

# Delete and recreate tag if needed
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
git tag v1.2.3
git push origin v1.2.3
```

#### 2. **Build Failures**
Check the GitHub Actions logs for specific error details:

- **Linux ARM64**: Cross-compilation toolchain issues
- **macOS**: Code signing or architecture problems  
- **Windows**: Visual Studio Build Tools missing
- **PyPI**: Authentication token or package conflicts

#### 3. **Publishing Failures**
Common publishing issues and solutions:

```bash
# PyPI token issues
# Solution: Regenerate token in PyPI account settings

# TestPyPI upload conflicts  
# Solution: Increment version number or use dev versions

# GitHub release conflicts
# Solution: Delete existing release and retry
```

### Manual Override Process

If automated release fails, manual steps can be used:

#### 1. **Manual Binary Build**
```bash
# Build locally for current platform
poetry run python build/build_binary.py

# Test the binary
./dist/giv-* --version
```

#### 2. **Manual PyPI Publishing**
```bash
# Build package
poetry build

# Upload to TestPyPI first
poetry publish --repository testpypi

# Upload to PyPI
poetry publish
```

#### 3. **Manual GitHub Release**  
```bash
# Create release using GitHub CLI
gh release create v1.2.3 dist/* --title "v1.2.3" --notes "Release notes"
```

### Monitoring and Verification

#### Release Verification Checklist

After a release completes:

- [ ] **GitHub Release**: Check all binaries are attached
- [ ] **PyPI**: Verify package is available (`pip install giv`)
- [ ] **TestPyPI**: Confirm test deployment worked
- [ ] **Checksums**: Validate SHA256 checksums match
- [ ] **Download Test**: Test binary downloads from GitHub
- [ ] **Installation Test**: Test package manager installations

#### Package Manager Updates

Package managers update automatically, but verify:

```bash
# Homebrew (may take time to propagate)
brew install giv-cli/tap/giv

# Scoop
scoop install giv

# PyPI
pip install giv
# PyPI
pip install giv
```

## Distribution Channels

The automated release process publishes to multiple distribution channels:

### 1. GitHub Releases (Primary)
- **Location**: https://github.com/giv-cli/giv-py/releases
- **Content**: Platform-specific binaries, checksums, source code
- **Updates**: Automatic on tag creation
- **Usage**: Direct binary downloads

### 2. PyPI (Python Package Index)
- **Location**: https://pypi.org/project/giv/
- **Content**: Python wheel and source distribution
- **Updates**: Automatic via GitHub Actions
- **Usage**: `pip install giv`

### 3. TestPyPI (Testing)
- **Location**: https://test.pypi.org/project/giv/
- **Content**: Pre-release testing packages
- **Updates**: Automatic for all releases
- **Usage**: `pip install -i https://test.pypi.org/simple/ giv`

### 4. Package Managers

#### Homebrew (macOS/Linux)
- **Location**: https://github.com/giv-cli/homebrew-tap
- **Content**: Formula for tap-based installation
- **Updates**: Automatic tap and formula generation
- **Usage**: `brew install giv-cli/tap/giv`

#### Scoop (Windows)
- **Location**: https://github.com/giv-cli/scoop-bucket  
- **Content**: Manifest for bucket-based installation
- **Updates**: Automatic bucket and manifest generation
- **Usage**: `scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket && scoop install giv`

#### Chocolatey (Windows)
- **Location**: Generated automatically
- **Content**: Package specification
- **Updates**: Manual submission to Chocolatey gallery
- **Usage**: `choco install giv`

## Binary Naming Convention

All binaries follow a consistent naming pattern:

```
giv-{platform}-{arch}[.exe]

Examples:
- giv-linux-x86_64
- giv-linux-arm64  
- giv-macos-x86_64
- giv-macos-arm64
- giv-windows-x86_64.exe
```

This naming ensures clear platform identification and prevents conflicts.

## Version Management

### Semantic Versioning
The project follows semantic versioning (SemVer):
- **Major**: Breaking changes (v2.0.0)
- **Minor**: New features (v1.1.0)  
- **Patch**: Bug fixes (v1.0.1)

### Release Types
- **Stable releases**: Tagged versions (v1.2.3)
- **Pre-releases**: Beta/RC versions (v1.2.3-beta.1)
- **Development**: Commit-based versions (automated)

The version is automatically extracted from Git tags and updated across all distribution channels.
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
## GitHub Actions Integration

All build and publishing is handled through GitHub Actions workflows:

### Workflow Configuration

The release process is triggered by git tags:

```yaml
# .github/workflows/release.yml
on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-binaries:
    uses: ./.github/workflows/build-binaries.yml
    
  create-release:
    needs: build-binaries
    runs-on: ubuntu-latest
    steps:
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
          
  publish-pypi:
    needs: build-binaries
    runs-on: ubuntu-latest
    steps:
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

### Build Matrix

Cross-platform builds using matrix strategy:

```yaml
strategy:
  matrix:
    include:
      - platform: linux
        arch: x86_64
        runner: ubuntu-latest
      - platform: linux
        arch: arm64
        runner: ubuntu-latest
      - platform: macos
        arch: x86_64
        runner: macos-13
      - platform: macos
        arch: arm64
        runner: macos-latest
      - platform: windows
        arch: x86_64
        runner: windows-latest
```

## Directory Structure

The build system is organized for maintainability:

```
build/
├── build_binary.py                   # Core binary builder
├── README.md                         # Build documentation
├── core/                             # Core utilities
│   ├── config.py                     # Build configuration
│   ├── utils.py                      # Helper functions
│   └── version_manager.py            # Version management
├── homebrew/                         # Homebrew formula generation
│   ├── build.py                      # Formula builder
│   └── giv.rb                        # Formula template
├── scoop/                            # Scoop manifest generation
│   ├── build.py                      # Manifest builder
│   └── giv.json                      # Manifest template
├── pypi/                             # PyPI package building
│   ├── build.py                      # Package builder
│   └── setup.py                      # Setup configuration
└── [other package managers...]

.github/workflows/                    # GitHub Actions
├── build.yml                         # Main build workflow
├── build-ci.yml                      # CI-focused builds
├── build-binaries.yml                # Binary compilation
└── release.yml                       # Release automation
```

## Best Practices

### For Development
1. **Local testing**: Build and test binaries locally before pushing
2. **Incremental versions**: Use proper semantic versioning
3. **Clean workspace**: Ensure no uncommitted changes before tagging
4. **Test automation**: Run full test suite before releases

### For Releases  
1. **Tag format**: Use `v1.2.3` format for version tags
2. **Release notes**: GitHub generates automatic release notes
3. **Validation**: Monitor GitHub Actions for build success
4. **Distribution**: Verify all distribution channels receive updates

### For Troubleshooting
1. **GitHub Actions logs**: Primary source for build issues
2. **Local reproduction**: Use `poetry run python build/build_binary.py` to debug
3. **Platform testing**: Test binaries on target platforms
4. **Package verification**: Test installations from published packages

## Support and Maintenance

### Monitoring Release Health
- **GitHub Actions**: Monitor workflow success rates
- **Package repositories**: Check PyPI download statistics
- **User feedback**: Track issues and feature requests
- **Binary validation**: Automated testing in CI

### Common Maintenance Tasks
- **Dependencies**: Regular Poetry dependency updates
- **Security**: Automated security scanning in CI
- **Platform support**: Adding new platforms as needed
- **Package managers**: Maintaining formulas and manifests

### Getting Help
- **Build issues**: Check GitHub Actions workflow logs
- **Local problems**: Use `poetry install` and `poetry run pytest`
- **Distribution issues**: Verify repository secrets and permissions
- **Documentation**: Reference this guide and build/ README files

The automated system ensures consistent, reliable releases while minimizing manual intervention and potential errors.