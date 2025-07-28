"""
giv package

This package contains a Python rewrite of the original Bash‐based `giv` command
line interface.  The goal of the rewrite is to provide an equivalent feature
set in a cross platform, maintainable implementation.  The API surface is kept
as close as practical to the original scripts: commands are exposed via a
single entry point and each subcommand performs similar work to its Bash
counterpart.  See `README.md` in the project root for a high level overview.
"""

from importlib import metadata

__all__ = ["__version__"]

try:
    # Read version from package metadata when installed
    __version__ = metadata.version("giv")
except metadata.PackageNotFoundError:
    # Fallback during development
    __version__ = "0.1.0"