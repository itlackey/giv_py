"""
Document command implementation.

This module implements the document command that generates custom content
using user-provided prompt templates.
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional

from ..config import ConfigManager
from ..constants import TEMPERATURE_CREATIVE
from ..errors import ConfigError
from ..lib.metadata import ProjectMetadata
from .base import DocumentGeneratingCommand


class DocumentCommand(DocumentGeneratingCommand):
    """Generate custom content using arbitrary prompt templates."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize document command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        # Document command uses custom template from args.prompt_file
        template_name = getattr(args, 'prompt_file', None)
        if not template_name:
            raise ConfigError("--prompt-file is required for the document subcommand")
        
        super().__init__(args, config_manager, template_name, default_temperature=TEMPERATURE_CREATIVE)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Customize template context for document generation.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Customized context for document generation
        """
        # Document command uses the base context as-is
        return context
    
    def handle_output(self, content: str, output_file: Optional[str] = None, 
                     output_mode: str = "auto", output_version: Optional[str] = None) -> bool:
        """Handle document output with version-based default file naming.
        
        Parameters
        ----------
        content : str
            Content to output
        output_file : str
            Output file path (defaults to {VERSION}_document.md)
        output_mode : str
            Output mode (defaults to "overwrite" for documents)
        output_version : str
            Version for section updates
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Use document-specific defaults with version-based naming  
        if not output_file and not getattr(self.args, 'output_file', None):
            version = output_version or ProjectMetadata.get_version() or "unknown"
            output_file = f"{version}_document.md"
        else:
            output_file = output_file or getattr(self.args, 'output_file', None)
            
        output_mode = getattr(self.args, 'output_mode', None) or output_mode
        output_version = getattr(self.args, 'output_version', None) or output_version or ProjectMetadata.get_version()
        
        # Map "auto" mode to "overwrite" for documents
        if output_mode == "auto":
            output_mode = "overwrite"
        
        return super().handle_output(content, output_file, output_mode, output_version)