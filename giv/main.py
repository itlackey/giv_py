"""
Entry point for the `giv` command line application.

This module constructs the argument parser and dispatches to the
appropriate subcommand function.  It exists as a thin wrapper around the
command definitions in :mod:`giv.cli`.
"""
from __future__ import annotations

import logging
import sys

from .cli import build_parser, run_command

logger = logging.getLogger(__name__)


def _preprocess_args(argv: list[str]) -> list[str]:
    """Preprocess arguments to handle Bash-style config command syntax."""
    if not argv:
        return argv
    
    # Find the position of the 'config' command, accounting for global flags
    config_pos = -1
    for i, arg in enumerate(argv):
        if arg == "config":
            config_pos = i
            break
    
    if config_pos >= 0:
        # If 'config' is the last argument, default to list
        if config_pos + 1 >= len(argv):
            return argv[:config_pos] + ["config", "--list"]
        
        # Check if already processed (next arg is a flag like --list, --get, etc.)
        next_arg = argv[config_pos + 1]
        if next_arg.startswith("--") and next_arg[2:] in {"list", "get", "set", "unset"}:
            return argv  # Already processed, leave as-is
        
        # Check if next argument is an operation
        operation = next_arg
        if operation in ["list", "get", "set", "unset"]:
            # Convert "config list" to "config --list", preserving preceding args
            new_argv = argv[:config_pos] + ["config", f"--{operation}"]
            # Add remaining arguments (key, value for get/set/unset operations)  
            if config_pos + 2 < len(argv):
                new_argv.extend(argv[config_pos + 2:])
            return new_argv
        elif operation in ["--list", "--get", "--set", "--unset"]:
            # Already in flag format - just add key handling for get/set/unset
            new_argv = argv[:config_pos + 2]  # Keep "config --operation"
            # Add remaining arguments
            if config_pos + 2 < len(argv):
                new_argv.extend(argv[config_pos + 2:])
            return new_argv
        else:
            # Next argument is not an operation, could be:
            # - "config <key>" -> get operation
            # - "config <key> <value>" -> set operation
            if config_pos + 2 < len(argv):
                # There are 3+ args: config, key, value -> set operation
                key = argv[config_pos + 1]
                value = argv[config_pos + 2]
                new_argv = argv[:config_pos] + ["config", "--set", key, value]
                # Add any remaining arguments
                if config_pos + 3 < len(argv):
                    new_argv.extend(argv[config_pos + 3:])
                return new_argv
            else:
                # Only 2 args: config, key -> get operation  
                return argv[:config_pos] + ["config", "--get", operation]
    
    # Edge case: Handle empty arguments or unexpected input
    # Example: argv = [] should return [] without processing
    # Example: argv = ['config'] should default to ['config', '--list']
    return argv


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``giv`` command.

    This is the main entry point for giv CLI.  It parses the command line
    arguments and dispatches control to the relevant subcommand handler.

    Parameters
    ----------
    argv : list of str, optional
        Arguments to parse, by default None

    Returns
    -------
    int
        Exit code.  ``0`` indicates success, non–zero indicates failure.
    """
    if argv is None:
        argv = sys.argv[1:]
    
    # Preprocess arguments for compatibility
    argv = _preprocess_args(argv)
    
    # Handle case where preprocessing returns None (edge case for testing)
    if argv is None:
        argv = []
    
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # Convert SystemExit to return code for better test compatibility
        # Map argparse exit codes (2) to standard error code (1)
        return 1 if e.code != 0 else 0

    # Configure logging based on verbosity
    verbose_level = getattr(args, "verbose", 0)
    # Handle case where verbose might be a Mock object (in tests)
    try:
        is_verbose = verbose_level > 0
    except TypeError:
        # If comparison fails (e.g., Mock object), treat as verbose if truthy
        is_verbose = bool(verbose_level)
    
    if is_verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Repository validation and root navigation
    # Skip for certain commands that don't require repository context
    skip_repo_validation = getattr(args, 'command', None) in ['version', 'help', 'available-releases', 'update', 'init']
    
    if not skip_repo_validation:
        from .lib.repository import validate_and_change_to_repo_root
        validate_and_change_to_repo_root()

    try:
        return run_command(args)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception:
        logger.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())