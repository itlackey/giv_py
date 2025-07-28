"""
Argument parsing and command dispatch.

This module defines the command line interface for the Python rewrite of
``giv``.  It closely mirrors the original Bash argument parser: global
options apply to all subcommands and each command implements its own
options and behaviour.  To add a new command or extend existing ones,
edit the ``build_parser`` and ``run_command`` functions.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from . import __version__
from .config import ConfigManager
from .commands import (
    MessageCommand,
    SummaryCommand, 
    DocumentCommand,
    ChangelogCommand,
    ReleaseNotesCommand,
    AnnouncementCommand,
    ConfigCommand,
)
from .lib.templates import TemplateEngine

logger = logging.getLogger(__name__)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments that can appear after subcommands."""
    parser.add_argument("--verbose", action="store_true", help="Enable debug/trace output")  
    parser.add_argument("--dry-run", action="store_true", help="Preview only; don't write any files")
    parser.add_argument("--output-mode", type=str, choices=["auto", "prepend", "append", "update", "overwrite", "none"], 
                       help="Output mode: auto, prepend, append, update, overwrite, none")
    parser.add_argument("--output-file", type=str, help="Write the output to the specified file instead of stdout")
    return parser


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser used for all commands.

    Returns
    -------
    argparse.ArgumentParser
        Fully configured parser with subcommands.
    """
    parser = argparse.ArgumentParser(
        prog="giv",
        description=(
            "Python implementation of the giv CLI, ported from the original Bash scripts. "
            "Use this tool to generate AI‑assisted commit messages, summaries, release notes and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  giv init                               # Interactive configuration setup
  giv config list                        # List all configuration values
  giv config set api.key "your-api-key"  # Set configuration value
  giv message HEAD~3..HEAD src/
  giv summary --output-file SUMMARY.md
  giv changelog v1.0.0..HEAD --todo-files '*.js' --todo-pattern 'TODO:'
  giv release-notes v1.2.0..HEAD --api-model gpt-4o --api-url https://api.example.com
  giv announcement --output-file ANNOUNCE.md
  giv document --prompt-file templates/my_custom_prompt.md --output-file REPORT.md HEAD
        """,
        add_help=False,
    )

    # Global options - matching Bash version exactly
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("-v", "--version", action="store_true", help="Show the program's version number and exit")
    parser.add_argument("--verbose", action="store_true", help="Enable debug/trace output")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; don't write any files")
    parser.add_argument("--config-file", type=str, help="Shell config file to source before running")
    parser.add_argument("--todo-files", type=str, help="Pathspec for files to scan for TODOs")
    parser.add_argument("--todo-pattern", type=str, help="Regex to match TODO lines")
    parser.add_argument("--version-file", type=str, help="Pathspec of file(s) to inspect for version bumps")
    parser.add_argument("--version-pattern", type=str, help="Custom regex to identify version strings")
    parser.add_argument("--model", type=str, help="Specify the local or remote model name")
    parser.add_argument("--api-model", type=str, help="Remote model name (alias for --model)")
    parser.add_argument("--api-url", type=str, help="Remote API endpoint URL")
    parser.add_argument("--api-key", type=str, help="API key for remote mode")
    parser.add_argument("--output-mode", type=str, choices=["auto", "prepend", "append", "update", "overwrite", "none"], 
                       help="Output mode: auto, prepend, append, update, overwrite, none")
    parser.add_argument("--output-version", type=str, help="Version string for release content")
    parser.add_argument("--output-file", type=str, help="Write the output to the specified file instead of stdout")
    parser.add_argument("--prompt-file", type=str, help="Path to a custom prompt template file")
    parser.add_argument("--list", action="store_true", help="List available local models")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>", help="Available subcommands")

    # config command
    config_parser = subparsers.add_parser("config", help="Manage configuration values (list, get, set, unset)")
    config_group = config_parser.add_mutually_exclusive_group()
    config_group.add_argument("--list", action="store_true", help="List all configuration values")
    config_group.add_argument("--get", action="store_true", help="Get a configuration value")
    config_group.add_argument("--set", action="store_true", help="Set a configuration value")
    config_group.add_argument("--unset", action="store_true", help="Remove a configuration value")
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value (for set operation)")

    # message command
    msg_parser = subparsers.add_parser("message", aliases=["msg"], help="Generate a commit message from the diff")
    msg_parser.add_argument("revision", nargs="?", default="--current", help="Revision range to analyze")
    msg_parser.add_argument("pathspec", nargs="*", help="Limit analysis to the specified paths")
    _add_common_args(msg_parser)

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Generate a summary of recent changes")
    summary_parser.add_argument("revision", nargs="?", default="--current", help="Revision range to summarize")
    summary_parser.add_argument("pathspec", nargs="*", help="Limit summary to the specified paths")
    _add_common_args(summary_parser)

    # changelog command
    changelog_parser = subparsers.add_parser("changelog", help="Generate or update a changelog")
    changelog_parser.add_argument("revision", nargs="?", default="--current", help="Revision range for changelog")
    changelog_parser.add_argument("pathspec", nargs="*", help="Limit changelog to the specified paths")
    _add_common_args(changelog_parser)

    # release-notes command
    release_parser = subparsers.add_parser("release-notes", help="Generate release notes for a tagged release")
    release_parser.add_argument("revision", nargs="?", default="--current", help="Revision range for release notes")
    release_parser.add_argument("pathspec", nargs="*", help="Limit release notes to the specified paths")
    _add_common_args(release_parser)

    # announcement command
    announce_parser = subparsers.add_parser("announcement", help="Create a marketing-style announcement")
    announce_parser.add_argument("revision", nargs="?", default="--current", help="Revision range for announcement")
    announce_parser.add_argument("pathspec", nargs="*", help="Limit announcement to the specified paths")
    _add_common_args(announce_parser)

    # document command
    doc_parser = subparsers.add_parser("document", help="Generate custom content using your own prompt template")
    doc_parser.add_argument("revision", nargs="?", default="--current", help="Revision range to document")
    doc_parser.add_argument("pathspec", nargs="*", help="Limit documentation to the specified paths")
    doc_parser.add_argument("--prompt-file", dest="prompt_file", required=True, help="Path to custom prompt template")
    _add_common_args(doc_parser)

    # init command
    subparsers.add_parser("init", help="Initialize giv configuration")

    # version command
    subparsers.add_parser("version", help="Print the version and exit")

    # help command
    subparsers.add_parser("help", help="Show help for a given command")

    # available-releases command
    subparsers.add_parser("available-releases", help="List script versions")

    # update command
    update_parser = subparsers.add_parser("update", help="Self-update giv")
    update_parser.add_argument("version", nargs="?", help="Specific version to update to (default: latest)")

    return parser


def run_command(args: argparse.Namespace) -> int:
    """Dispatch the parsed arguments to the corresponding subcommand.

    Parameters
    ----------
    args:
        The parsed arguments from :func:`build_parser`.

    Returns
    -------
    int
        Exit code.
    """
    # Set up logging if verbose mode enabled
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Preprocess global flags
    if args.help and not args.command:
        # Show top level help
        build_parser().print_help()
        return 0
    if args.version and not args.command:
        print(f"giv {__version__}")
        return 0

    # Default to message command if no command specified
    if not args.command:
        args.command = "message"

    # Determine config file path
    config_path = None
    if args.config_file:
        config_path = Path(args.config_file)
    cfg_mgr = ConfigManager(config_path=config_path)

    # Apply global configuration from args to environment
    _apply_global_args(args, cfg_mgr)

    # Dispatch to subcommands
    if args.command == "config":
        return ConfigCommand(args, cfg_mgr).run()
    elif args.command in ["message", "msg"]:
        return MessageCommand(args, cfg_mgr).run()
    elif args.command == "summary":
        return SummaryCommand(args, cfg_mgr).run()
    elif args.command == "document":
        return DocumentCommand(args, cfg_mgr).run()
    elif args.command == "changelog":
        return ChangelogCommand(args, cfg_mgr).run()
    elif args.command == "release-notes":
        return ReleaseNotesCommand(args, cfg_mgr).run()
    elif args.command == "announcement":
        return AnnouncementCommand(args, cfg_mgr).run()
    elif args.command == "available-releases":
        return _run_available_releases(args, cfg_mgr)
    elif args.command == "update":
        return _run_update(args, cfg_mgr)
    elif args.command == "init":
        return _run_init(args, cfg_mgr)
    elif args.command == "version":
        print(f"giv {__version__}")
        return 0
    elif args.command == "help":
        # Delegate help to specific command if provided
        build_parser().print_help()
        return 0
    else:
        # Unknown command
        print(f"Error: Unknown subcommand '{args.command}'.", file=sys.stderr)
        print("Use -h or --help for usage information.", file=sys.stderr)
        return 1


def _apply_global_args(args: argparse.Namespace, cfg_mgr: ConfigManager) -> None:
    """Apply global arguments to configuration, respecting precedence."""
    # Apply global args to config manager for access by subcommands
    if args.api_url:
        cfg_mgr.set("api_url", args.api_url)
    if args.api_key:
        cfg_mgr.set("api_key", args.api_key)
    if args.api_model or args.model:
        cfg_mgr.set("api_model", args.api_model or args.model)
    if args.todo_files:
        cfg_mgr.set("todo_files", args.todo_files)
    if args.todo_pattern:
        cfg_mgr.set("todo_pattern", args.todo_pattern)
    if args.version_file:
        cfg_mgr.set("version_file", args.version_file)
    if args.version_pattern:
        cfg_mgr.set("version_pattern", args.version_pattern)
    if args.output_mode:
        cfg_mgr.set("output_mode", args.output_mode)
    if args.output_version:
        cfg_mgr.set("output_version", args.output_version)






def _run_available_releases(args: argparse.Namespace, cfg_mgr: ConfigManager) -> int:
    """Handle the ``available-releases`` subcommand."""
    import urllib.request
    import json
    
    try:
        # Fetch releases from GitHub API
        url = "https://api.github.com/repos/giv-cli/giv/releases"
        with urllib.request.urlopen(url) as response:
            releases_data = json.loads(response.read().decode('utf-8'))
        
        # Extract and print tag names
        for release in releases_data:
            if 'tag_name' in release:
                print(release['tag_name'])
        
        return 0
    except Exception as e:
        print(f"Error fetching releases: {e}", file=sys.stderr)
        return 1


def _run_update(args: argparse.Namespace, cfg_mgr: ConfigManager) -> int:
    """Handle the ``update`` subcommand."""
    import urllib.request
    import json
    import subprocess
    import shlex
    
    # Get target version from args or default to latest
    target_version = getattr(args, 'version', None) or 'latest'
    
    try:
        # Fetch available releases from GitHub API
        url = "https://api.github.com/repos/giv-cli/giv/releases"
        with urllib.request.urlopen(url) as response:
            releases_data = json.loads(response.read().decode('utf-8'))
        
        if not releases_data:
            print("No releases available", file=sys.stderr)
            return 1
        
        # Determine the actual version to install
        if target_version == 'latest':
            latest_version = releases_data[0]['tag_name']
            actual_version = latest_version
            print(f"Updating giv to version {actual_version}...")
        else:
            # Verify the specified version exists
            available_versions = [release['tag_name'] for release in releases_data]
            if target_version not in available_versions:
                print(f"Error: Version {target_version} not found in available releases", file=sys.stderr)
                print(f"Available versions: {', '.join(available_versions)}", file=sys.stderr)
                return 1
            actual_version = target_version
            print(f"Updating giv to version {actual_version}...")
        
        # Run the install script with the target version
        install_url = "https://raw.githubusercontent.com/giv-cli/giv/main/install.sh"
        curl_cmd = ["curl", "-fsSL", install_url]
        sh_cmd = ["sh", "--", "--version", actual_version]
        
        # Use subprocess to pipe curl output to sh
        with subprocess.Popen(curl_cmd, stdout=subprocess.PIPE) as curl_proc:
            result = subprocess.run(sh_cmd, stdin=curl_proc.stdout, 
                                  capture_output=False, text=True)
            curl_proc.stdout.close()
            
            if result.returncode != 0:
                print(f"Error: Installation failed with exit code {result.returncode}", file=sys.stderr)
                return 1
        
        print("Update complete.")
        return 0
        
    except Exception as e:
        print(f"Error during update: {e}", file=sys.stderr)
        return 1




def _run_init(args: argparse.Namespace, cfg_mgr: ConfigManager) -> int:
    """Handle the ``init`` subcommand."""
    # Create a .giv directory and copy default templates using template manager
    template_mgr = TemplateEngine()
    cwd = Path.cwd()
    giv_dir = cwd / ".giv"
    giv_dir.mkdir(exist_ok=True)
    
    # Create templates directory
    templates_dir = giv_dir / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Copy system templates to project templates directory
    system_templates_dir = Path(__file__).parent / "templates"
    if system_templates_dir.exists():
        for template_file in system_templates_dir.glob("*.md"):
            dest = templates_dir / template_file.name
            if not dest.exists():
                dest.write_text(template_file.read_text(encoding='utf-8'), encoding='utf-8')
    
    print(f"Initialised {giv_dir}")
    return 0