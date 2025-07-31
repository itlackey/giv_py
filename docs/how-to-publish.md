# How to Build and Publish GIV CLI Binaries

This guide explains how to build and publish the `giv` CLI tool as cross-platform binaries using the automated GitHub Actions workflows.

## Overview

The build system creates self-contained binary executables for multiple platforms:
- **Linux** - x86_64 and ARM64 architectures
- **macOS** - Intel and Apple Silicon architectures  
- **Windows** - x86_64 architecture
- **PyPI** - Python package distribution
- **Package Managers** - Homebrew, Scoop, Chocolatey

## Quick Release Process

Publishing releases is fully automated through GitHub Actions. The process is triggered by creating and pushing a Git tag:

```bash
# Tag the current commit with version
git tag v1.2.3
git push origin v1.2.3
```

This automatically triggers the release workflow which:
1. **Builds binaries** for all platforms (Linux x86_64/ARM64, macOS Intel/ARM64, Windows x86_64)
2. **Generates checksums** (SHA256) for all binaries
3. **Creates package manager configurations** (Homebrew formula, Scoop manifest)
4. **Publishes to PyPI** (both main and test repositories)
5. **Creates GitHub release** with all assets attached

## Build Architecture

The build system uses modern Python tooling:

- **Poetry**: Dependency management and virtual environments
- **PyInstaller**: Python to binary compilation
- **GitHub Actions**: Automated CI/CD pipeline with matrix builds
- **Cross-compilation**: ARM64 Linux builds on x86_64
- **Checksums**: SHA256 verification for all binaries

### Platform Matrix

```yaml
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

## Development Workflow

### Prerequisites
- **Python 3.8+** - For running build scripts
- **Poetry** - Dependency management (`pip install poetry`)
- **Git** - Version control

### Local Development Setup
```bash
# Clone repository
git clone https://github.com/giv-cli/giv-py.git
cd giv-py

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Local Binary Building
```bash
# Build binary for current platform
poetry run python build/build_binary.py

# Binary created as giv-{platform}-{arch}[.exe]
# Test the binary
./giv-linux-x86_64 --version
```

### Development Testing
```bash
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

## GitHub Actions Workflows

### Workflow Structure

The project uses specialized workflows:

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

### Required Repository Secrets

Configure these secrets in your GitHub repository:

| Secret | Purpose | Required |
|--------|---------|----------|
| `PYPI_API_TOKEN` | PyPI publishing | Yes |
| `TEST_PYPI_API_TOKEN` | TestPyPI publishing | Optional |
| `GITHUB_TOKEN` | GitHub releases | Auto-provided |

**Setup Instructions:**
1. Create PyPI token at https://pypi.org/manage/account/token/
2. Create TestPyPI token at https://test.pypi.org/manage/account/token/
3. Add tokens to repository secrets in GitHub

## Binary Validation

Each compiled binary undergoes automated validation:

```bash
# Validation tests run by GitHub Actions
./giv-{platform}-{arch} --version    # Version check
./giv-{platform}-{arch} --help       # Help output
./giv-{platform}-{arch} config list  # Config functionality
```

### Validation Results
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
```

## Distribution Channels

The automated release process publishes to multiple distribution channels:

### 1. GitHub Releases (Primary)
- **Location**: https://github.com/giv-cli/giv-py/releases
- **Content**: Platform-specific binaries, checksums, source code
- **Usage**: Direct binary downloads

### 2. PyPI (Python Package Index)
- **Location**: https://pypi.org/project/giv/
- **Content**: Python wheel and source distribution
- **Usage**: `pip install giv`

### 3. TestPyPI (Testing)
- **Location**: https://test.pypi.org/project/giv/
- **Content**: Pre-release testing packages
- **Usage**: `pip install -i https://test.pypi.org/simple/ giv`

### 4. Package Managers

#### Homebrew (macOS/Linux)
- **Location**: https://github.com/giv-cli/homebrew-tap
- **Usage**: `brew install giv-cli/tap/giv`

#### Scoop (Windows)
- **Location**: https://github.com/giv-cli/scoop-bucket  
- **Usage**: `scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket && scoop install giv`

#### Chocolatey (Windows)
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

## Release Verification Checklist

After a release completes:

- [ ] **GitHub Release**: Check all binaries are attached
- [ ] **PyPI**: Verify package is available (`pip install giv`)
- [ ] **TestPyPI**: Confirm test deployment worked
- [ ] **Checksums**: Validate SHA256 checksums match
- [ ] **Download Test**: Test binary downloads from GitHub
- [ ] **Installation Test**: Test package manager installations

### Package Manager Updates

Package managers update automatically, but verify:

```bash
# Homebrew (may take time to propagate)
brew install giv-cli/tap/giv

# Scoop
scoop install giv

# PyPI
pip install giv
```

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