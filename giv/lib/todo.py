"""
TODO scanning and extraction utilities.

This module provides functionality to scan files for TODO, FIXME, and other
comment patterns and extract them for inclusion in generated content.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fnmatch
import logging

logger = logging.getLogger(__name__)


class TodoScanner:
    """Scanner for extracting TODO items from source files."""
    
    # Default patterns from specification
    DEFAULT_TODO_PATTERN = r"TODO|FIXME|XXX"
    DEFAULT_TODO_FILES = "**/*"
    
    # Common binary file extensions to skip
    BINARY_EXTENSIONS = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.exe', '.bin', '.obj', '.o', '.a', '.lib',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.rar',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.ogg'
    }
    
    def __init__(self, pattern: Optional[str] = None, file_pattern: Optional[str] = None):
        """Initialize TODO scanner.
        
        Parameters
        ----------
        pattern : Optional[str]
            Regex pattern to match TODO items (default: TODO|FIXME|XXX)
        file_pattern : Optional[str]
            File glob pattern to scan (default: **/*) 
        """
        self.pattern = pattern or self.DEFAULT_TODO_PATTERN
        self.file_pattern = file_pattern or self.DEFAULT_TODO_FILES
        
        # Compile regex for performance
        try:
            self.regex = re.compile(self.pattern, re.IGNORECASE)
        except re.error as e:
            logger.warning(f"Invalid TODO pattern '{self.pattern}': {e}")
            self.regex = re.compile(self.DEFAULT_TODO_PATTERN, re.IGNORECASE)
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is likely binary and should be skipped."""
        if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
            
        # Check for binary content in first 1KB
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # If null bytes found, likely binary
                return b'\x00' in chunk
        except (OSError, PermissionError):
            return True
    
    def _matches_pattern(self, file_path: Path, base_path: Path) -> bool:
        """Check if file matches the file pattern."""
        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(base_path)
            path_str = str(rel_path).replace(os.sep, '/')
            
            # Handle glob patterns
            if '**' in self.file_pattern:
                return fnmatch.fnmatch(path_str, self.file_pattern)
            else:
                return fnmatch.fnmatch(path_str, self.file_pattern)
        except ValueError:
            return False
    
    def scan_file(self, file_path: Path) -> List[Tuple[int, str]]:
        """Scan a single file for TODO items.
        
        Parameters
        ----------
        file_path : Path
            Path to file to scan
            
        Returns
        -------
        List[Tuple[int, str]]
            List of (line_number, todo_text) tuples
        """
        todos = []
        
        if self._is_binary_file(file_path):
            return todos
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if self.regex.search(line):
                        # Clean up the line (remove extra whitespace)
                        clean_line = line.strip()
                        todos.append((line_num, clean_line))
        except (OSError, PermissionError, UnicodeDecodeError) as e:
            logger.debug(f"Could not scan file {file_path}: {e}")
        
        return todos
    
    def scan_directory(self, directory: Path = None) -> Dict[str, List[Tuple[int, str]]]:  
        """Scan directory for TODO items.
        
        Parameters
        ----------
        directory : Optional[Path]
            Directory to scan (default: current working directory)
            
        Returns  
        -------
        Dict[str, List[Tuple[int, str]]]
            Dictionary mapping file paths to lists of (line_number, todo_text) tuples
        """
        if directory is None:
            directory = Path.cwd()
            
        todos_by_file = {}
        
        # Handle different patterns
        if self.file_pattern == "**/*":
            # Recursive scan
            for file_path in directory.rglob("*"):
                if file_path.is_file() and not self._is_binary_file(file_path):
                    todos = self.scan_file(file_path)
                    if todos:
                        rel_path = str(file_path.relative_to(directory))
                        todos_by_file[rel_path] = todos
        else:
            # Pattern-based scan
            for file_path in directory.rglob("*"):
                if file_path.is_file() and self._matches_pattern(file_path, directory):
                    todos = self.scan_file(file_path)
                    if todos:
                        rel_path = str(file_path.relative_to(directory))
                        todos_by_file[rel_path] = todos
        
        return todos_by_file
    
    def format_todos(self, todos_by_file: Dict[str, List[Tuple[int, str]]]) -> str:
        """Format TODO items for inclusion in templates.
        
        Parameters
        ----------
        todos_by_file : Dict[str, List[Tuple[int, str]]]
            Dictionary from scan_directory()
            
        Returns
        -------
        str
            Formatted TODO items ready for template inclusion
        """
        if not todos_by_file:
            return ""
        
        lines = ["## TODO Items\n"]
        
        for file_path, todos in sorted(todos_by_file.items()):
            lines.append(f"### {file_path}")
            for line_num, todo_text in todos:
                lines.append(f"- Line {line_num}: {todo_text}")
            lines.append("")  # Empty line between files
        
        return "\n".join(lines)


def scan_todos(pattern: Optional[str] = None, file_pattern: Optional[str] = None, 
               directory: Optional[Path] = None) -> str:
    """Convenience function to scan and format TODO items.
    
    Parameters
    ----------
    pattern : Optional[str]
        Regex pattern to match TODO items
    file_pattern : Optional[str]
        File glob pattern to scan
    directory : Optional[Path]
        Directory to scan
        
    Returns
    -------
    str
        Formatted TODO items for template inclusion
    """
    scanner = TodoScanner(pattern, file_pattern)
    todos_by_file = scanner.scan_directory(directory)
    return scanner.format_todos(todos_by_file)