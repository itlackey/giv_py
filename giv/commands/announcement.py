"""
Announcement command implementation.

This module implements the announcement command that creates marketing-style
announcements with full output mode support.
"""
from __future__ import annotations

import argparse
from typing import Dict

from ..config import ConfigManager
from ..constants import (
    TEMPLATE_ANNOUNCEMENT, TEMPERATURE_CREATIVE, DEFAULT_ANNOUNCEMENT_FILE,
    CONFIG_ANNOUNCEMENT_FILE, CONFIG_OUTPUT_MODE, CONFIG_OUTPUT_VERSION,
    OUTPUT_MODE_AUTO, OUTPUT_MODE_OVERWRITE
)
from ..lib.metadata import ProjectMetadata
from .base import DocumentGeneratingCommand


class AnnouncementCommand(DocumentGeneratingCommand):
    """Create marketing-style announcements."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize announcement command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager, TEMPLATE_ANNOUNCEMENT, default_temperature=TEMPERATURE_CREATIVE)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Customize template context for announcement generation.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Customized context for announcement generation
        """
        # Override VERSION with output_version if specified
        output_version = getattr(self.args, 'output_version', None) or self.config.get("output_version") or ProjectMetadata.get_version()
        context["VERSION"] = output_version
        return context
    
    def handle_output(self, content: str, output_file: Optional[str] = None, 
                     output_mode: str = "auto", output_version: Optional[str] = None) -> bool:
        """Handle announcement output with appropriate defaults.
        
        Parameters
        ----------
        content : str
            Content to output
        output_file : str
            Output file path (defaults to ANNOUNCEMENT.md)
        output_mode : str
            Output mode (defaults to "overwrite" for announcements)
        output_version : str
            Version for section updates
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Use announcement-specific defaults with version-based naming  
        if not output_file and not getattr(self.args, 'output_file', None) and not self.config.get(CONFIG_ANNOUNCEMENT_FILE):
            version = output_version or ProjectMetadata.get_version() or "unknown"
            output_file = f"{version}_announcement.md"
        else:
            output_file = output_file or getattr(self.args, 'output_file', None) or self.config.get(CONFIG_ANNOUNCEMENT_FILE) or DEFAULT_ANNOUNCEMENT_FILE
        output_mode = getattr(self.args, 'output_mode', None) or self.config.get(CONFIG_OUTPUT_MODE) or OUTPUT_MODE_AUTO
        output_version = getattr(self.args, 'output_version', None) or self.config.get(CONFIG_OUTPUT_VERSION) or ProjectMetadata.get_version()
        
        # Map "auto" mode to "overwrite" for announcements
        if output_mode == OUTPUT_MODE_AUTO:
            output_mode = OUTPUT_MODE_OVERWRITE
        
        return super().handle_output(content, output_file, output_mode, output_version)