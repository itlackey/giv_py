# GitHub Copilot Instructions for giv CLI

## Project Overview
**giv** is an AI-powered Git history assistant that generates commit messages, changelogs, release notes, and announcements. This Python implementation provides cross-platform binaries with zero runtime dependencies.

## Architecture & Key Patterns

### Command System (`giv/commands/`)
All commands inherit from `BaseCommand` with consistent patterns:
- Use `argparse.Namespace` + `ConfigManager` in constructor
- Override `customize_context()` to modify template variables
- Override `handle_output()` to customize file writing behavior
- Commands auto-discover templates via `template_name` attribute

Example: `MessageCommand` uses `TEMPLATE_MESSAGE` = `"commit_message_prompt.md"`

### Configuration Hierarchy (`giv/config.py`)
Configuration follows Git-style precedence:
1. Project `.giv/config` 
2. User `~/.giv/config`
3. Environment variables with `GIV_` prefix (dot-notation: `api.key` → `GIV_API_KEY`)

Use `ConfigManager.get(key)` to access merged configuration.

### Template System (`giv/lib/templates.py`)
Templates discovered from multiple sources (project > user > system):
- Built-in templates in `giv/templates/*.md`
- Custom templates in `.giv/templates/` (project) or `~/.giv/templates/` (user)
- Variables use `{VARIABLE}` syntax, rendered with `TemplateEngine.render_template_file()`

### Git Integration (`giv/lib/git.py`)
`GitRepository` provides comprehensive Git operations:
- `get_diff(revision, pathspec, cached=False)` - unified diffs with context
- `build_history_metadata(revision)` - commit metadata for templates
- `get_commits(revision, pathspec)` - commit list for processing

### Testing Strategy
Use pytest markers for different test types:
```bash
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only  
poetry run pytest -m compatibility # Bash compatibility tests
```

## Development Commands

### Core Workflows
```bash
# Install dependencies and setup
poetry install

# Run comprehensive test suite
poetry run pytest

# Run specific test categories
poetry run pytest -m "unit and not slow"
poetry run pytest tests/test_commands_integration.py

# Build cross-platform binaries
poetry run build-binary

# Lint and format
poetry run black giv/ tests/
poetry run flake8 giv/ tests/
poetry run mypy giv/
```

### Binary Building (`build/`)
The build system creates standalone executables:
- `build/build_binary.py` - PyInstaller-based binary building
- Cross-platform CI via GitHub Actions workflows in `.github/workflows/`
- Package manager artifacts (Homebrew, Scoop, etc.) generated in `build/*/`

## Project-Specific Conventions

### Error Handling
Use custom exceptions from `giv.errors`:
- `TemplateError` for template issues → exit code 2
- `GitError` for Git problems → exit code 3  
- `ConfigError` for configuration issues → exit code 4
- `APIError` for LLM API failures → exit code 5

### LLM Integration (`giv/lib/llm.py`)
`LLMClient` supports multiple backends:
- OpenAI-compatible APIs (default)
- Local Ollama instances
- Custom endpoints via configuration

### Output Management (`giv/lib/output.py`)
`write_output()` supports multiple modes:
- `auto` - command-specific default behavior
- `append` - add to end of file
- `prepend` - add to beginning  
- `update` - replace specific sections
- `overwrite` - replace entire file

### Cross-Platform Considerations
Tests include platform-specific mocking for:
- Path resolution differences (macOS symbolic links)
- File encoding (Windows CP1252 vs UTF-8)
- Configuration path discovery (Windows vs Unix)

Use `unittest.mock.patch.object()` for reliable cross-platform testing.

## Common Integration Points

### Adding New Commands
1. Create `giv/commands/new_command.py` inheriting from `BaseCommand`
2. Register in `giv/commands/__init__.py` and `giv/cli.py`
3. Add template constant to `giv/constants.py`
4. Create template file in `giv/templates/`
5. Add comprehensive tests in `tests/test_commands_integration.py`

### Template Development
Templates support these context variables:
- `{DIFF}` - Git diff content
- `{VERSION}` - Project version from metadata
- `{COMMIT_ID}`, `{DATE}`, `{AUTHOR}` - Git commit metadata
- `{TODOS}` - TODO scan results (if enabled)

Use `TemplateEngine.validate_template()` to check token usage.
