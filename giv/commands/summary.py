"""
Summary command implementation.

This module implements the summary command that generates summaries
of recent changes using AI assistance.
"""
from __future__ import annotations

import argparse
from typing import Dict

from ..config import ConfigManager
from ..constants import TEMPLATE_SUMMARY, TEMPERATURE_CREATIVE
from .base import DocumentGeneratingCommand


class SummaryCommand(DocumentGeneratingCommand):
    """Generate summaries of recent changes."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize summary command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager, TEMPLATE_SUMMARY, default_temperature=TEMPERATURE_CREATIVE)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Customize template context for summary generation.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Customized context for summary generation
        """
        # Summary command uses the base context as-is
        return context