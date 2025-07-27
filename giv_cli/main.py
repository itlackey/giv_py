"""
Entry point for the `giv` command line application.

This module constructs the argument parser and dispatches to the
appropriate subcommand function.  It exists as a thin wrapper around the
command definitions in :mod:`giv_cli.cli`.
"""
from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .cli import build_parser, run_command

logger = logging.getLogger(__name__)


def _preprocess_args(argv):
    """Preprocess arguments to handle Bash-style config command syntax."""
    if not argv:
        return argv
    
    # Find the position of the 'config' command, accounting for global flags
    config_pos = -1
    for i, arg in enumerate(argv):
        if arg == "config":
            config_pos = i
            break
    
    # If we found 'config' and there's a next argument that's an operation
    if config_pos >= 0 and config_pos + 1 < len(argv):
        operation = argv[config_pos + 1]
        if operation in ["list", "get", "set", "unset"]:
            # Convert "config list" to "config --list", preserving preceding args
            new_argv = argv[:config_pos] + ["config", f"--{operation}"]
            # Add remaining arguments (key, value for get/set/unset operations)  
            if config_pos + 2 < len(argv):
                new_argv.extend(argv[config_pos + 2:])
            return new_argv
    
    return argv


def main(argv=None):
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
    
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # Convert SystemExit to return code for better test compatibility
        # Map argparse exit codes (2) to standard error code (1)
        return 1 if e.code != 0 else 0

    # Configure logging based on verbosity
    if getattr(args, "verbose", False):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        return run_command(args)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())