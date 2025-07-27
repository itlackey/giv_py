"""
Configuration management for giv_cli.

This module provides comprehensive configuration management that matches the
Bash implementation exactly, including:
- Configuration hierarchy (project .giv/config > user ~/.giv/config)
- Environment variable integration with GIV_* prefix
- Dot-notation key normalization (api.key → GIV_API_KEY)
- Configuration validation and merging
- Support for quoted values and special characters
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Optional, Union


class ConfigManager:
    """Manage persistent configuration for giv with full Bash compatibility.

    Parameters
    ----------
    config_path: Optional[Path]
        Override the default path to the configuration file.  When ``None``,
        the manager will search for `.giv/config` in the current working
        directory and fall back to `$HOME/.giv/config`.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        if config_path is not None:
            self.path = config_path
        else:
            # Search hierarchy: project .giv/config -> user ~/.giv/config
            self.path = self._find_config_file()
        
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        """Get the configuration file path for backward compatibility."""
        return self.path

    def _find_config_file(self) -> Path:
        """Find configuration file using Bash-compatible search hierarchy."""
        # 1. Look for project-level .giv/config (walk up directory tree)
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            project_cfg = current_dir / ".giv" / "config"
            if project_cfg.exists():
                return project_cfg
            current_dir = current_dir.parent

        # 2. Fall back to user-level config
        home = Path(os.environ.get("HOME", "~")).expanduser()
        return home / ".giv" / "config"

    def _normalize_key(self, key: str) -> str:
        """Normalize dot-notation keys to GIV_* environment variable format."""
        if "/" in key:
            # Reject keys with slashes (Bash compatibility)
            return ""
        
        if key.startswith("GIV_"):
            return key
        
        # Convert dot notation to GIV_* format: api.key -> GIV_API_KEY
        return f"GIV_{key.replace('.', '_').upper()}"

    def _denormalize_key(self, env_key: str) -> str:
        """Convert GIV_* environment key back to dot notation."""
        if env_key.startswith("GIV_"):
            # Remove GIV_ prefix and convert to lowercase with dots
            return env_key[4:].lower().replace("_", ".")
        return env_key

    def _quote_value(self, value: str) -> str:
        """Quote value if it contains spaces, special characters, or is empty."""
        if not value or " " in value or any(c in value for c in ['"', "'", '`', '$', '\\']):
            return f'"{value}"'
        return value

    def _unquote_value(self, value: str) -> str:
        """Remove surrounding quotes from value."""
        value = value.strip()
        if ((value.startswith('"') and value.endswith('"')) or 
            (value.startswith("'") and value.endswith("'"))):
            return value[1:-1]
        return value

    def _parse_config_file(self) -> Dict[str, str]:
        """Parse the configuration file into a dictionary."""
        data: Dict[str, str] = {}
        if not self.path.exists():
            return data

        try:
            content = self.path.read_text(encoding="utf-8")
        except Exception:
            return data

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Validate line format
            if "=" not in line:
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = self._unquote_value(value)
            
            if key:
                data[key] = value

        return data

    def _get_from_environment(self, key: str) -> Optional[str]:
        """Get value from environment variables with GIV_* prefix."""
        env_key = self._normalize_key(key)
        if env_key:
            return os.environ.get(env_key)
        return None

    def _write_config_file(self, data: Dict[str, str]) -> None:
        """Write the configuration dictionary back to disk."""
        lines = []
        for key, value in sorted(data.items()):
            quoted_value = self._quote_value(value)
            lines.append(f"{key}={quoted_value}")
        
        content = "\n".join(lines)
        if content:
            content += "\n"
        
        self.path.write_text(content, encoding="utf-8")

    def list(self) -> Dict[str, str]:
        """Return all key–value pairs from config file and environment.
        
        Environment variables take precedence over config file values.
        """
        # Start with config file data
        config_data = self._parse_config_file()
        result = {}
        
        # Add config file entries, converting GIV_* keys to dot notation for output
        for key, value in config_data.items():
            if key.startswith("GIV_"):
                display_key = self._denormalize_key(key)
            else:
                display_key = key
            result[display_key] = value
        
        # Override with environment variables
        for env_key, env_value in os.environ.items():
            if env_key.startswith("GIV_"):
                display_key = self._denormalize_key(env_key)
                result[display_key] = env_value
        
        return result

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve value with precedence: environment > config file > default."""
        # First check environment variables
        env_value = self._get_from_environment(key)
        if env_value is not None:
            return env_value
        
        # Then check config file
        config_data = self._parse_config_file()
        
        # Try exact key match first
        if key in config_data:
            return config_data[key]
        
        # Try GIV_* normalized version
        normalized_key = self._normalize_key(key)
        if normalized_key and normalized_key in config_data:
            return config_data[normalized_key]
        
        return default

    def set(self, key: str, value: str) -> None:
        """Set ``key`` to ``value`` in the configuration file."""
        if "/" in key:
            raise ValueError(f"Invalid key format: {key}")
        
        config_data = self._parse_config_file()
        
        # Always store in normalized GIV_* format for consistency
        normalized_key = self._normalize_key(key)
        if normalized_key:
            # Remove any existing entries for this key (both formats)
            config_data.pop(key, None)
            config_data.pop(normalized_key, None)
            # Set the normalized version
            config_data[normalized_key] = value
        else:
            config_data[key] = value
        
        self._write_config_file(config_data)

    def unset(self, key: str) -> None:
        """Remove ``key`` from the configuration file if present."""
        config_data = self._parse_config_file()
        
        # Remove both normalized and non-normalized versions
        removed = False
        if key in config_data:
            del config_data[key]
            removed = True
        
        normalized_key = self._normalize_key(key)
        if normalized_key and normalized_key in config_data:
            del config_data[normalized_key]
            removed = True
        
        if removed:
            self._write_config_file(config_data)