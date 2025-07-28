# Build System for giv CLI

This directory contains the modern Python-based build system for creating cross-platform binaries and packages for the giv CLI tool.

## Overview

The build system has been completely rewritten from Bash scripts to Python for better maintainability, cross-platform support, and integration with modern CI/CD workflows.

### Key Features

- **Cross-platform binary compilation** using PyInstaller
- **Automated GitHub Actions** for building on multiple platforms
- **Package manager integration** (Homebrew, Scoop, PyPI, etc.)
- **Comprehensive testing** of built binaries
- **Size optimization** with UPX compression
- **Release automation** with checksums and signing

## Quick Start

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- Git

### Building Binaries

```bash
# Build for current platform
./build.py binaries

# Build for all platforms (where possible)
./build.py binaries --platforms linux-x86_64,darwin-arm64,windows-x86_64

# Build complete release artifacts
./build.py release
```

### Publishing

```bash
# Publish to PyPI
./publish.py pypi

# Update package manager configurations
./publish.py package-managers

# Publish to all channels
./publish.py all
```

## Architecture

### Core Components

- **`core/`** - Core build system infrastructure
  - `config.py` - Build configuration management
  - `platform_detector.py` - Platform and architecture detection
  - `version_manager.py` - Version handling and validation

- **`pyinstaller/`** - Binary compilation system
  - `binary_builder.py` - PyInstaller wrapper for building binaries
  - `build_all_platforms.py` - Cross-platform build orchestration
  - `giv.spec` - PyInstaller specification file

### Package Managers

- **`pypi/`** - Python Package Index distribution
- **`homebrew/`** - macOS/Linux Homebrew formula
- **`scoop/`** - Windows Scoop manifest
- **`linux/`** - Linux package formats (deb, rpm, AppImage)
- **`snap/`** - Ubuntu Snap packages
- **`flatpak/`** - Linux Flatpak packages

### Automation

- **`.github/workflows/`** - GitHub Actions workflows
  - `build-binaries.yml` - Cross-platform binary builds
  - `release.yml` - Complete release automation

## Build Commands

### Main Build Script (`build.py`)

```bash
# Show build system status
./build.py status

# Build binaries for all platforms
./build.py binaries

# Build specific platforms
./build.py binaries --platforms linux-x86_64,darwin-arm64

# Build PyPI packages
./build.py packages

# Build complete release
./build.py release

# Clean build artifacts
./build.py clean
```

### Publishing Script (`publish.py`)

```bash
# Show publishing status
./publish.py status

# Publish to PyPI
./publish.py pypi

# Publish to Test PyPI
./publish.py pypi --test

# Update package managers
./publish.py package-managers

# Create GitHub release
./publish.py github

# Publish to all channels
./publish.py all
```

### Individual Component Scripts

```bash
# Build binary for current platform
python pyinstaller/binary_builder.py

# Build cross-platform
python pyinstaller/build_all_platforms.py

# Build PyPI packages
python pypi/build.py

# Generate Homebrew formula
python homebrew/build.py

# Generate Scoop manifest
python scoop/build.py
```

## Platform Support

### Target Platforms

| Platform | Architecture | Binary Name | Status |
|----------|-------------|-------------|--------|
| Linux | x86_64 | `giv-linux-x86_64` | ✅ Supported |
| Linux | ARM64 | `giv-linux-arm64` | ✅ Supported |
| macOS | x86_64 (Intel) | `giv-darwin-x86_64` | ✅ Supported |
| macOS | ARM64 (Apple Silicon) | `giv-darwin-arm64` | ✅ Supported |
| Windows | x86_64 | `giv-windows-x86_64.exe` | ✅ Supported |

### Build Methods

1. **Native builds** - Build on the target platform
2. **Cross-compilation** - Limited support for some platforms
3. **GitHub Actions** - Automated builds on all platforms
4. **Docker** - Containerized Linux builds

## Package Manager Support

### Homebrew (macOS/Linux)

```bash
# Generate formula
python homebrew/build.py

# Test formula
python homebrew/build.py --test

# Create tap structure
python homebrew/build.py --create-tap
```

### Scoop (Windows)

```bash
# Generate manifest
python scoop/build.py

# Validate manifest
python scoop/build.py --validate

# Create bucket structure
python scoop/build.py --create-bucket
```

### PyPI (Python Package)

```bash
# Build packages
python pypi/build.py

# Publish to Test PyPI
python pypi/build.py --test-pypi

# Publish to PyPI
python pypi/build.py --pypi
```

## CI/CD Integration

### GitHub Actions

The build system includes comprehensive GitHub Actions workflows:

- **Build Binaries** - Builds on every platform on tag or manual trigger
- **Release** - Complete release process including PyPI publishing
- **Package Configs** - Updates Homebrew/Scoop configurations

### Environment Variables

Required for publishing:

```bash
# PyPI publishing
PYPI_API_TOKEN=your-pypi-token
TEST_PYPI_API_TOKEN=your-test-pypi-token

# GitHub releases (automatically provided)
GITHUB_TOKEN=automatic
```

## Development

### Adding New Platforms

1. Update `core/platform_detector.py` with new platform/architecture
2. Update `pyinstaller/giv.spec` for platform-specific requirements
3. Add platform to GitHub Actions matrix in `build-binaries.yml`
4. Test binary compilation and functionality

### Adding New Package Managers

1. Create new directory under `build/` (e.g., `apt/`, `yum/`)
2. Implement builder class following existing patterns
3. Add integration to main build and publish scripts
4. Update documentation and CI workflows

### Debugging Builds

```bash
# Verbose output
./build.py binaries --verbose

# Test specific binary
python pyinstaller/binary_builder.py --test

# Check build status
./build.py status

# Platform information
python core/platform_detector.py
```

## File Structure

```
build/
├── README.md                       # This file
├── build.py                        # Main build orchestrator
├── publish.py                      # Main publishing orchestrator
├── build-todos.md                  # Development roadmap
│
├── core/                           # Core infrastructure
│   ├── __init__.py
│   ├── config.py
│   ├── platform_detector.py
│   └── version_manager.py
│
├── pyinstaller/                    # Binary compilation
│   ├── __init__.py
│   ├── binary_builder.py
│   ├── build_all_platforms.py
│   └── giv.spec
│
├── pypi/                          # PyPI packages
│   ├── build.py
│   └── publish.py
│
├── homebrew/                      # Homebrew formula
│   ├── build.py
│   ├── giv.rb
│   └── giv.local.rb
│
├── scoop/                         # Scoop manifest
│   ├── build.py
│   └── giv.json
│
└── [other package managers...]
```

## Migration from Bash

The original Bash-based build system has been replaced with this Python implementation. Key improvements:

- **Better cross-platform support** - No shell dependencies
- **Improved error handling** - Detailed error messages and validation
- **Modern tooling** - Poetry, PyInstaller, GitHub Actions
- **Maintainability** - Type hints, documentation, testing
- **Performance** - Parallel builds, optimized binaries

Legacy Bash scripts are preserved in the repository for reference but are no longer used in the build process.

## Troubleshooting

### Common Issues

1. **PyInstaller not found**: Install with `poetry install`
2. **Platform not supported**: Check `core/platform_detector.py` output
3. **Binary too large**: Ensure UPX is installed and working
4. **Cross-compilation fails**: Use GitHub Actions or Docker
5. **Package validation fails**: Check template variables and checksums

### Getting Help

- Check build system status: `./build.py status`
- Verify platform support: `python core/platform_detector.py`
- Test individual components: `python [component]/build.py --help`
- Review build logs in CI/CD for automated builds

## Contributing

When contributing to the build system:

1. Follow existing code patterns and documentation
2. Test on multiple platforms when possible
3. Update this README for significant changes
4. Ensure CI/CD workflows continue to pass
5. Add appropriate error handling and validation