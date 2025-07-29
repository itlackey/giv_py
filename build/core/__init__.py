"""
Core build system for giv CLI.
"""
from .config import BuildConfig
from .version_manager import VersionManager

__all__ = ["BuildConfig", "VersionManager"]
