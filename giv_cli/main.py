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


def main(argv: list[str] | None = None) -> int:
    """Entrypoint used by the ``giv`` console script.

    Parameters
    ----------
    argv:
        Optional list of command line arguments.  When ``None``, defaults
        to :data:`sys.argv[1:]`.

    Returns
    -------
    int
        Exit code.  ``0`` indicates success, non–zero indicates failure.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

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