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

## 🚀 Quick Install

### Direct Download (Recommended)
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

**Other Installation Methods:** [Package managers, PyPI, and more →](docs/installation.md)

## 🏁 Getting Started

```bash
# Initialize giv in your project
giv init

# Generate commit message for current changes
giv message

# Create changelog entry
giv changelog v1.0.0..HEAD

# Generate release notes
giv release-notes v1.2.0..HEAD
```

**Detailed Usage Guide:** [Command examples and advanced usage →](docs/app-spec.md)

## ⚙️ Basic Configuration

Set up your AI provider:

```bash
# Quick setup with environment variables (recommended)
export OPENAI_API_KEY="your-api-key"
export GIV_API_MODEL="gpt-4"

# Or configure via giv
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4"
```

**Complete Configuration Guide:** [All settings and providers →](docs/configuration.md)

## 🎨 Customization

```bash
# Initialize project templates
giv init

# Edit templates
nano .giv/templates/commit_message_prompt.md
nano .giv/templates/changelog_prompt.md

# Use custom template
giv message --prompt-file custom-prompt.md
```

**Template System:** [Customization and variables →](docs/app-spec.md#5-template-system)

## 📖 Documentation

- **[Installation Guide](docs/installation.md)** - All installation methods and troubleshooting
- **[Configuration](docs/configuration.md)** - Complete configuration reference
- **[App Specification](docs/app-spec.md)** - Commands, usage, and template system
- **[Build System](docs/build-system-review.md)** - Technical architecture
- **[Publishing Guide](docs/how-to-publish.md)** - Release process for contributors

## 🤖 Supported AI Providers

- **OpenAI** - GPT-4, GPT-3.5-turbo
- **Anthropic** - Claude 3.5 Sonnet, Claude 3 Opus
- **Local (Ollama)** - Llama 3.2, Code Llama, and more
- **Custom endpoints** - Any OpenAI-compatible API

**Provider Setup Examples:** [Configuration guide →](docs/configuration.md#configuration-examples)

## 🔧 Development

```bash
git clone https://github.com/giv-cli/giv-py.git
cd giv-py
poetry install
poetry run pytest
```

**Development Details:** [Build system and contributing →](docs/build-system-review.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Quick Links

- [📥 Releases](https://github.com/giv-cli/giv-py/releases) - Download binaries
- [🐛 Issues](https://github.com/giv-cli/giv-py/issues) - Report bugs
- [💬 Discussions](https://github.com/giv-cli/giv-py/discussions) - Community support
- [🗺️ Roadmap](docs/roadmap.md) - Planned features

---

*Transform your Git history into professional documentation with the power of AI.*