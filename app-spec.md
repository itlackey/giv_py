# Giv CLI Application Specification

## 1. Application Overview

**Giv** is an AI-powered command-line interface tool that generates polished commit messages, changelogs, release notes, summaries, and announcements from Git repository history. The application transforms raw Git diffs and metadata into professionally formatted content using large language models.

### 1.1 Purpose
- Generate AI-assisted Git commit messages from working tree or staged changes
- Create technical summaries of project changes and updates
- Maintain structured changelog files following industry standards
- Generate professional release notes for version releases
- Create marketing-style announcements for public communication
- Support custom content generation through user-defined templates

### 1.2 Target Users
- Software developers managing Git repositories
- Project maintainers creating release documentation
- Teams requiring consistent documentation standards
- Organizations needing automated content generation for releases

## 2. Command Structure and Interface

### 2.1 Basic Command Pattern
```
giv [global-options] <command> [command-options] [revision] [pathspec...]
```

### 2.2 Global Options (must appear before subcommand)
| Option | Description | Default |
|--------|-------------|---------|
| `--config-file <file>` | Configuration file to load | `.giv/config` |
| `--verbose` | Enable detailed logging output | false |
| `--dry-run` | Preview mode - no file writes or API calls | false |

### 2.3 Document Related Command Options (must appear after revision or pathspec)
| Option | Description | Default |
|--------|-------------|---------|
| `--api-url <url>` | Remote API endpoint URL | None |
| `--api-key <key>` | API authentication key (prefer environment variables) | None |
| `--api-model <model>` | LLM model name | "default" |
| `--model <model>` | Alias for --api-model | "default" |
| `--output-mode <mode>` | Output mode: auto/prepend/append/update/overwrite/none | auto |
| `--output-file <file>` | Write output to file instead of stdout | None |
| `--output-version <version>` | Version string for versioned content | Auto-detected |
| `--prompt-file <file>` | Custom prompt template file, required for document subcommand | None |
| `--todo-files <pathspec>` | Files to scan for TODO items | `**/*` |
| `--todo-pattern <regex>` | Regex pattern for TODO matching | `TODO\|FIXME\|XXX` |
| `--version-file <pathspec>` | Files to inspect for version information | Project-specific |
| `--version-pattern <regex>` | Regex pattern for version extraction | SemVer default |

## 3. Subcommands

### 3.1 Message Command (Default)
**Usage**: `giv [global options] [message] [revision] [pathspec...] [command options]`

**Purpose**: Generate commit messages from Git diffs

**Behavior**:
- Analyzes Git working tree changes by default
- Supports revision ranges and pathspecs for targeted analysis
- Uses structured commit message format with clear, descriptive language
- Integrates TODO scanning and file change analysis

**Special Revisions**:
- `--current` (default): Working tree changes
- `--cached`: Staged changes only
- Git revision syntax: `HEAD~3..HEAD`, `v1.0.0..HEAD`, etc.

**Output**: 
- Formatted commit message suitable for `git commit -m`
- Includes summary line and detailed description
- References specific files and changes when relevant

### 3.2 Summary Command
**Usage**: `giv [options] summary [revision] [pathspec...] [command options]`

**Purpose**: Create comprehensive technical summaries of changes

**Behavior**:
- Generates detailed technical documentation of changes
- Suitable for project updates, documentation, and reports
- Includes analysis of code changes, new features, and modifications

**Output**:
- Technical summary in Markdown format
- Structured sections covering different aspects of changes
- Professional tone suitable for technical documentation

### 3.3 Changelog Command
**Usage**: `giv [options] changelog [revision] [pathspec...] [command options]`

**Purpose**: Generate or update changelog files following Keep a Changelog standard

**Behavior**:
- Automatically detects project version from metadata files
- Updates existing changelog sections or creates new entries
- Follows conventional changelog structure (Added, Changed, Fixed, etc.)
- Default output mode is `auto` to replace version sections or prepend a new section them if they do not
- Supports [Unreleased] section for changes not associated with a release

**Default Output File**: `CHANGELOG.md`

**Output Format**:
```markdown
## [1.2.0] - 2024-01-15

### Added
- New feature descriptions

### Changed
- Modification descriptions

### Fixed
- Bug fix descriptions
```

### 3.4 Release Notes Command
**Usage**: `giv [options] release-notes [revision] [pathspec...] [command options]`

**Purpose**: Generate professional release notes for tagged releases

**Behavior**:
- Creates formal release documentation
- Integrates with Git tags for version information
- Professional tone suitable for public release announcements
- Default output mode is `overwrite` to replace entire file

**Default Output File**: `RELEASE_NOTES_{VERSION}.md`

**Output**: Professional release notes with version highlights and changes

### 3.5 Announcement Command
**Usage**: `giv [options] announcement [revision] [pathspec...] [command options]`

**Purpose**: Create marketing-style announcements and public communications

**Behavior**:
- Generates user-friendly, engaging content
- Focuses on user benefits and exciting features
- Suitable for blog posts, social media, and public announcements
- Marketing-oriented language and structure

**Default Output File**: `ANNOUNCEMENT_{VERSION}.md`

**Output**: Engaging announcement content with marketing focus

### 3.6 Document Command
**Usage**: `giv [options] document [revision] [pathspec...] --prompt-file <template> [command options]`

**Purpose**: Generate custom content using user-provided templates

**Requirements**:
- `--prompt-file` parameter is mandatory
- Template file must exist and be readable

**Behavior**:
- Uses custom prompt templates for specialized content generation
- Supports all template variables and substitution
- Flexible content generation for unique requirements

### 3.7 Config Command
**Usage**: `giv config <operation> [key] [value]`
- CLI options/args matches `git config` for configuration operations

**Operations**:
- `list`: Display all configuration values
- `get <key>`: Retrieve specific configuration value
- `set <key> <value>`: Set configuration value
- `unset <key>`: Remove configuration value

**Configuration Keys** (dot notation):
- `api.url`: API endpoint URL
- `api.key`: API authentication key (environment variables preferred)  
- `api.model`: Default model name
- `temperature`: LLM temperature setting (0.0-2.0)
- `max_tokens`: Maximum response tokens
- `timeout`: API request timeout (seconds)
- `output.mode`: Default output mode
- `project.title`: Project title override
- `changelog.file`: Changelog filename
- `todo.file`: Pathspec to search for TODO items
- `todo.pattern`: RegEx pattern to locate TODO items
- Also supports version file and pattern

### 3.8 Init Command
**Usage**: `giv init`

**Purpose**: Initialize giv configuration and templates in project

**Behavior**:
- Creates `.giv/` directory structure
- Copies default templates to project
- Prompts for basic configuration values
- Sets up project-local configuration

### 3.9 Utility Commands
- `giv version`: Display version information
- `giv help [command]`: Show help information
- `giv available-releases`: List available releases
- `giv update [version]`: Self-update to latest or specific version

## 4. Configuration System

### 4.1 Configuration Hierarchy (precedence from highest to lowest)
1. **Command-line arguments**: Override all other settings
2. **Project configuration**: `.giv/config` in project root
3. **User configuration**: `~/.giv/config` in home directory  
4. **Environment variables**: `GIV_*` prefixed (e.g., `GIV_API_KEY`)
5. **Built-in defaults**: Application defaults

### 4.2 Configuration File Format
```ini
# Key-value pairs with dot notation
api.url=https://api.openai.com/v1/chat/completions
api.model=gpt-4
api.key="ENV varibale key" # This sets what ENV var to use, DO NOT store keys in config
output.mode=auto
temperature=0.8
max_tokens=8192
project.title="My Project"
changelog.file=CHANGELOG.md
```

### 4.3 Environment Variable Mapping
- Configuration keys convert to uppercase with `GIV_` prefix
- Dots become underscores: `api.key` → `GIV_API_KEY`
- Supports quoted values for special characters
- **Preferred API key variables**: `OPENAI_API_KEY`, `GIV_API_KEY`
- **Security**: API keys should only be provided via environment variables, not stored in configuration files

## 5. Template System

### 5.1 Template Hierarchy (precedence from highest to lowest)
1. **Custom template**: Specified via `--prompt-file`
2. **Project templates**: `.giv/templates/` directory
3. **System templates**: Bundled with application

### 5.2 Built-in Templates
- `message_prompt.md`: Commit message generation
- `final_summary_prompt.md`: Technical summaries
- `changelog_prompt.md`: Changelog entries
- `release_notes_prompt.md`: Release documentation
- `announcement_prompt.md`: Marketing announcements

### 5.3 Template Variables
Templates support variable substitution with `{VARIABLE}` syntax:

| Variable | Description | Example |
|----------|-------------|---------|
| `{SUMMARY}` | LLM generated summary of Git diff content | Produced for each commit |
| `{HISTORY}` |Git diff content | Unified diff output |
| `{PROJECT_TITLE}` | Project name | "My Application" |
| `{VERSION}` | Version string | "1.2.0" |
| `{OUTPUT_VERSION}` | Specified output version | "1.2.0" |
| `{COMMIT_ID}` | Full commit hash | "a1b2c3d4..." |
| `{SHORT_COMMIT_ID}` | Abbreviated hash | "a1b2c3d" |
| `{DATE}` | Commit or current date | "2024-01-15" |
| `{MESSAGE}` | Commit message | "Fix authentication bug" |
| `{BRANCH}` | Current Git branch | "main" |
| `{REVISION}` | Specified revision | "HEAD~3..HEAD" |

## 6. Git Integration

### 6.1 Revision Support
- **Full Git syntax**: Supports all gitrevisions formats
- **Revision ranges**: `v1.0.0..HEAD`, `HEAD~3..HEAD`, `branch1..branch2`
- **Special revisions**:
  - `--current`: Working tree changes (default)
  - `--cached`: Staged changes only
- **Path specifications**: Limit analysis to specific files/directories

### 6.2 Repository Analysis
- **Diff extraction**: Generates unified diffs for AI analysis
- **Metadata collection**: Commit hashes, dates, messages, authors
- **Branch detection**: Current branch identification
- **Status checking**: Working tree and index status
- **Untracked files**: Includes new files in analysis

### 6.3 Project Metadata Detection
Automatically detects project information from:

| Project Type | Files | Metadata Extracted |
|--------------|-------|-------------------|
| Node.js | `package.json` | name, version, description |
| Python | `pyproject.toml`, `setup.py` | name, version, description |
| Rust | `Cargo.toml` | name, version, description |
| Go | `go.mod` | module name, version |
| PHP | `composer.json` | name, version, description |
| Java | `pom.xml`, `build.gradle` | name, version, description |
| Generic | `VERSION`, `version.txt` | version string |
| Git | Tags, commit history | version tags |

**Version Format Support**:
- Semantic versioning (1.2.3)
- Version prefixes (v1.2.3, V1.2.3)
- Pre-release suffixes (1.2.3-beta, 1.2.3-alpha.1)
- **Conflict Resolution**: Determined by project type setting; prompts user if project type unset

## 7. Output Management

### 7.1 Output Modes
- **`auto`**: Intelligent mode selection:
  - Changelog command: `update` or `prepend` if the section is missing
  - Release notes command: `overwrite`
  - Other commands: `none` (stdout)
- **`prepend`**: Add content to beginning of file
- **`append`**: Add content to end of file
- **`update`**: Replace existing version sections in file
- **`overwrite`**: Replace entire file content
- **`none`**: Output to stdout only

### 7.2 File Handling
- **Section management**: Version-aware updates for structured files
- **Format preservation**: Maintains existing file structure and formatting
- **Encoding**: UTF-8 encoding throughout application

## 8. AI Provider Support

### 8.1 Supported API Types
- **OpenAI**: GPT-3.5, GPT-4, GPT-4o series models
- **Anthropic**: Claude 3.5 Sonnet and other Claude models  
- **Local models**: Ollama and other OpenAI-compatible endpoints
- **Custom APIs**: Any service implementing OpenAI ChatCompletion format

### 8.2 API Configuration Examples
```bash
# OpenAI Configuration
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4"
giv config set api.key "sk-..."

# Anthropic Configuration  
giv config set api.url "https://api.anthropic.com/v1/messages"
giv config set api.model "claude-3-5-sonnet-20241022"
giv config set api.key "sk-ant-..."

# Local Ollama Configuration
giv config set api.url "http://localhost:11434/v1/chat/completions"
giv config set api.model "llama3.2"
# No API key needed for localhost
```

### 8.3 Model Parameters
- **Temperature**: Controls creativity/randomness (0.0-2.0)
  - Creative commands (message, summary): 0.9 default
  - Factual commands (changelog, release-notes): 0.7 default
- **Max tokens**: Response length limit (default: 8192)
- **Timeout**: Request timeout in seconds (default: 60)
- **Retries**: Automatic retry attempts on failure (default: 3, then exit)

## 9. Advanced Features

### 9.1 TODO Scanning
- **Pattern matching**: Custom regex via `--todo-pattern`
- **File filtering**: Specific files via `--todo-files`
- **Integration**: TODO items included in generated content
- **Default patterns**: Matches `TODO`, `FIXME`, `XXX` comments

### 9.2 Version Management
- **Automatic detection**: Extracts versions from project files
- **SemVer support**: Semantic versioning parsing and validation
- **Custom patterns**: User-defined version regex patterns
- **Manual override**: Explicit version specification via `--output-version`

### 9.3 Dry Run Mode
- **Preview generation**: Shows what would be generated without execution
- **No API calls**: Skips actual LLM requests, uses prompt as output
- **Output simulation**: Displays where content would be written
- **Configuration testing**: Validates settings without side effects

## 10. Error Handling and Validation

### 10.1 Comprehensive Error Management
- **Configuration validation**: Detects invalid or missing settings
- **Git repository validation**: Ensures valid Git repository context  
- **API error handling**: 3 retry attempts for LLM requests, then exit on failure
- **Template validation**: Verifies template file existence and readability
- **File permission checking**: Validates write permissions before modification
- **Binary/large file exclusion**: Automatically excludes binary and large files from processing
- **Submodule limitation**: Does not support Git submodules (graceful handling)

### 10.2 User Experience
- **Clear error messages**: Specific problem identification with context
- **Actionable suggestions**: Concrete steps to resolve issues
- **Graceful degradation**: Fallback behaviors when possible
- **State preservation**: Maintains user work without data loss
- **UTF-8 encoding**: Default character encoding throughout application
- **Basic Markdown**: Supports standard Markdown formatting without extensions

## 11. Installation and Distribution

### 11.1 Installation Methods
1. **Binary distribution**: Self-contained executables (~15MB)
   - Linux (x86_64, ARM64)
   - macOS (Intel, Apple Silicon)  
   - Windows (x86_64)
2. **Package managers**: Homebrew, Scoop, apt, yum
3. **PyPI installation**: `pip install giv` (requires Python 3.8.1+)

### 11.2 File System Layout
- **User configuration**: `~/.giv/config`
- **Project configuration**: `.giv/config` 
- **Project templates**: `.giv/templates/`
- **System templates**: Bundled in binary or Python package

### 11.3 Self-Update System
- **Update command**: `giv update [version]` for in-place updates
- **Version checking**: `giv available-releases` lists available versions
- **Binary replacement**: Downloads and replaces current executable

## 12. Business Rules and Requirements

### 12.1 Content Generation Rules
1. **Commit messages** must be clear, concise, and follow conventional format
2. **Changelogs** must follow Keep a Changelog standard with proper versioning
3. **Release notes** must maintain professional tone suitable for public consumption
4. **Announcements** must emphasize user benefits and engaging language
5. **All content** must be factually accurate based on actual code changes

### 12.2 Git Integration Requirements
1. **Must operate in valid Git repositories** or provide clear error messages
2. **Must support all standard Git revision syntax** without exceptions
3. **Must handle empty repositories and initial commits** gracefully
4. **Must respect Git ignore patterns** for file analysis
5. **Must preserve Git repository state** without unintended modifications

### 12.3 Configuration Requirements
1. **Must support hierarchical configuration** with clear precedence rules
2. **Must validate configuration values** before use
3. **Must provide clear feedback** for configuration errors
4. **Must support environment variable override** for CI/CD integration
5. **Must maintain backward compatibility** for configuration formats

### 12.4 API Integration Requirements
1. **Must support multiple AI providers** without vendor lock-in
2. **Must handle API failures gracefully** with exactly 3 retry attempts
3. **Must respect API rate limits** and provide appropriate backoff
4. **Must validate API responses** before processing
5. **Must support both authenticated and local APIs** seamlessly
6. **Must use 60-second timeout** for LLM requests unless explicitly configured
7. **Must prioritize environment variables** for API key authentication

### 12.5 File Operation Requirements
1. **Must create backups** before modifying existing files
2. **Must preserve file permissions** and ownership
3. **Must handle concurrent access** safely
4. **Must validate write permissions** before attempting operations
5. **Must support atomic file operations** to prevent corruption
6. **Must exclude binary and large files** from diff processing
7. **Must use UTF-8 encoding** for all file operations

### 12.6 Caching and Performance Requirements
1. **Must cache generated commit summaries** until explicitly cleared
2. **Must support chunking for large repositories** (future version)
3. **Must handle project type conflicts** by prompting user when unset
4. **Must support CI/CD integration** through environment variables
5. **Must manage team configuration** via `.giv/config` files in repositories

## 13. Security and Extensibility

### 13.1 Authentication and Security
- **API Key Management**: API keys must only be provided via environment variables (`OPENAI_API_KEY`, `GIV_API_KEY`)
- **No Credential Storage**: Application does not store or cache API credentials
- **No Session Authentication**: Enterprise session-based authentication is not supported
- **UTF-8 Encoding**: All file operations and content generation uses UTF-8 encoding

### 13.2 Extensibility and Integration
- **Template System**: Simple variable substitution only, no conditional logic or loops
- **Custom AI Providers**: All LLM integration handled through standard API configuration
- **CI/CD Integration**: Environment variable support enables seamless CI/CD pipeline integration
- **Team Configuration**: Managed through `.giv/config` files committed to repositories
- **Contribution Model**: New commands and features contributed via pull requests
- **Git Hooks**: Tool designed for easy integration with Git hooks and workflows

### 13.3 Limitations and Future Features
- **Submodules**: Git submodules are not currently supported
- **Internationalization**: Officially supports English only (user customizable via templates)
- **Date Formatting**: No locale-specific date formatting
- **Audit Logging**: May be considered for future enterprise releases
- **Repository Chunking**: Large repository support via commit chunking planned for future versions
- **Manual Review**: Interactive review features may be added in future releases

### 13.4 Performance and Caching
- **Commit Summary Caching**: Generated summaries cached until user manually clears cache
- **Binary File Exclusion**: Binary and large files automatically excluded from processing
- **Timeout Management**: 60-second default timeout for LLM requests
- **Failure Handling**: Exactly 3 retry attempts before application exit

This specification provides a complete foundation for building the giv CLI application, incorporating all clarifications and addressing previously pending questions. The application is designed as a focused, reliable tool for AI-assisted Git workflow enhancement with clear boundaries and well-defined extensibility patterns.