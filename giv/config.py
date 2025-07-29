"""
Configuration management for giv.

This module provides comprehensive configuration management with proper hierarchy:
- Configuration hierarchy (project .giv/config > user ~/.giv/config > environment)
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
        
        # Initialize cache for performance optimization
        self._config_cache: Optional[Dict[str, str]] = None
        self._cache_mtime: Optional[float] = None

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
        # Check for HOME first (Unix/testing), then USERPROFILE (Windows), then use Path.home()
        home_env = os.environ.get("HOME") or os.environ.get("USERPROFILE")
        if home_env:
            # Environment variable was explicitly set, use it
            home = Path(home_env)
        else:
            # Use pathlib's home directory resolution which handles Windows correctly
            home = Path.home()
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
        """Quote a configuration value if necessary."""
        # Don't quote simple values without special characters
        if not any(char in value for char in [' ', '"', "'", '\n', '\t', '=']):
            return value
        
        # Use double quotes for values with special characters
        # Escape existing double quotes and preserve newlines as literal \n
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f'"{escaped}"'

    def _unquote_value(self, value: str) -> str:
        """Remove surrounding quotes from value and handle escape sequences."""
        value = value.strip()
        if ((value.startswith('"') and value.endswith('"')) or 
            (value.startswith("'") and value.endswith("'"))):
            unquoted = value[1:-1]
            # Handle escape sequences in double-quoted strings
            if value.startswith('"'):
                unquoted = unquoted.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            return unquoted
        return value

    def _get_cached_config(self) -> Dict[str, str]:
        """Get configuration with caching for performance optimization."""
        if not self.path.exists():
            return {}
        
        try:
            # Check if cache is valid by comparing modification time
            current_mtime = self.path.stat().st_mtime
            if (self._config_cache is not None and 
                self._cache_mtime is not None and 
                self._cache_mtime == current_mtime):
                # Cache is valid, return cached data
                return self._config_cache
            
            # Cache is invalid or doesn't exist, reload from file
            self._config_cache = self._parse_config_file()
            self._cache_mtime = current_mtime
            return self._config_cache
            
        except (OSError, IOError):
            # If we can't stat the file, return empty config
            return {}
    
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
        """Write the configuration dictionary back to disk, preserving comments."""
        lines = []
        
        # Try to preserve existing structure if file exists
        existing_lines = []
        if self.path.exists():
            try:
                existing_lines = self.path.read_text(encoding="utf-8").splitlines()
            except Exception:
                pass
        
        # Keep track of which keys we've written
        written_keys = set()
        
        # First pass: process existing lines, updating values as needed
        for line in existing_lines:
            stripped = line.strip()
            
            # Preserve comments and empty lines
            if not stripped or stripped.startswith("#"):
                lines.append(line)
                continue
            
            # Process existing key-value pairs
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in data:
                    # Update existing key with new escaped value
                    quoted_value = self._quote_value(data[key])
                    lines.append(f"{key}={quoted_value}")
                    written_keys.add(key)
                # If key not in data, skip the line (effectively removing it)
            else:
                # Keep malformed lines as-is
                lines.append(line)
        
        # Second pass: add any new keys that weren't in the original file
        for key, value in sorted(data.items()):
            if key not in written_keys:
                quoted_value = self._quote_value(value)
                lines.append(f"{key}={quoted_value}")
        
        # Write the result
        content = "\n".join(lines)
        if content and not content.endswith("\n"):
            content += "\n"
        
        self.path.write_text(content, encoding="utf-8")

    def list(self) -> Dict[str, str]:
        """Return all key–value pairs from config file and environment.
        
        Environment variables override config file values in display only.
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
        """Retrieve value with precedence: config file > environment > default."""
        # First check config file (now with caching for performance)
        config_data = self._get_cached_config()
        
        # Try exact key match first
        if key in config_data:
            return config_data[key]
        
        # Try GIV_* normalized version
        normalized_key = self._normalize_key(key)
        if normalized_key and normalized_key in config_data:
            return config_data[normalized_key]
        
        # Then check environment variables
        env_value = self._get_from_environment(key)
        if env_value is not None:
            return env_value
        
        return default

    def set(self, key: str, value: str) -> None:
        """Set ``key`` to ``value`` in the configuration file."""
        if "/" in key:
            raise ValueError(f"Invalid key format: {key}")
        
        config_data = self._parse_config_file()
        normalized_key = self._normalize_key(key)
        
        # Preserve existing key format if present, otherwise use normalized format
        if key in config_data:
            # Key exists in dot notation - preserve the format
            config_data.pop(normalized_key, None)  # Remove normalized version if it exists
            config_data[key] = value
        elif normalized_key and normalized_key in config_data:
            # Key exists in normalized format - preserve that format
            config_data.pop(key, None)  # Remove dot notation version if it exists
            config_data[normalized_key] = value
        else:
            # New key - use normalized format for consistency
            if normalized_key:
                config_data[normalized_key] = value
            else:
                config_data[key] = value
        
        self._write_config_file(config_data)
        # Invalidate cache after writing
        self._config_cache = None
        self._cache_mtime = None

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
            # Invalidate cache after writing
            self._config_cache = None
            self._cache_mtime = None