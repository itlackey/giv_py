"""
Help command implementation.

This module implements the help command that provides detailed help information
for specific commands or general usage information.
"""
from __future__ import annotations

import argparse
import sys

from ..config import ConfigManager
from .base import BaseCommand


class HelpCommand(BaseCommand):
    """Show help for a given command or general usage."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize help command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager)
    
    def run(self) -> int:
        """Execute the help command.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        command = getattr(self.args, 'command_name', None)
        
        if command:
            return self._show_command_help(command)
        else:
            return self._show_general_help()
    
    def _show_general_help(self) -> int:
        """Show general help information."""
        help_text = """giv - AI-powered Git workflow enhancement tool

USAGE:
    giv [global-options] <command> [command-options] [revision] [pathspec...]

GLOBAL OPTIONS:
    --config-file <file>    Configuration file to load
    --verbose              Enable detailed logging output  
    --dry-run              Preview mode - no file writes or API calls

COMMANDS:
    message      Generate commit messages from Git diffs (default)
    summary      Create comprehensive technical summaries of changes
    changelog    Generate or update changelog files
    release-notes Generate professional release notes for tagged releases
    announcement Create marketing-style announcements
    document     Generate custom content using user-provided templates
    config       Manage configuration values (list, get, set, unset)
    init         Initialize giv configuration and templates in project
    version      Show version information
    help         Show help for a given command
    available-releases List available releases
    update       Self-update giv to latest or specific version

EXAMPLES:
    giv message                    # Generate commit message for current changes
    giv summary HEAD~3..HEAD       # Summarize last 3 commits
    giv changelog v1.0.0..HEAD     # Generate changelog since v1.0.0
    giv --dry-run release-notes    # Preview release notes
    giv config set api.model gpt-4 # Set API model
    giv help changelog             # Get help for changelog command

For more information on a specific command, use:
    giv help <command>

For full documentation, visit: https://github.com/giv-cli/giv-py
"""
        print(help_text)
        return 0
    
    def _show_command_help(self, command: str) -> int:
        """Show help for a specific command.
        
        Parameters
        ----------
        command : str
            Command name to show help for
            
        Returns
        -------
        int
            Exit code
        """
        command_help = {
            "message": """MESSAGE - Generate commit messages from Git diffs

USAGE:
    giv [options] message [revision] [pathspec...]

DESCRIPTION:
    Generate AI-assisted commit messages from Git diffs. Analyzes working tree 
    changes by default and creates structured commit messages with clear, 
    descriptive language.

REVISION OPTIONS:
    --current (default)    Working tree changes
    --cached              Staged changes only  
    HEAD~3..HEAD          Git revision ranges
    <commit-hash>         Specific commit

EXAMPLES:
    giv message                    # Current working tree changes
    giv message --cached           # Staged changes only
    giv message HEAD~1             # Last commit
    giv message v1.0.0..HEAD       # Range of commits
    giv message -- src/            # Limit to src/ directory
""",
            "summary": """SUMMARY - Create comprehensive technical summaries

USAGE:
    giv [options] summary [revision] [pathspec...]

DESCRIPTION:
    Generate detailed technical documentation of changes suitable for project 
    updates, documentation, and reports. Includes analysis of code changes, 
    new features, and modifications.

EXAMPLES:
    giv summary                    # Summarize current changes
    giv summary HEAD~3..HEAD       # Summarize last 3 commits
    giv summary v1.0.0..HEAD       # Summarize since version 1.0.0
""",
            "changelog": """CHANGELOG - Generate or update changelog files

USAGE:  
    giv [options] changelog [revision] [pathspec...]

DESCRIPTION:
    Generate or update changelog files following Keep a Changelog standard.
    Automatically detects project version from metadata files and updates 
    existing changelog sections or creates new entries.

OUTPUT:
    Default file: CHANGELOG.md
    Default mode: auto (update existing sections or prepend new ones)

EXAMPLES:
    giv changelog                  # Update changelog with current changes
    giv changelog v1.0.0..HEAD     # Generate changelog since v1.0.0
    giv changelog --output-file CHANGES.md  # Custom output file
""",
            "release-notes": """RELEASE-NOTES - Generate professional release notes

USAGE:
    giv [options] release-notes [revision] [pathspec...]

DESCRIPTION:
    Generate professional release notes for tagged releases. Creates formal 
    release documentation with professional tone suitable for public release 
    announcements.

OUTPUT:
    Default file: {VERSION}_release_notes.md
    Default mode: overwrite

EXAMPLES:
    giv release-notes              # Generate notes for current version
    giv release-notes v1.2.0..HEAD # Generate notes for version range
""",
            "announcement": """ANNOUNCEMENT - Create marketing-style announcements

USAGE:
    giv [options] announcement [revision] [pathspec...]

DESCRIPTION:
    Generate user-friendly, engaging content that focuses on user benefits and 
    exciting features. Suitable for blog posts, social media, and public 
    announcements with marketing-oriented language.

OUTPUT:
    Default file: {VERSION}_announcement.md  
    Default mode: overwrite

EXAMPLES:
    giv announcement               # Create announcement for current changes
    giv announcement v1.2.0..HEAD  # Announcement for version range
""",
            "document": """DOCUMENT - Generate custom content using templates

USAGE:
    giv [options] document --prompt-file <template> [revision] [pathspec...]

DESCRIPTION:
    Generate custom content using user-provided templates. Supports all 
    template variables and substitution for flexible content generation 
    for unique requirements.

REQUIRED:
    --prompt-file <file>          Path to custom prompt template

OUTPUT:
    Default file: {VERSION}_document.md

EXAMPLES:
    giv document --prompt-file custom.md          # Use custom template
    giv document --prompt-file report.md HEAD~5..HEAD  # Custom report
""",
            "config": """CONFIG - Manage configuration values

USAGE:
    giv config [operation] [key] [value]

OPERATIONS:
    list              Display all configuration values (default)
    get <key>         Retrieve specific configuration value  
    set <key> <value> Set configuration value
    unset <key>       Remove configuration value

CONFIGURATION KEYS:
    api.url                    API endpoint URL
    api.key                    API authentication key
    api.model.name             Default model name
    api.model.temperature      LLM temperature (0.0-2.0)
    api.model.max_tokens       Maximum response tokens
    project.title              Project title override
    output.mode                Default output mode
    changelog.file             Changelog filename

EXAMPLES:
    giv config                          # List all settings
    giv config get api.model.name       # Get specific setting
    giv config set api.url "https://api.openai.com/v1/chat/completions"
    giv config unset api.key            # Remove setting
""",
            "init": """INIT - Initialize giv configuration and templates

USAGE:
    giv init

DESCRIPTION:
    Initialize giv configuration and templates in the current project.
    Creates .giv/ directory structure, copies default templates to project,
    and sets up project-local configuration.

ACTIONS:
    - Creates .giv/ directory structure
    - Copies system templates to .giv/templates/
    - Creates default configuration file
    - Sets up project-local configuration

EXAMPLES:
    giv init                    # Initialize giv in current project
""",
            "version": """VERSION - Show version information

USAGE:
    giv version

DESCRIPTION:
    Display the current version of giv and exit.

EXAMPLES:
    giv version                 # Show version
""",
        }
        
        if command in command_help:
            print(command_help[command])
            return 0
        else:
            print(f"No help available for command: {command}", file=sys.stderr)
            print(f"Available commands: {', '.join(sorted(command_help.keys()))}", file=sys.stderr)
            return 1