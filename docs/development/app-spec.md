# Giv CLI Application Specification

Sections 2,3,5,7,9,12 need corrections

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

### 1.3 Repository Requirements
**Giv requires execution from within a Git repository and automatically operates from the repository root directory:**

- **Git Repository Required**: The application must be executed from within a Git repository or one of its subdirectories
- **Automatic Root Discovery**: On startup, the application automatically detects the Git repository root using `git rev-parse --show-toplevel`
- **Working Directory Change**: The application changes to the repository root directory for all operations
- **Exit on Invalid Repository**: If not executed from within a Git repository, the application exits with an error message

This design ensures:
- Consistent behavior regardless of execution location within the repository
- Proper relative path resolution for configuration files (`.giv/config`, `.giv/templates/`)
- Accurate project metadata detection from root-level files (`package.json`, `pyproject.toml`, etc.)
- Reliable Git operations across the entire repository

## 2. Command Structure and Interface

### 2.1 Basic Command Pattern
```
giv [global-options] <command> [revision] [pathspec...] [command-options] 
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
| `--api-model <model>` | LLM model name | `"default"` |
| `--model <model>` | Alias for --api-model | `"default"` |
| `--output-mode <mode>` | Output mode: auto/prepend/append/update/overwrite/none | `auto` |
| `--output-file <file>` | Write output to file instead of stdout | None |
| `--prompt-file <file>` | Custom prompt template file, required for document subcommand | None |
| `--todo-files <pathspec>` | Files to scan for TODO items | `**/*` |
| `--todo-pattern <regex>` | Regex pattern for TODO matching | `TODO\|FIXME\|XXX` |
| `--version-file <pathspec>` | Files to inspect for version information | Project-specific |
| `--version-pattern <regex>` | Regex pattern for version extraction | SemVer default |
| `--version <version>` | Version string for versioned content, defaults to auto-detected | `auto` |

## 3. Usage Examples

### 3.1 Basic Commands
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

### 3.2 Advanced Usage
```bash
# Filter by file patterns
giv message HEAD~1..HEAD src/ docs/

# Scan for TODOs in specific files
giv changelog --todo-files '*.py' --todo-pattern 'TODO|FIXME|XXX'

# Use custom templates
giv message --prompt-file my-template.md

# Different output modes
giv changelog --output-mode append    # Add to end
giv changelog --output-mode prepend   # Add to beginning  
giv changelog --output-mode update    # Replace existing section
```

### 3.3 Configuration Management
```bash
# List all configuration
giv config list

# Set API configuration
giv config set api.url "https://api.openai.com/v1/chat/completions"
giv config set api.model "gpt-4"

# Set project metadata
giv config set project.title "My Project"
giv config set output.mode "auto"

# Remove configuration
giv config unset old.setting
```

### 3.4 Template Customization
```bash
# Initialize project templates (copies defaults to .giv/templates/)
giv init

# Edit templates
nano .giv/templates/commit_message_prompt.md
nano .giv/templates/changelog_prompt.md

# Use custom template for one command
giv message --prompt-file custom-prompt.md
```

## 4. Subcommands

### 4.1 Message Command (Default)
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
  - Revisions other than `--current` and `--cached` will return existing commit message

**Output**: 
- Formatted commit message suitable for `git commit -m`
- Includes summary line and detailed description
- References specific files and changes when relevant

### 4.2 Summary Command
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

### 4.3 Changelog Command
**Usage**: `giv [options] changelog [revision] [pathspec...] [command options]`

**Purpose**: Generate or update changelog files following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standard

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

### 4.4 Release Notes Command
**Usage**: `giv [options] release-notes [revision] [pathspec...] [command options]`

**Purpose**: Generate professional release notes for tagged releases

**Behavior**:
- Creates formal release documentation
- Integrates with Git tags for version information
- Professional tone suitable for public release announcements
- Default output mode is `overwrite` to replace entire file if it exists

**Default Output File**: `{VERSION}_release_notes.md`

**Output**: Professional release notes with version highlights and changes

### 4.5 Announcement Command
**Usage**: `giv [options] announcement [revision] [pathspec...] [command options]`

**Purpose**: Create marketing-style announcements and public communications

**Behavior**:
- Generates user-friendly, engaging content
- Focuses on user benefits and exciting features
- Suitable for blog posts, social media, and public announcements
- Marketing-oriented language and structure

**Default Output File**: `{VERSION}_announcement.md`

**Output**: Engaging announcement content with marketing focus

### 4.6 Document Command
**Usage**: `giv [options] document [revision] [pathspec...] --prompt-file <template> [command options]`

**Purpose**: Generate custom content using user-provided templates

**Requirements**:
- `--prompt-file` parameter is mandatory
- Template file must exist and be readable

**Behavior**:
- Uses custom prompt templates for specialized content generation
- Supports all template variables and substitution
- Flexible content generation for unique requirements

**Default Output File**: `{VERSION}_document.md`

### 4.7 Config Command
**Usage**: `giv config <operation> [key] [value]`
- CLI options/args matches `git config` for configuration operations

**Operations**:
- `list`: Display all configuration values
- `get <key>`: Retrieve specific configuration value
- `set <key> <value>`: Set configuration value
- `unset <key>`: Remove configuration value
- If no operation is provided, defaults to `list`

**Configuration Keys** (dot notation):
- `api.url`: API endpoint URL
- `api.key`: API authentication key (environment variables preferred)  
- `api.model.name`: Default model name
- `api.model.temperature`: LLM temperature setting (0.0-2.0)
- `api.model.max_tokens`: Maximum response tokens
- `api.model.timeout`: API request timeout (seconds)
- `project.title`: Project title override
- `project.description`: Project description
- `project.url`: Project URL
- `project.type`: Project type (auto-detected: node, python, rust, custom)
- `todo.file`: Pathspec to search for TODO items
- `todo.pattern`: RegEx pattern to locate TODO items
- `todo.label.[key]`: Description to replace key with (fix = "Bug Fixed", add = "New Feature Added")
- `version.file`: Pathspec to inspect for version information (alias for version.file)
- `version.pattern`: Regex pattern for version extraction (alias for version.pattern)
- `output.mode`: Default output mode
- `changelog.file`: Changelog file path

### 4.8 Init Command
**Usage**: `giv init`

**Purpose**: Initialize giv configuration and templates in project

**Behavior**:
- Creates `.giv/` directory structure
- Copies default templates to project
- Prompts for basic configuration values
- Sets up project-local configuration

### 4.9 Utility Commands
- `giv version`: Display version information
- `giv help [command]`: Show help information
- `giv available-releases`: List available releases
- `giv update [version]`: Self-update to latest or specific version

## 5. Configuration System

### 5.1 Configuration Hierarchy (precedence from highest to lowest)
1. **Command-line arguments**: Override all other settings
2. **Project configuration**: `.giv/config` in project root
3. **User configuration**: `~/.giv/config` in home directory  
4. **Environment variables**: `GIV_*` prefixed (e.g., `GIV_API_KEY`)
5. **Built-in defaults**: Application defaults

### 5.2 Configuration File Format
```ini
# Key-value pairs with dot notation
api.url=https://api.openai.com/v1/chat/completions
api.key="ENV varibale key" # This sets what ENV var to use, DO NOT store keys in config
api.model.name=gpt-4
api.model.temperature=0.8
api.model.max_tokens=8192
project.title="My Project"
changelog.file=CHANGELOG.md
output.mode=auto
```

### 5.3 Environment Variable Mapping
- Configuration keys convert to uppercase with `GIV_` prefix
- Dots become underscores: `api.key` → `GIV_API_KEY`
- Supports quoted values for special characters
- **Preferred API key variables**: `OPENAI_API_KEY`, `GIV_API_KEY`
- **Security**: API keys should only be provided via environment variables, not stored in configuration files

## 6. Template System

### 6.1 Template Hierarchy (precedence from highest to lowest)
1. **Custom template**: Specified via `--prompt-file`
2. **Project templates**: `.giv/templates/` directory
3. **System templates**: Bundled with application

### 6.2 Built-in Templates
- `commit_message_prompt.md`: Commit message generation
- `commit_summary_prompt.md`: Commit summary generation
- `summary_prompt.md`: Technical summaries
- `changelog_prompt.md`: Changelog entries
- `release_notes_prompt.md`: Release documentation
- `announcement_prompt.md`: Marketing announcements

### 6.3 Template Variables
Templates support variable substitution with `[VARIABLE]` syntax:

| Variable | Description | Example |
|----------|-------------|---------|
| `[HISTORY]` |Git diff content | Unified diff output used in commit message and commit summary |
| `[SUMMARY]` | LLM generated summary of Git diff content | Produced for given revision |
| `[PROJECT_TITLE]` | Project name | "My Application" |
| `[VERSION]` | Version string | "1.2.0" |
| `[COMMIT_ID]` | Full commit hash | "a1b2c3d4..." |
| `[SHORT_COMMIT_ID]` | Abbreviated hash | "a1b2c3d" |
| `[BRANCH]` | Current Git branch | "main" |
| `[DATE]` | Commit or current date | "2024-01-15" |
| `[MESSAGE]` | Commit message | "Fix authentication bug" |
| `[AUTHOR]`   | Git user name for the commit |

## 7. Git Integration

### 7.1 Repository Requirements and Initialization
- **Repository Detection**: Application uses `git rev-parse --show-toplevel` to find repository root
- **Automatic Root Navigation**: Changes working directory to repository root on startup
- **Repository Validation**: Exits with error if not executed from within a Git repository
- **Consistent Operation**: All file paths and operations are relative to repository root

### 7.2 Revision Support
- **Full Git syntax**: Supports all gitrevisions formats
- **Revision ranges**: `v1.0.0..HEAD`, `HEAD~3..HEAD`, `branch1..branch2`
- **Special revisions**:
  - `--current`: Working tree changes (default)
  - `--cached`: Staged changes only
- **Path specifications**: Limit analysis to specific files/directories

### 7.3 Repository Analysis
- **Diff extraction**: Generates unified diffs for AI analysis
- **Metadata collection**: Commit hashes, dates, messages, authors
- **Branch detection**: Current branch identification
- **Status checking**: Working tree and index status
- **Untracked files**: Includes new files in analysis

### 7.4 Project Metadata Detection
Automatically detects project information from:

| Project Type | Files | Metadata Extracted |
|--------------|-------|-------------------|
| Node.js | `package.json` | name, version, description |
| Python | `pyproject.toml`, `setup.py` | name, version, description |
| Rust | `Cargo.toml` | name, version, description |
| Go | `go.mod` | module name, version |
| PHP | `composer.json` | name, version, description |
| Java | `pom.xml`, `build.gradle` | name, version, description |
| Giv | `.giv/config` | name, version, description |
| Git | Tags, commit history | version tags |
| Custom | `--version-file` & `--version-pattern` | version

**Version Format Support**:
- Semantic versioning (1.2.3)
- Version prefixes (v1.2.3, V1.2.3)
- Pre-release suffixes (1.2.3-beta, 1.2.3-alpha.1)
- **Conflict Resolution**: Determined by project type setting; prompts user if project type unset

## 8. Output Management

### 8.1 Output Modes
- **`auto`**: Intelligent mode selection:
  - Changelog command: `update` or `prepend` if the section is missing
  - Release notes command: `overwrite`
  - Announcement command: `overwrite`
  - Other commands: `none` (stdout)
- **`prepend`**: Add content to beginning of file
- **`append`**: Add content to end of file
- **`update`**: Replace existing version sections in file
- **`overwrite`**: Replace entire file content
- **`none`**: Output to stdout only

### 8.2 File Handling
- **Section management**: Version-aware updates for structured files
- **Format preservation**: Maintains existing file structure and formatting
- **Encoding**: UTF-8 encoding throughout application
- **Output Linting**: All output should pass basic markdown linting

## 9. AI Provider Support

### 9.1 Supported API Types
- **OpenAI**
- **Anthropic**  
- **Local models**: Ollama and other OpenAI-compatible endpoints
- **Custom APIs**: Any service implementing OpenAI ChatCompletion format

### 9.2 API Configuration Examples
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

### 9.3 Model Parameters
- **Temperature**: Controls creativity/randomness (0.0-2.0)
  - Creative commands (message, summary): 0.9 default
  - Factual commands (changelog, release-notes): 0.7 default
- **Max tokens**: Response length limit (default: 8192)
- **Timeout**: Request timeout in seconds (default: 60)
- **Retries**: Automatic retry attempts on failure (default: 3, then exit)

## 10. Advanced Features

### 10.1 TODO Scanning
- **Pattern matching**: Custom regex via `--todo-pattern`
- **File filtering**: Specific files via `--todo-files`
- **Integration**: TODO items included in generated content
- **Default patterns**: Matches `TODO`, `FIXME`, `ADD` comments

### 10.2 Version Management
- **Automatic detection**: Extracts versions from project files or based on `--version-file` 
- **SemVer support**: Semantic versioning parsing and validation
- **Custom patterns**: User-defined version regex patterns
- **Manual override**: Explicit version specification via `--version`

### 10.3 Dry Run Mode
- **Prompt generation**: Shows what would be sent to the LLM
- **No API calls**: Skips actual LLM requests, uses prompt as output
- **Output simulation**: Displays where content would be written
- **Configuration testing**: Validates settings without side effects

## 11. Error Handling and Validation

### 10.1 Comprehensive Error Management
- **Configuration validation**: Detects invalid or missing settings
- **Git repository validation**: Ensures valid Git repository context and exits if not in repository
- **Repository root detection**: Automatically finds and changes to repository root directory
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

## 12. Installation and Distribution

### 11.1 Installation Methods
1. **Binary distribution**: Self-contained executables (~15MB)
   - Linux (x86_64, ARM64)
   - macOS (Intel, Apple Silicon)  
   - Windows (x86_64)
2. **Package managers**: Homebrew, Scoop, apt, yum
3. **PyPI installation**: `pip install giv` (requires Python 3.8.1+)
4. **Docker**: Pull from Docker Hub or build locally

### 11.2 File System Layout
- **User configuration**: `~/.giv/config`
- **Project configuration**: `.giv/config` (relative to repository root)
- **Project templates**: `.giv/templates/` (relative to repository root)
- **System templates**: Bundled in binary or Python package

**Note**: All project-relative paths are resolved from the Git repository root directory, ensuring consistent behavior regardless of where the application is executed within the repository.

### 11.3 Self-Update System
- **Update command**: `giv update [version]` for in-place updates
- **Version checking**: `giv available-releases` lists available versions
- **Binary replacement**: Downloads and replaces current executable

## 13. Business Rules and Requirements

### 12.0 Workflow
**Application Initialization**:
1. Validate execution environment (check for Git repository)
2. Detect Git repository root using `git rev-parse --show-toplevel`
3. Change working directory to repository root
4. Load configuration from repository and user settings

**Content Generation**:
1. Parse the list of commits from the provided revision
2. Loop through each commit in the list
   1. Create history file contain diff and metadata for a commit
   2. Send the history file content along with the `commit_summary.md` prompt template to the LLM to get a summary of the commit
   3. Save commit summary response in `giv/cache/[commit id]-summary.md`
3. Create prompt for the given document type and insert the commit summaries into the associated prompt template
4. Send final prompt to the LLM
5. Save response from the LLM to the output file or write it to stdout

### 12.1 Content Generation Rules
1. **Commit messages** must be clear, concise, and follow conventional format
2. **Changelogs** must follow Keep a Changelog standard with proper versioning
3. **Release notes** must maintain professional tone suitable for public consumption
4. **Announcements** must emphasize user benefits and engaging language
5. **All content** must be factually accurate based on actual code changes

### 12.2 Git Integration Requirements
1. **Must operate in valid Git repositories** and exit with clear error messages if not in a repository
2. **Must automatically change to repository root directory** on startup using `git rev-parse --show-toplevel`
3. **Must support all standard Git revision syntax** without exceptions
4. **Must handle empty repositories and initial commits** gracefully
5. **Must respect Git ignore patterns** for file analysis
6. **Must preserve Git repository state** without unintended modifications
7. **Must ensure consistent behavior** regardless of execution location within repository

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
1. **Must preserve file permissions** and ownership
2. **Must handle concurrent access** safely
3. **Must validate write permissions** before attempting operations
4. **Must support atomic file operations** to prevent corruption
5. **Must exclude binary and large files** from diff processing
6. **Must use UTF-8 encoding** for all file operations

### 12.6 Caching and Performance Requirements
1. **Must cache generated commit summaries** until explicitly cleared
2. **Must support chunking for large commits** (future version)
3. **Must handle project type conflicts** by prompting user when unset
4. **Must support CI/CD integration** through environment variables
5. **Must manage team configuration** via `.giv/config` files in repositories

## 14. Security and Extensibility

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

## 14 Potential Future Features

### 14.1 Performance and Scalability Enhancements
- **Large commit chunking**: Support breaking down large diffs into chunks and returning a summary for the commit once all chunks are processed
- **Enhanced section updating**: Improve merge lists, update headers, and better date/header management for structured documents
- **Markdown linting and fixing**: Automatically lint and fix markdown formatting issues before output

### 14.2 Content and Metadata Enhancements
- **Git user integration**: Add `git config user.name` to template variables and output metadata
- **README integration**: Include project README content in summaries and prompts for better context
- **Enhanced date tokens**: Add more granular date formatting options to template variables (current implementation uses `{DATE}`)
- **TODO label replacement**: Optionally configure todo labels and descriptions
  - `todo.labels.bug="Bug Fixed"` in the config would replace `bug` with `Bug Fixed` in the history file that is added to the prompt
- **Advanced TODO processing**: Improve prompt with more specific todo rules (e.g., BUG→FIXED changes go in `### Fixed` subsection)

- **Advanced template system**: 
  - `--rules-file` parameter for custom content generation rules to replace the `{RULES}` token in templates
  - `--example-file` parameter with "auto" mode to extract examples from existing output files to replace the `{EXAMPLE}` token in templates
- **Sample content tokens**: Include `{SAMPLE}` token to provide current or previous section content in prompts for consistency

### 14.3 User Interface and Experience
- **Glow integration**: Use [glow](https://github.com/charmbracelet/glow) for enhanced markdown rendering when available
  - New config setting: `GIV_USE_GLOW` to enable/disable glow output
  - Automatic detection of glow binary in PATH
- **No-pager option**: Add `--no-pager` option for stdout output (default true for message command)
- **Interactive mode**: Add `--interactive` flag to review, confirm, or regenerate model output before saving
- **Manual review option**: Option to manually review and update content before saving to files

### 14.4 Advanced Help and Documentation
- **Enhanced help command**: AI-powered help system using vector search
  - Index docs folder, project tree, and usage text using Milvus CLI
  - Support natural language queries: `giv help "some question here"`
  - Provide command suggestions when commands fail based on indexed documentation
- **Chat interfaces**: 
  - Chat with codebase/history: Interactive exploration of repository changes
  - Chat with TODOs: Interactive management and discussion of TODO items

### 14.5 Quality Assurance and Review
- **LLM-powered automatic review**: Option to use LLM to automatically review output before final save
  - Reviews format and attempts corrections or triggers retry
  - Validates against Keep a Changelog standards for changelog command
- **Advanced pattern matching**: Allow users to specify regex patterns for:
  - Section matching in existing files
  - Header identification and formatting
  - Version number extraction
  - TODO pattern customization (extends current `--todo-pattern`)

### 14.6 New Document Types and Commands
- **Roadmap document type**: Generate project roadmaps based on TODO items, issues, and planned features
- **Contributing subcommand**: Generate CONTRIBUTING.md files with project-specific guidelines
- **README subcommand**: Generate or update README.md files with project metadata and documentation
- **License subcommand**: Generate LICENSE files by fetching license content from web sources

### 14.7 Development and Distribution
- **Enhanced Docker image**: Include additional CLI tools in Docker distribution:
  - Ollama for local LLM support
  - Glow for markdown rendering
  - GitHub CLI (gh) for repository integration