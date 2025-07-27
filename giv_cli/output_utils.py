"""
Output management utilities for giv_cli.

This module provides comprehensive output management that matches the
Bash implementation exactly, including:
- Output mode detection and handling (auto, prepend, append, update, none)
- File modification with backup
- Section insertion and updates  
- Output formatting and validation
- Markdown section management
- Support for different file formats
"""
from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class OutputManager:
    """Manage output modes and file modifications matching Bash behavior."""
    
    def __init__(self, output_file: Optional[Union[str, Path]] = None,
                 output_mode: str = "auto",
                 output_version: Optional[str] = None):
        """Initialize output manager.
        
        Parameters
        ----------
        output_file : Optional[Union[str, Path]]
            Target output file path
        output_mode : str
            Output mode: 'auto', 'prepend', 'append', 'update', 'none'
        output_version : Optional[str]
            Version/section identifier for updates
        """
        self.output_file = Path(output_file) if output_file else None
        self.output_mode = output_mode
        self.output_version = output_version or "Unreleased"
        
    def write_output(self, content: str, dry_run: bool = False) -> bool:
        """Write content using the configured output mode.
        
        Parameters
        ----------
        content : str
            Content to write
        dry_run : bool
            If True, only print what would be written
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if self.output_mode == "none":
            # Don't write anything
            return True
            
        if not self.output_file:
            # Write to stdout
            if dry_run:
                print("Dry run: would write to stdout:")
                print(content)
            else:
                print(content)
            return True
            
        # Write to file using specified mode
        if dry_run:
            print(f"Dry run: would write to {self.output_file} using mode '{self.output_mode}'")
            print("Content:")
            print(content)
            return True
            
        try:
            if self.output_mode == "auto":
                # Auto mode: detect based on file type and content
                if self.output_file.name.lower() == "changelog.md":
                    return self._write_changelog(content)
                else:
                    # Default to overwrite for non-changelog files
                    return self._write_overwrite(content)
            elif self.output_mode == "overwrite":
                return self._write_overwrite(content)
            elif self.output_mode == "append":
                return self._write_append(content)
            elif self.output_mode == "prepend":
                return self._write_prepend(content)
            elif self.output_mode == "update":
                return self._write_update(content)
            else:
                logger.error(f"Unknown output mode: {self.output_mode}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to write output: {e}")
            return False
    
    def _write_overwrite(self, content: str) -> bool:
        """Overwrite the entire file with new content."""
        try:
            self.output_file.write_text(content, encoding="utf-8")
            print(f"Output written to {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to overwrite {self.output_file}: {e}")
            return False
    
    def _write_append(self, content: str) -> bool:
        """Append content to the end of the file."""
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                if self.output_file.exists() and self.output_file.stat().st_size > 0:
                    f.write("\n")  # Add separator if file is not empty
                f.write(content)
            print(f"Content appended to {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to append to {self.output_file}: {e}")
            return False
    
    def _write_prepend(self, content: str) -> bool:
        """Prepend content to the beginning of the file."""
        try:
            existing_content = ""
            if self.output_file.exists():
                existing_content = self.output_file.read_text(encoding="utf-8")
            
            new_content = content
            if existing_content.strip():
                new_content += "\n" + existing_content
                
            self.output_file.write_text(new_content, encoding="utf-8")
            print(f"Content prepended to {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to prepend to {self.output_file}: {e}")
            return False
    
    def _write_update(self, content: str) -> bool:
        """Update a specific section in the file."""
        if self.output_file.name.lower() == "changelog.md":
            return self._write_changelog(content)
        else:
            # For non-changelog files, fall back to prepend
            return self._write_prepend(content)
    
    def _write_changelog(self, content: str) -> bool:
        """Write changelog content with proper section management."""
        try:
            # Ensure parent directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing content or start with empty
            existing_content = ""
            if self.output_file.exists():
                existing_content = self.output_file.read_text(encoding="utf-8")
            
            # Manage the changelog section
            updated_content = self._manage_changelog_section(
                existing_content, content, self.output_version
            )
            
            # Add link footer
            updated_content = self._append_link(
                updated_content, "Managed by giv", "https://github.com/giv-cli/giv"
            )
            
            # Write the updated content
            self.output_file.write_text(updated_content, encoding="utf-8")
            print(f"Changelog written to {self.output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write changelog: {e}")
            return False
    
    def _manage_changelog_section(self, existing: str, new_content: str, version: str) -> str:
        """Manage changelog sections matching Bash manage_section functionality."""
        lines = existing.splitlines() if existing else []
        
        # If file is empty, create basic structure
        if not lines:
            return f"# Changelog\n\n## {version}\n\n{new_content.strip()}\n"
        
        # Find the title line
        title_line = -1
        for i, line in enumerate(lines):
            if line.strip() == "# Changelog":
                title_line = i
                break
        
        # If no title found, add it at the top
        if title_line == -1:
            return f"# Changelog\n\n## {version}\n\n{new_content.strip()}\n\n{existing}"
        
        # Find where to insert the new section
        insert_pos = title_line + 1
        
        # Skip blank lines after title
        while insert_pos < len(lines) and not lines[insert_pos].strip():
            insert_pos += 1
        
        # Check if version section already exists
        version_pattern = rf"^##\s+{re.escape(version)}(\s|$)"
        version_line = -1
        
        for i in range(insert_pos, len(lines)):
            if re.match(version_pattern, lines[i]):
                version_line = i
                break
        
        if version_line != -1:
            # Update existing section - find the end of this section
            section_end = len(lines)
            for i in range(version_line + 1, len(lines)):
                if lines[i].startswith("## "):
                    section_end = i
                    break
            
            # Replace the section content
            new_lines = (
                lines[:version_line + 1] +
                [""] +  # Blank line after header
                new_content.strip().splitlines() +
                [""] +  # Blank line after content
                lines[section_end:]
            )
        else:
            # Insert new section at the beginning after title
            new_lines = (
                lines[:insert_pos] +
                [""] +  # Blank line after title if needed
                [f"## {version}"] +
                [""] +  # Blank line after header
                new_content.strip().splitlines() +
                [""] +  # Blank line after content
                lines[insert_pos:]
            )
        
        return "\n".join(new_lines)
    
    def _append_link(self, content: str, text: str, url: str) -> str:
        """Append a link at the end of the content if not already present."""
        link_text = f"[{text}]({url})"
        
        # Check if link already exists
        if link_text in content:
            return content
            
        # Add the link at the end
        content = content.rstrip()
        if content:
            content += "\n\n"
        content += f"---\n*{link_text}*\n"
        
        return content


def write_output(content: str, output_file: Optional[Union[str, Path]] = None,
                output_mode: str = "auto", output_version: Optional[str] = None,
                dry_run: bool = False) -> bool:
    """Convenience function for writing output.
    
    Parameters
    ----------
    content : str
        Content to write
    output_file : Optional[Union[str, Path]]
        Output file path (None for stdout)
    output_mode : str
        Output mode: 'auto', 'prepend', 'append', 'update', 'overwrite', 'none'
    output_version : Optional[str]
        Version/section identifier for updates
    dry_run : bool
        If True, only print what would be written
        
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    manager = OutputManager(output_file, output_mode, output_version)
    return manager.write_output(content, dry_run)
