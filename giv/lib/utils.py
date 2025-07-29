"""
Shared utility functions for the giv CLI.

This module provides common utility functions that are used across
multiple modules to reduce code duplication and improve maintainability.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional, Union

from ..lib.metadata import ProjectMetadata


def resolve_config_value(
    args: Any, 
    config_manager: Any, 
    arg_name: str,
    config_key: str, 
    default_value: Optional[str] = None
) -> Optional[str]:
    """Resolve configuration value with precedence: args > config > default.
    
    This function implements the standard configuration resolution pattern
    used throughout the codebase to eliminate duplication.
    
    Parameters
    ----------
    args : Any
        Argument namespace from argparse
    config_manager : Any
        Configuration manager instance
    arg_name : str
        Name of the argument attribute
    config_key : str
        Configuration key to look up
    default_value : Optional[str]
        Default value if not found elsewhere
        
    Returns
    -------
    Optional[str]
        Resolved configuration value
    """
    # 1. Check command line arguments (highest priority)
    arg_value = getattr(args, arg_name, None)
    if arg_value is not None:
        return arg_value
    
    # 2. Check configuration file
    config_value = config_manager.get(config_key)
    if config_value is not None:
        return config_value
    
    # 3. Return default value (lowest priority)
    return default_value


def resolve_config_triple(
    args: Any,
    config_manager: Any,
    file_config: tuple[str, str, str],  # (arg_name, config_key, default_value)
    mode_config: tuple[str, str, str],  # (arg_name, config_key, default_value) 
    version_config: tuple[str, str]     # (arg_name, config_key)
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Resolve the common output file/mode/version configuration pattern.
    
    This eliminates the duplicated 3-line pattern found across multiple commands.
    
    Parameters
    ----------
    args : Any
        Argument namespace from argparse
    config_manager : Any
        Configuration manager instance
    file_config : tuple[str, str, str]
        (arg_name, config_key, default_value) for output file
    mode_config : tuple[str, str, str]
        (arg_name, config_key, default_value) for output mode
    version_config : tuple[str, str]
        (arg_name, config_key) for output version
        
    Returns
    -------
    tuple[Optional[str], Optional[str], Optional[str]]
        (output_file, output_mode, output_version)
    """
    output_file = resolve_config_value(
        args, config_manager, 
        file_config[0], file_config[1], file_config[2]
    )
    
    output_mode = resolve_config_value(
        args, config_manager,
        mode_config[0], mode_config[1], mode_config[2]
    )
    
    output_version = resolve_config_value(
        args, config_manager,
        version_config[0], version_config[1], 
        ProjectMetadata.get_version()
    )
    
    return output_file, output_mode, output_version


def generate_version_based_filename(
    base_name: str,
    version: Optional[str] = None,
    extension: str = ".md"
) -> str:
    """Generate version-based filename following consistent pattern.
    
    This eliminates the duplicated version-based filename generation
    found in announcement, release_notes, and document commands.
    
    Parameters
    ----------
    base_name : str
        Base name for the file (e.g., "announcement", "release_notes")
    version : Optional[str]
        Version string, defaults to project version
    extension : str
        File extension, defaults to ".md"
        
    Returns
    -------
    str
        Generated filename like "v1.0.0_announcement.md"
    """
    if version is None:
        version = ProjectMetadata.get_version() or "unknown"
    
    # Normalize version (remove 'v' prefix if present)
    if version.startswith('v'):
        version = version[1:]
    
    return f"{version}_{base_name}{extension}"


def calculate_file_sha256(file_path: Union[str, Path]) -> str:
    """Calculate SHA256 hash of a file.
    
    This eliminates the duplicated SHA256 calculation found in
    homebrew and scoop build scripts.
    
    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the file to hash
        
    Returns
    -------
    str
        Hexadecimal SHA256 hash
        
    Raises
    ------
    FileNotFoundError
        If file does not exist
    OSError
        If file cannot be read
    """
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
    """Mask sensitive value for safe logging.
    
    Parameters
    ----------
    value : str
        Sensitive value to mask
    show_chars : int
        Number of characters to show at start and end
        
    Returns
    -------
    str
        Masked value
    """
    if not value or len(value) <= show_chars * 2:
        return "***"
    
    return f"{value[:show_chars]}{'*' * (len(value) - show_chars * 2)}{value[-show_chars:]}"