"""
Document command implementation.

This module implements the document command that generates custom content
using user-provided prompt templates.
"""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from ..config import ConfigManager
from ..constants import TEMPERATURE_CREATIVE
from ..errors import ConfigError
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