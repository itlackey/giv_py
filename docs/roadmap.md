# GIV CLI Roadmap

This document outlines planned features and improvements for the GIV CLI tool.

## Documentation Improvements

### Priority: High
- **External API documentation**: Comprehensive guide for using third-party APIs
- **Workflow examples**: Integration examples with npm, CI/CD pipelines, Git hooks
- **Custom prompt examples**: Using `document` subcommand with custom templates
- **Extension guide**: Adding new document type subcommands
- **Scripting integration**: Sourcing giv functions in other scripts

## Testing and Quality Assurance

### Priority: High
- **Comprehensive test suite**: More "real-world" tests with detailed output validation
- **Long commit history testing**: Validation with extensive commit histories and summaries
- **Performance benchmarking**: Testing with large repositories and complex diffs

## Enhanced Content Generation

### Priority: Medium
- **Git user integration**: Add `git config user.name` to template variables and output
- **README integration**: Include project README content in summaries for better context
- **Enhanced date formatting**: More granular date formatting options for templates
- **TODO label replacement**: Configurable todo labels and descriptions
  - Example: `todo.labels.bug="Bug Fixed"` replaces `bug` with `Bug Fixed` in prompts
- **Advanced TODO processing**: Specific rules for different TODO types (BUG→FIXED goes in `### Fixed`)

## Template System Enhancements

### Priority: Medium
- **Rules files**: `--rules-file` parameter for custom content generation rules (`[RULES]` token)
- **Example extraction**: `--example-file` with "auto" mode to extract examples from existing files (`[EXAMPLE]` token)
- **Sample content**: `[SAMPLE]` token to provide current or previous section content for consistency

## User Interface and Experience

### Priority: Medium
- **Glow integration**: Enhanced markdown rendering when [glow](https://github.com/charmbracelet/glow) is available
  - New config setting: `GIV_USE_GLOW` to enable/disable
  - Automatic detection of glow binary in PATH
- **No-pager option**: `--no-pager` option for stdout output (default true for message command)
- **Interactive mode**: `--interactive` flag to review, confirm, or regenerate output before saving
- **Manual review**: Option to manually review and update content before saving

## Advanced Features

### Priority: Low
- **Enhanced help system**: AI-powered help using vector search
  - Index docs folder, project tree, and usage text using Milvus CLI
  - Natural language queries: `giv help "some question here"`
  - Command suggestions when commands fail based on documentation
- **Chat interfaces**: 
  - Chat with codebase/history: Interactive exploration of repository changes
  - Chat with TODOs: Interactive management and discussion of TODO items
- **LLM-powered review**: Automatic output review before final save
  - Format validation and correction attempts
  - Keep a Changelog standard validation for changelog command
- **Advanced pattern matching**: User-specified regex patterns for:
  - Section matching in existing files
  - Header identification and formatting
  - Version number extraction
  - TODO pattern customization

## Section Management Improvements

### Priority: Medium
- **Improved section updating**: Better merge lists, update headers, date and header management
- **Markdown linting**: Automatic linting and fixing before output
- **Sample token support**: Include `[SAMPLE]` token for current or previous section content

## New Document Types

### Priority: Low
- **Roadmap generation**: Generate project roadmaps based on TODO items and planned features
- **Contributing guidelines**: `contributing` subcommand for CONTRIBUTING.md files
- **README generation**: `readme` subcommand for README.md files with project metadata
- **License management**: `license` subcommand that fetches license content from web sources

## Docker and Distribution

### Priority: Low
- **Enhanced Docker image**: Include additional CLI tools:
  - Ollama for local LLM support
  - Glow for markdown rendering
  - GitHub CLI (gh) for repository integration

## Infrastructure and Performance

### Priority: Future
- **Large commit chunking**: Support breaking down large diffs into chunks
- **Repository chunking**: Handle very large repositories efficiently
- **Caching improvements**: Enhanced commit summary caching strategies
- **Performance optimization**: Faster processing for large codebases

---

## Contributing

To contribute to any of these roadmap items:

1. Check existing issues and discussions
2. Create an issue for new features or enhancements
3. Follow the contribution guidelines in CONTRIBUTING.md
4. Submit pull requests with clear descriptions and tests

## Status Legend

- **Priority: High** - Planned for next major release
- **Priority: Medium** - Planned for future releases
- **Priority: Low** - Ideas for consideration
- **Priority: Future** - Long-term vision items