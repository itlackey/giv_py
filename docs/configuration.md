# Configuration

`giv` uses a Git-style configuration system that stores settings in `.giv/config` files. Configuration can be managed through the `giv config` command, environment variables, or command-line arguments.

> **Note:** This configuration system works identically across all platforms with the compiled binary distribution.

## Getting Started

When you first run `giv`, it will prompt you to initialize configuration for your project:

```bash
# Interactive configuration setup
giv init
```

This will create a `.giv/config` file in your project root and prompt you for:
- Project name and description
- API URL (OpenAI, etc.)
- Model name
- Other project settings

## Configuration Management

Use the `giv config` command to manage settings:

```bash
# List all configuration values
giv config list

# Get a specific value
giv config get api.url
giv config api.url  # shorthand syntax

# Set a configuration value
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config api.url "https://api.openai.com/v1/chat/completions"  # shorthand

# Remove a configuration value
giv config unset api.url
```

## Configuration Keys

The following configuration keys are available:

| Key                  | Purpose                                             | Example Value                                 |
|----------------------|-----------------------------------------------------|-----------------------------------------------|
| `api.url`            | API endpoint URL                                    | `https://api.openai.com/v1/chat/completions` |
| `api.model`          | AI model name                                       | `gpt-4o-mini`, `llama3.2`, `claude-3-sonnet` |
| `api.key`            | API key (use environment variables)                | `OPENAI_API_KEY` (env var name)               |
| `project.title`      | Project name                                        | `My Awesome Project`                          |
| `project.description`| Project description                                 | `A CLI tool for managing projects`           |
| `project.url`        | Project URL                                         | `https://github.com/user/project`            |
| `project.type`       | Project type (auto-detected)                       | `node`, `python`, `rust`, `custom`           |
| `version.file`       | File containing version information                 | `package.json`, `pyproject.toml`             |
| `version.pattern`    | Regex pattern to extract version                   | `"version":\s*"([^"]+)"`                     |
| `output.mode`        | Default output mode                                 | `auto`, `append`, `prepend`, `overwrite`     |
| `changelog.file`     | Changelog file path                                 | `CHANGELOG.md`                                |
| `temperature`        | AI model temperature (0.0-1.0)                     | `0.7`                                         |
| `max_tokens`         | Maximum tokens for AI response                      | `8192`                                        |

## Environment Variables

Configuration values are stored as `GIV_*` environment variables and can be overridden:

| Variable              | Purpose                                             | Configuration Key     |
|-----------------------|-----------------------------------------------------|-----------------------|
| `GIV_API_KEY`         | API key for remote AI services                     | `api.key`            |
| `GIV_API_URL`         | API endpoint URL                                    | `api.url`            |
| `GIV_API_MODEL`       | AI model name                                       | `api.model`          |
| `GIV_PROJECT_TITLE`   | Project name                                        | `project.title`      |
| `GIV_PROJECT_DESCRIPTION` | Project description                             | `project.description`|
| `GIV_PROJECT_URL`     | Project URL                                         | `project.url`        |
| `GIV_PROJECT_TYPE`    | Project type                                        | `project.type`       |
| `GIV_VERSION_FILE`    | Version file path                                   | `version.file`       |
| `GIV_VERSION_PATTERN` | Version extraction pattern                          | `version.pattern`    |
| `GIV_OUTPUT_MODE`     | Default output mode                                 | `output.mode`        |
| `GIV_CHANGELOG_FILE`  | Changelog file path                                 | `changelog.file`     |
| `GIV_CONFIG_FILE`     | Path to configuration file                          | N/A                  |

**Preferred API Key Variables**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GIV_API_KEY`

You can also use a `.env` file in your project root to set these variables. The configuration hierarchy is:
1. Command-line arguments (highest priority)
2. Environment variables  
3. `.giv/config` file
4. Default values (lowest priority)

## Using a Custom Configuration File

You can specify a custom config file with the `--config-file` option:

```sh
giv --config-file ./myconfig.env changelog
```

The custom config file should use environment variable format:

```env
GIV_API_KEY=your_api_key_here
GIV_API_URL=https://api.openai.com/v1/chat/completions
GIV_API_MODEL=gpt-4o-mini
```

## Configuration Examples

### OpenAI Setup
```bash
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4o-mini"
# Set API key via environment variable
export OPENAI_API_KEY="your_openai_api_key_here"
```

### Anthropic Claude Setup
```bash
giv config set api.url "https://api.anthropic.com/v1/messages"
giv config set api.model "claude-3-5-sonnet-20241022"
# Set API key via environment variable
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

### Groq Setup
```bash
giv config set api.url "https://api.groq.com/openai/v1/chat/completions"
giv config set api.model "llama3-70b-8192"
# Set API key via environment variable
export GROQ_API_KEY="your_groq_api_key_here"
```

### Local Ollama Setup
```bash
giv config set api.url "http://localhost:11434/v1/chat/completions"
giv config set api.model "llama3.2"
# No API key needed for localhost
```

### Cross-Platform Configuration

The compiled binary handles configuration identically on all platforms:
- **Linux/macOS**: Configuration stored in `.giv/config` (same format)
- **Windows**: Configuration stored in `.giv/config` (same format)
- **All platforms**: Same environment variable names and precedence

You can also create a `.env` file in your project root for environment-specific settings.

## Command-Line Overrides

Configuration values can be overridden by command-line flags:

- `--api-model` overrides `api.model` configuration
- `--api-url` overrides `api.url` configuration  
- `--api-key` overrides `api.key` configuration
- `--config-file` specifies an alternative configuration file

Examples:
```bash
# Override API model for one command
giv changelog --api-model gpt-4o

# Use different configuration file
giv summary --config-file ./prod.env
```

## Project Detection and Metadata

`giv` automatically detects your project type and sets appropriate defaults:

- **Node.js**: Detects `package.json`, sets version file and pattern
- **Python**: Detects `setup.py`, `pyproject.toml`, sets appropriate patterns  
- **Rust**: Detects `Cargo.toml`, sets version extraction pattern
- **PHP**: Detects `composer.json`, sets appropriate configuration
- **Gradle**: Detects `build.gradle`, sets version extraction pattern
- **Maven**: Detects `pom.xml`, sets version extraction pattern
- **Custom**: Allows manual configuration of version files and patterns

You can override auto-detection:
```bash
giv config set project.type "custom"
giv config set version.file "VERSION.txt"  
giv config set version.pattern "([0-9]+\.[0-9]+\.[0-9]+)"
```

## Prompt Templates

- By default, `giv` uses built-in prompt templates for each subcommand
- You can provide custom templates with `--prompt-file ./my_template.md`
- Templates support token replacement like `[PROJECT_TITLE]`, `[VERSION]`, etc.
- See `templates/` directory for examples

## Tips

- Use `giv config` without arguments for interactive setup of a new project
- Configuration values are normalized: `api.key` becomes `GIV_API_KEY` environment variable
- For remote API usage, you **must** set a valid `api.key` and `api.url`
- Use `giv config list` to see your current configuration
- Configuration files use shell variable format and support quotes for values with spaces
- The `.giv` directory is automatically created in your project root (similar to `.git`)

> See the [README](../README.md) and [Installation](./installation.md) for more details and examples.