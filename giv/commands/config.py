"""
Config command implementation.

This module implements the config command that manages configuration values
using the list, get, set, and unset operations.
"""
from __future__ import annotations

import argparse
import sys

from ..config import ConfigManager
from .base import BaseCommand


class ConfigCommand(BaseCommand):
    """Manage configuration values (list, get, set, unset)."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize config command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager)
    
    def run(self) -> int:
        """Execute the config command.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        # Determine operation from flag-style arguments
        operation = None
        if getattr(self.args, 'list', False):
            operation = "list"
        elif getattr(self.args, 'get', False):
            operation = "get"
        elif getattr(self.args, 'set', False):
            operation = "set"
        elif getattr(self.args, 'unset', False):
            operation = "unset"
        
        key = getattr(self.args, 'key', None)
        value = getattr(self.args, 'value', None)
        
        # Handle "show" as an alias for "list"
        if key == "show":
            operation = "list"
            key = None
        
        # Handle different config operations
        if operation == "list" or (not operation and not key):
            return self._list_config()
        elif operation == "get" or (key and not value and not operation):
            return self._get_config(key)
        elif operation == "set" or (key and value):
            return self._set_config(key, value)
        elif operation == "unset":
            return self._unset_config(key)
        else:
            print("Error: Unknown config operation", file=sys.stderr)
            return 1
    
    def _list_config(self) -> int:
        """List all configuration values.
        
        Returns
        -------
        int
            Exit code (0 for success)
        """
        items = self.config.list()
        for k, v in items.items():
            print(f"{k}={v}")
        return 0
    
    def _get_config(self, key: str) -> int:
        """Get a configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key to retrieve
            
        Returns
        -------
        int
            Exit code (0 for success, 1 for failure)
        """
        if not key:
            print("Error: key required for get operation", file=sys.stderr)
            return 1
        
        value_result = self.config.get(key)
        if value_result is None:
            print(f"{key} is not set", file=sys.stderr)
            return 1
        else:
            print(value_result)
            return 0
    
    def _set_config(self, key: str, value: str) -> int:
        """Set a configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key to set
        value : str
            Configuration value to set
            
        Returns
        -------
        int
            Exit code (0 for success, 1 for failure)
        """
        if not key or not value:
            print("Error: both key and value required for set operation", file=sys.stderr)
            return 1
        
        try:
            self.config.set(key, value)
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _unset_config(self, key: str) -> int:
        """Remove a configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key to remove
            
        Returns
        -------
        int
            Exit code (0 for success, 1 for failure)
        """
        if not key:
            print("Error: key required for unset operation", file=sys.stderr)
            return 1
        
        self.config.unset(key)
        return 0