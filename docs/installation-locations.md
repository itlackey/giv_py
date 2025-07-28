# Installation Locations and File Layout

This document describes where the giv CLI tool and its components are installed on different platforms and through different installation methods.

## Binary Distributions

### GitHub Releases (Direct Download)

When you download binaries directly from GitHub releases, you can place them anywhere you prefer:

**Recommended locations:**

- **Linux/macOS**: `/usr/local/bin/giv` or `~/.local/bin/giv`
- **Windows**: `C:\Program Files\giv\giv.exe` or `%USERPROFILE%\bin\giv.exe`

**Template location:**
Templates are bundled inside the binary using PyInstaller and are extracted at runtime to a temporary directory. The binary is completely self-contained.

**Example installation:**
```bash
# Linux/macOS
sudo curl -L -o /usr/local/bin/giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64
sudo chmod +x /usr/local/bin/giv

# Or for user installation
mkdir -p ~/.local/bin
curl -L -o ~/.local/bin/giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64
chmod +x ~/.local/bin/giv
```

### PyPI Installation (pip install giv)

When installed via PyPI, files are placed in the Python environment:

**Binary location:**
- **Linux/macOS**: `$VIRTUAL_ENV/bin/giv` or `~/.local/bin/giv` (with --user)
- **Windows**: `$VIRTUAL_ENV\Scripts\giv.exe` or `%APPDATA%\Python\Scripts\giv.exe`

**Template location:**
- **All platforms**: Inside the Python package at `site-packages/giv/templates/`
- Example: `~/.local/lib/python3.11/site-packages/giv/templates/`

**Configuration location:**
- **All platforms**: `~/.giv/config` (user config) or `.giv/config` (project config)

### Homebrew (macOS/Linux)

**Binary location:**
- **macOS**: `/opt/homebrew/bin/giv` (Apple Silicon) or `/usr/local/bin/giv` (Intel)
- **Linux**: `/home/linuxbrew/.linuxbrew/bin/giv`

**Template location:**
Templates are bundled inside the binary (self-contained).

**Installation:**
```bash
brew install giv-cli/tap/giv
```

### Scoop (Windows)

**Binary location:**
- **Windows**: `%USERPROFILE%\scoop\apps\giv\current\giv-windows-x86_64.exe`
- **Shimmed path**: `%USERPROFILE%\scoop\shims\giv.exe`

**Template location:**
Templates are bundled inside the binary (self-contained).

**Installation:**
```powershell
scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket
scoop install giv
```

## Configuration Files

Regardless of installation method, configuration files are stored in the same locations:

### User Configuration
- **Path**: `~/.giv/config`
- **Purpose**: Global user settings that apply to all projects
- **Format**: INI-style key=value pairs

### Project Configuration  
- **Path**: `.giv/config` (in project root)
- **Purpose**: Project-specific settings that override user settings
- **Format**: INI-style key=value pairs

### Priority Order
1. Command-line arguments (highest priority)
2. Environment variables (`GIV_*`)
3. Project config (`.giv/config`)
4. User config (`~/.giv/config`)
5. Built-in defaults (lowest priority)

## Template Customization

### For PyPI Installation
You can customize templates by copying them from the package and creating a project-specific template directory:

```bash
# Copy templates to your project
mkdir -p .giv/templates
cp -r $(python -c "import giv; print(giv.__path__[0])")/templates/* .giv/templates/

# Edit templates
nano .giv/templates/message_prompt.md
```

### For Binary Installation
Since templates are bundled in the binary, you need to create custom templates:

```bash
# Initialize project with default templates
giv init

# This creates .giv/templates/ with default templates that you can modify
ls .giv/templates/
```

## File Sizes and Dependencies

### Binary Distributions
- **Size**: ~15-25 MB (self-contained with Python runtime)
- **Dependencies**: None (completely standalone)
- **Python version**: Bundled Python 3.11 runtime

### PyPI Installation
- **Size**: ~500 KB (package only)
- **Dependencies**: Python 3.8.1+, requests, click, packaging
- **Python version**: Uses system/virtual environment Python

## Verification

To verify your installation and see where files are located:

```bash
# Check binary location
which giv
type giv

# Check version and template access
giv --version
giv --help

# Test template access (should work without errors)
giv message --dry-run

# Check configuration
giv config list
```

## Platform-Specific Notes

### Linux
- Binary installations to `/usr/local/bin/` require sudo
- User installations to `~/.local/bin/` require adding to PATH
- AppImage format may be supported in future releases

### macOS  
- Binaries may require permission in System Preferences > Security & Privacy
- Homebrew automatically handles PATH configuration
- Universal binaries support both Intel and Apple Silicon

### Windows
- Scoop automatically handles PATH configuration
- Manual installations require adding to PATH environment variable
- PowerShell execution policy may need to be adjusted

## Troubleshooting

### Binary not found
```bash
# Check if binary location is in PATH
echo $PATH

# Add to PATH (example for bash/zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Templates not working
```bash
# For binary installations, initialize templates
giv init

# For PyPI installations, check package installation
python -c "import giv; print(giv.__file__)"
```

### Permission denied
```bash
# Make binary executable
chmod +x /path/to/giv

# Or fix ownership
sudo chown $USER:$USER /path/to/giv
```

This layout ensures that giv works consistently across all installation methods while providing the flexibility for users to customize templates and configuration as needed.