# giv - AI-Powered Git History Assistant

**giv** (pronounced "give") is a powerful CLI tool that transforms raw Git history into polished commit messages, summaries, changelogs, release notes, and announcements. This Python implementation provides cross-platform binary distribution with zero dependencies.

[![Build Status](https://img.shields.io/badge/build-passing-green)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ Key Features

- **🚀 Self-contained binaries** - No Python installation required
- **🤖 Multiple AI backends** - OpenAI, Anthropic, Ollama, and custom endpoints  
- **📝 Rich command suite** - Generate messages, summaries, changelogs, and release notes
- **🎯 Smart Git integration** - Support for revision ranges, pathspecs, and staged changes
- **⚙️ Flexible configuration** - Project and user-level settings with inheritance
- **🔧 Template system** - Customizable prompts for all output types
- **📦 Multiple installation methods** - Direct download, package managers, or PyPI

## 🚀 Quick Start

### Install (Choose one method)

#### Direct Download (Recommended)
```bash
# Linux x86_64
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-linux-x86_64
chmod +x giv && sudo mv giv /usr/local/bin/

# macOS Apple Silicon  
curl -L -o giv https://github.com/giv-cli/giv-py/releases/latest/download/giv-darwin-arm64
chmod +x giv && sudo mv giv /usr/local/bin/

# Windows x86_64
curl -L -o giv.exe https://github.com/giv-cli/giv-py/releases/latest/download/giv-windows-x86_64.exe
# Move to a directory in your PATH
```

#### Package Managers
```bash
# Homebrew (macOS/Linux)
brew install giv-cli/tap/giv

# Scoop (Windows)
scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket
scoop install giv

# PyPI (requires Python 3.8.1+)
pip install giv
```

### First Run
```bash
# Initialize giv in your project
giv init

# Configure your AI provider (optional for testing)
giv config set api.key "your-api-key"
giv config set api.url "https://api.openai.com/v1/chat/completions"

# Generate your first commit message
giv message --dry-run  # Test without API call
giv message            # Generate actual message
```

## 📚 Usage Examples

### Basic Commands
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

### Advanced Usage
```bash
# Filter by file patterns
giv message HEAD~1..HEAD src/ docs/

# Scan for TODOs in specific files
giv changelog --todo-files '*.py' --todo-pattern 'TODO:'

# Use custom templates
giv message --prompt-file my-template.md

# Different output modes
giv changelog --output-mode append    # Add to end
giv changelog --output-mode prepend   # Add to beginning  
giv changelog --output-mode update    # Replace existing section
```

### Configuration Management
```bash
# List all configuration
giv config list

# Set API configuration
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4"
giv config set api.key "your-api-key"

# Set project metadata
giv config set project.title "My Project"
giv config set output.mode "auto"

# Remove configuration
giv config unset old.setting
```

## ⚙️ Configuration

Configuration is stored in simple key=value files with inheritance:

1. **Command-line arguments** (highest priority)
2. **Environment variables** (`GIV_*` prefix)
3. **Project config** (`.giv/config` in project root)
4. **User config** (`~/.giv/config` in home directory)
5. **Built-in defaults** (lowest priority)

### Example Configuration
```ini
# ~/.giv/config or .giv/config
api.url=https://api.openai.com/v1/chat/completions
api.model=gpt-4
api.key=your-api-key-here
output.mode=auto
project.title=My Awesome Project
```

## 🎨 Template Customization

Customize prompts for different output types:

```bash
# Initialize project templates (copies defaults to .giv/templates/)
giv init

# Edit templates
nano .giv/templates/message_prompt.md
nano .giv/templates/changelog_prompt.md

# Use custom template for one command
giv message --prompt-file custom-prompt.md
```

### Available Templates
- `message_prompt.md` - Commit message generation
- `summary_prompt.md` - Change summaries
- `changelog_prompt.md` - Changelog entries
- `release_notes_prompt.md` - Release documentation
- `announcement_prompt.md` - Marketing announcements

## 🏗️ Installation Methods Comparison

| Method | Size | Dependencies | Auto-updates | Platform Support |
|--------|------|--------------|--------------|------------------|
| Direct Download | ~15MB | None | Manual | Linux, macOS, Windows |
| Homebrew | ~15MB | None | `brew upgrade` | macOS, Linux |
| Scoop | ~15MB | None | `scoop update` | Windows |
| PyPI | ~500KB | Python 3.8.1+ | `pip install -U` | Cross-platform |

## 🔧 Development

### Building from Source
```bash
# Clone repository
git clone https://github.com/giv-cli/giv-py.git
cd giv-py

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Build binary for current platform
python build/build.py binaries

# Built binary location
./dist/1.0.0/linux-x86_64/giv-linux-x86_64
```

### Build System
- **Poetry** for dependency management
- **PyInstaller** for binary compilation
- **GitHub Actions** for cross-platform builds
- **Automated testing** with pytest

## 📍 File Locations

### Binary Installations
- **Templates**: Bundled in binary (self-contained)
- **Config**: `~/.giv/config` (user) or `.giv/config` (project)
- **Size**: ~15-25MB standalone executable

### PyPI Installation  
- **Binary**: Python environment bin directory
- **Templates**: `site-packages/giv/templates/`
- **Config**: Same as binary installations

See [Installation Locations](docs/installation-locations.md) for detailed information.

## 🤖 Supported AI Providers

### Local Models (Ollama)
```bash
giv config set api.url "http://localhost:11434/api/chat"
giv config set api.model "llama2"
```

### Remote APIs
```bash
# OpenAI
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4"

# Anthropic Claude
giv config set api.url "https://api.anthropic.com/v1/messages"
giv config set api.model "claude-3-5-sonnet-20241022"

# Custom endpoint
giv config set api.url "https://your-api.com/v1/chat/completions"
```

## 🐛 Troubleshooting

### Binary not found
```bash
# Check if installation directory is in PATH
echo $PATH

# Add to PATH (bash/zsh)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Template errors
```bash
# Initialize templates in project
giv init

# Check template access
giv message --dry-run
```

### Permission denied
```bash
# Make binary executable
chmod +x /path/to/giv

# Or install to user directory
mkdir -p ~/.local/bin
mv giv ~/.local/bin/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 🔗 Links

- [Installation Locations](docs/installation-locations.md) - Detailed file layout information  
- [Build System](docs/build-system-review.md) - Technical architecture overview
- [Publishing Guide](docs/how-to-publish.md) - Release process documentation
- [GitHub Releases](https://github.com/giv-cli/giv-py/releases) - Download binaries
- [Issue Tracker](https://github.com/giv-cli/giv-py/issues) - Report bugs

---

*Transform your Git history into professional documentation with the power of AI.*