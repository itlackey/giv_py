"""
Standardized error handling for giv CLI.

This module provides consistent error handling patterns including
custom exceptions, error formatting, and standardized exit codes.
"""
from __future__ import annotations

import sys
from typing import Optional


# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_TEMPLATE_ERROR = 2
EXIT_GIT_ERROR = 3
EXIT_CONFIG_ERROR = 4
EXIT_API_ERROR = 5
EXIT_OUTPUT_ERROR = 6


class GivError(Exception):
    """Base exception for all giv CLI errors."""
    
    def __init__(self, message: str, exit_code: int = EXIT_GENERAL_ERROR):
        """Initialize error with message and exit code.
        
        Parameters
        ----------
        message : str
            Error message
        exit_code : int
            Exit code for CLI
        """
        super().__init__(message)
        self.exit_code = exit_code


class TemplateError(GivError):
    """Error in template processing."""
    
    def __init__(self, message: str):
        super().__init__(f"Template error: {message}", EXIT_TEMPLATE_ERROR)


class GitError(GivError):
    """Error in Git operations."""
    
    def __init__(self, message: str):
        super().__init__(f"Git error: {message}", EXIT_GIT_ERROR)


class ConfigError(GivError):
    """Error in configuration management."""
    
    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}", EXIT_CONFIG_ERROR)


class APIError(GivError):
    """Error in API communication."""
    
    def __init__(self, message: str):
        super().__init__(f"API error: {message}", EXIT_API_ERROR)


class OutputError(GivError):
    """Error in output handling."""
    
    def __init__(self, message: str):
        super().__init__(f"Output error: {message}", EXIT_OUTPUT_ERROR)


def handle_error(error: Exception, verbose: bool = False) -> int:
    """Handle errors with consistent formatting and exit codes.
    
    Parameters
    ----------
    error : Exception
        Exception to handle
    verbose : bool
        Whether to show full traceback
        
    Returns
    -------
    int
        Exit code
    """
    if isinstance(error, GivError):
        print(f"Error: {error}", file=sys.stderr)
        return error.exit_code
    elif isinstance(error, FileNotFoundError):
        print(f"Error: File not found: {error}", file=sys.stderr)
        return EXIT_GENERAL_ERROR
    elif isinstance(error, KeyboardInterrupt):
        print("\nOperation cancelled by user", file=sys.stderr)
        return EXIT_GENERAL_ERROR
    else:
        if verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        else:
            print(f"Error: {error}", file=sys.stderr)
        return EXIT_GENERAL_ERROR


def print_error(message: str, prefix: str = "Error") -> None:
    """Print error message to stderr with consistent formatting.
    
    Parameters
    ----------
    message : str
        Error message
    prefix : str
        Error prefix (default: "Error")
    """
    print(f"{prefix}: {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message to stderr.
    
    Parameters
    ----------
    message : str
        Warning message
    """
    print_error(message, "Warning")