"""
Message command implementation.

This module implements the message command that generates commit messages
from git diffs using AI assistance.
"""
from __future__ import annotations

import argparse
from typing import Dict

from ..config import ConfigManager
from ..constants import TEMPLATE_MESSAGE, TEMPERATURE_CREATIVE
from .base import DocumentGeneratingCommand


class MessageCommand(DocumentGeneratingCommand):
    """Generate commit messages from git diffs."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize message command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager, TEMPLATE_MESSAGE, default_temperature=TEMPERATURE_CREATIVE)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Customize template context for message generation.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Customized context for message generation
        """
        # Message command uses the base context as-is
        return context