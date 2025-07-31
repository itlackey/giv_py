# Installation

## Requirements

- [Git](https://git-scm.com/) (version 2.25 or newer)
- [Ollama](https://ollama.com/) (optional, for local AI models)

> **Note:** giv is distributed as compiled binaries with no runtime dependencies.

## Installation Methods Comparison

Choose the method that best fits your needs:

| Method | Size | Dependencies | Auto-updates | Platform Support |
|--------|------|--------------|--------------|------------------|
| Direct Download | ~15MB | None | Manual | Linux, macOS, Windows |
| Installation Script | ~15MB | None | Manual | Linux, macOS, Windows |
| Homebrew | ~15MB | None | `brew upgrade` | macOS, Linux |
| Scoop | ~15MB | None | `scoop update` | Windows |
| PyPI | ~500KB | Python 3.8.1+ | `pip install -U` | Cross-platform |

## Quick Install (Recommended)

### Installation Script
Install the latest version using the installation script:

```bash
curl -fsSL https://raw.githubusercontent.com/giv-cli/giv-py/main/install.sh | sh
```

This script will:
- Detect your platform (Linux, macOS, Windows)
- Download the appropriate binary
- Install it to a directory in your PATH
- Set up the necessary permissions

### Direct Download
```bash
# Linux x86_64
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64
chmod +x giv && sudo mv giv /usr/local/bin/

# macOS Apple Silicon  
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-macos-arm64
chmod +x giv && sudo mv giv /usr/local/bin/

# Windows x86_64
curl -L -o giv.exe https://github.com/giv-cli/giv-py/releases/latest/download/giv-windows-x86_64.exe
# Move to a directory in your PATH
```

## Manual Installation

### Download Binary Releases

Download the latest binary for your platform from the [releases page](https://github.com/giv-cli/giv-py/releases):

- **Linux (x86_64)**: `giv-linux-x86_64`
- **Linux (ARM64)**: `giv-linux-arm64`
- **macOS (Intel)**: `giv-macos-x86_64`
- **macOS (Apple Silicon)**: `giv-macos-arm64`
- **Windows (x86_64)**: `giv-windows-x86_64.exe`

### Install Manually

1. Download the binary for your platform
2. Make it executable (Linux/macOS): `chmod +x giv-*`
3. Move it to a directory in your PATH: `mv giv-* /usr/local/bin/giv`

### Platform-Specific Instructions

#### Linux/macOS
```bash
# Download (example for Linux x86_64)
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64

# Make executable
chmod +x giv

# Install system-wide
sudo mv giv /usr/local/bin/

# Or install user-local
mkdir -p ~/.local/bin
mv giv ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
```

#### Windows
```powershell
# Download using PowerShell
Invoke-WebRequest -Uri "https://github.com/giv-cli/giv-py/releases/latest/download/giv-windows-x86_64.exe" -OutFile "giv.exe"

# Move to a directory in PATH (example)
Move-Item giv.exe C:\Windows\System32\giv.exe
```

## Package Manager Installation

### Homebrew (macOS/Linux)
```bash
brew install giv-cli/tap/giv
```

### Scoop (Windows)
```bash
scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket
scoop install giv
```

### apt (Ubuntu/Debian)
```bash
curl -fsSL https://raw.githubusercontent.com/giv-cli/giv-py/main/install-apt.sh | sudo sh
sudo apt update
sudo apt install giv
```

### yum/dnf (RHEL/Fedora/CentOS)
```bash
curl -fsSL https://raw.githubusercontent.com/giv-cli/giv-py/main/install-rpm.sh | sudo sh
sudo dnf install giv  # or yum install giv
```

## PyPI Installation

To install `giv` via PyPI, ensure you have Python 3.8.1 or later installed. Run the following command:

```bash
pip install giv
```

After installation, verify the installation:

```bash
giv --version
```

Initialize `giv` in your project:

```bash
giv init
```

This will create a `.giv/config` file and prompt you for configuration values like API keys and project settings.

## After Installation

## After Installation

### First Run

Once installed, initialize giv in your project:

```bash
# Verify installation
giv --version

# Initialize giv in your project
giv init

# Configure your AI provider (optional for dry-run testing)
giv config set api.key "your-api-key"
giv config set api.url "https://api.openai.com/v1/chat/completions"

# Generate your first commit message
giv message --dry-run  # Test without API call
giv message            # Generate actual message
```

### Basic Usage Examples

```bash
# Generate commit message for current changes
giv message

# Generate message for specific revision range
giv message HEAD~3..HEAD

# Generate message for staged changes only
giv message --cached

# Create a project summary
giv summary v1.0.0..HEAD

# Generate changelog entry
giv changelog v1.0.0..HEAD --output-file CHANGELOG.md

# Create release notes
giv release-notes v1.2.0..HEAD --output-file RELEASE_NOTES.md
```

**For detailed usage and advanced examples, see [App Specification](app-spec.md).**

## Troubleshooting

### Common Installation Issues

#### Binary not found
```bash
# Check if installation directory is in PATH
echo $PATH

# Add to PATH (bash/zsh)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### Permission denied
```bash
# Make binary executable
chmod +x /path/to/giv

# Or install to user directory
mkdir -p ~/.local/bin
mv giv ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
```

#### Template errors
```bash
# Initialize templates in project
giv init

# Check template access
giv message --dry-run
```

### Platform-Specific Issues

#### macOS
- **Gatekeeper warning**: Run `xattr -d com.apple.quarantine /path/to/giv` to remove quarantine
- **Permission issues**: Use `brew install` instead of manual installation

#### Windows
- **Execution policy**: Run `Set-ExecutionPolicy RemoteSigned` in PowerShell as Administrator
- **PATH not updated**: Restart terminal or add manually through System Properties

#### Linux
- **Permission denied**: Ensure binary is executable and in a directory with execute permissions
- **Missing dependencies**: All dependencies are statically linked, no additional packages needed

Verify the installation:

```bash
giv --version
```

Initialize giv in your project:

```bash
giv init
```

This will create a `.giv/config` file and prompt you for configuration values like API keys and project settings.

## Upgrading

### Using Installation Script
Re-run the installation script to get the latest version:
```bash
curl -fsSL https://raw.githubusercontent.com/giv-cli/giv-py/main/install.sh | sh
```

### Using Package Managers
```bash
# Homebrew
brew upgrade giv

# Scoop  
scoop update giv

# apt
sudo apt update && sudo apt upgrade giv

# dnf/yum
sudo dnf upgrade giv
```

### Manual Upgrade
1. Download the new binary from releases
2. Replace the existing binary in your PATH
3. Verify with `giv --version`

## Self-Update

giv includes a self-update feature:

```bash
# Update to latest version
giv update

# Update to specific version
giv update v1.2.3

# Check available versions
giv available-releases
```

## Uninstall

### Remove Binary
```bash
# Find giv location
which giv

# Remove it
sudo rm /usr/local/bin/giv  # Adjust path as needed
```

### Package Managers
```bash
# Homebrew
brew uninstall giv

# Scoop
scoop uninstall giv

# apt
sudo apt remove giv

# dnf/yum
sudo dnf remove giv
```

Project-specific configuration in `.giv/` directories will remain untouched.

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure the installation directory is in your PATH
2. **Permission denied**: Make sure the binary is executable (`chmod +x giv`)
3. **Wrong architecture**: Download the correct binary for your platform
4. **Self-update fails**: Download manually from releases page

### Checking Installation

```bash
# Verify giv installation
giv --version
giv --help

# Check installation location
which giv
ls -la $(which giv)
```

### PATH Issues

If `giv` command is not found after installation:

```bash
# Check if binary exists
ls -la /usr/local/bin/giv
ls -la ~/.local/bin/giv

# Add to PATH if needed
export PATH="/usr/local/bin:$PATH"
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (add to shell profile)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Platform-Specific Issues

#### macOS
- **Gatekeeper warning**: Run `xattr -d com.apple.quarantine /path/to/giv` to remove quarantine
- **Permission issues**: Use `brew install` instead of manual installation

#### Windows
- **Execution policy**: Run `Set-ExecutionPolicy RemoteSigned` in PowerShell as Administrator
- **PATH not updated**: Restart terminal or add manually through System Properties

#### Linux
- **Permission denied**: Ensure binary is executable and in a directory with execute permissions
- **Missing dependencies**: All dependencies are statically linked, no additional packages needed
