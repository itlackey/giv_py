"""
Constants for giv CLI application.

This module contains all default values, magic numbers, and configuration
constants used throughout the application.
"""
from __future__ import annotations

# Default LLM settings
DEFAULT_TEMPERATURE = 0.9
DEFAULT_MAX_TOKENS = 8192
DEFAULT_API_TIMEOUT = 30

# Command-specific temperature defaults
TEMPERATURE_CREATIVE = 0.9  # For messages, summaries, announcements, documents
TEMPERATURE_FACTUAL = 0.7   # For changelogs, release notes

# Output file defaults
DEFAULT_CHANGELOG_FILE = "CHANGELOG.md"
DEFAULT_RELEASE_NOTES_FILE = "RELEASE_NOTES.md"
DEFAULT_ANNOUNCEMENT_FILE = "ANNOUNCEMENT.md"

# Configuration keys
CONFIG_API_URL = "api_url"
CONFIG_API_KEY = "api_key"
CONFIG_API_MODEL = "api_model"
CONFIG_TEMPERATURE = "temperature"
CONFIG_MAX_TOKENS = "max_tokens"
CONFIG_OUTPUT_MODE = "output_mode"
CONFIG_OUTPUT_VERSION = "output_version"
CONFIG_CHANGELOG_FILE = "changelog_file"
CONFIG_RELEASE_NOTES_FILE = "release_notes_file"
CONFIG_ANNOUNCEMENT_FILE = "announcement_file"

# Git revision defaults
DEFAULT_REVISION = "--current"

# Template names
TEMPLATE_MESSAGE = "message_prompt.md"
TEMPLATE_SUMMARY = "final_summary_prompt.md"
TEMPLATE_CHANGELOG = "changelog_prompt.md"
TEMPLATE_RELEASE_NOTES = "release_notes_prompt.md"
TEMPLATE_ANNOUNCEMENT = "announcement_prompt.md"

# Output modes
OUTPUT_MODE_AUTO = "auto"
OUTPUT_MODE_APPEND = "append"
OUTPUT_MODE_PREPEND = "prepend"
OUTPUT_MODE_UPDATE = "update"
OUTPUT_MODE_OVERWRITE = "overwrite"

# Buffer sizes for file operations
BUFFER_SIZE_DEFAULT = 4096
BUFFER_SIZE_LARGE = 8192
BUFFER_SIZE_SMALL = 2048

# Environment variable prefixes
ENV_PREFIX = "GIV_"

# Default directory names
CONFIG_DIR = ".giv"
TEMPLATES_DIR = "templates"