"""
Changelog command implementation.

This module implements the changelog command that generates or updates
changelog files with version management and output mode support.
"""
from __future__ import annotations

import argparse
from typing import Dict

from ..config import ConfigManager
from ..constants import (
    TEMPLATE_CHANGELOG, TEMPERATURE_FACTUAL, DEFAULT_CHANGELOG_FILE,
    CONFIG_CHANGELOG_FILE, CONFIG_OUTPUT_MODE, CONFIG_OUTPUT_VERSION,
    OUTPUT_MODE_AUTO, OUTPUT_MODE_UPDATE
)
from ..lib.metadata import ProjectMetadata
from ..lib.utils import resolve_config_triple
from .base import DocumentGeneratingCommand


class ChangelogCommand(DocumentGeneratingCommand):
    """Generate or update changelog files."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize changelog command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager, TEMPLATE_CHANGELOG, default_temperature=TEMPERATURE_FACTUAL)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Customize template context for changelog generation.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Customized context for changelog generation
        """
        # Override VERSION with output_version if specified
        output_version = getattr(self.args, 'output_version', None) or self.config.get("output_version") or ProjectMetadata.get_version()
        context["VERSION"] = output_version
        return context
    
    def handle_output(self, content: str, output_file: Optional[str] = None, 
                     output_mode: str = "auto", output_version: Optional[str] = None) -> bool:
        """Handle changelog output with appropriate defaults.
        
        Parameters
        ----------
        content : str
            Content to output
        output_file : str
            Output file path (defaults to CHANGELOG.md)
        output_mode : str
            Output mode (defaults to "update" for changelogs)
        output_version : str
            Version for section updates
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Use changelog-specific defaults with shared utility
        resolved_file, resolved_mode, resolved_version = resolve_config_triple(
            self.args, self.config,
            file_config=('output_file', CONFIG_CHANGELOG_FILE, DEFAULT_CHANGELOG_FILE),
            mode_config=('output_mode', CONFIG_OUTPUT_MODE, OUTPUT_MODE_AUTO),
            version_config=('output_version', CONFIG_OUTPUT_VERSION)
        )
        
        output_file = output_file or resolved_file
        output_mode = resolved_mode
        output_version = resolved_version
        
        # Map "auto" mode to "update" for changelog
        if output_mode == OUTPUT_MODE_AUTO:
            output_mode = OUTPUT_MODE_UPDATE
        
        return super().handle_output(content, output_file, output_mode, output_version)