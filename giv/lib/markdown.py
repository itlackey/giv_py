"""
Markdown processing and manipulation utilities.

This module provides comprehensive markdown processing functionality that
mirrors the original Bash implementation. It includes functions for:
- Header manipulation
- Code fence processing  
- Section extraction and management
- Link appending
- General post-processing

The functionality matches the Bash version exactly to ensure 100% compatibility.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


class MarkdownProcessor:
    """Markdown processing and manipulation operations.
    
    This class performs comprehensive transformations on markdown text and files,
    matching the original Bash implementation behavior exactly.
    """

    # Regex patterns
    code_fence_re = re.compile(r"```.*?```", re.DOTALL)
    top_header_re = re.compile(r"^#\s.*$", re.MULTILINE)
    
    @staticmethod
    def print_md_file(file_path: str) -> None:
        """Print markdown file using Glow if available, otherwise cat."""
        import shutil
        import subprocess
        import sys
        
        if sys.stdout.isatty() and shutil.which("glow"):
            subprocess.run(["glow", "-p", file_path])
        else:
            with open(file_path, 'r') as f:
                print(f.read(), end='')

    @staticmethod
    def remove_top_level_header(text: str) -> str:
        """Remove the first H1 heading from the document if present."""
        lines = text.splitlines(keepends=True)
        if lines and lines[0].lstrip().startswith("# "):
            return ''.join(lines[1:])
        return text

    @staticmethod
    def strip_code_fences(text: str) -> str:
        """Remove triple backtick code fences from first and last line if present."""
        lines = text.splitlines()
        if not lines:
            return text
            
        # Handle single line code fences (e.g. ```Code```)
        processed_lines = []
        for line in lines:
            if line.startswith('```') and line.endswith('```') and len(line) > 6:
                # Extract content between fences
                content = line[3:-3]
                processed_lines.append(content)
            else:
                processed_lines.append(line)
        
        # Remove code fence if first line is only ```
        if processed_lines and processed_lines[0].strip() == '```':
            processed_lines = processed_lines[1:]
            
        # Remove code fence if last line is only ```  
        if processed_lines and processed_lines[-1].strip() == '```':
            processed_lines = processed_lines[:-1]
            
        return '\n'.join(processed_lines)

    @staticmethod
    def enforce_final_newline(text: str) -> str:
        """Ensure the text ends with exactly one newline."""
        if not text:
            return text
        if not text.endswith('\n'):
            return text + '\n'
        return text

    @staticmethod
    def post_process_document(text: str) -> str:
        """Apply all post-processing steps to text."""
        text = MarkdownProcessor.remove_top_level_header(text)
        text = MarkdownProcessor.strip_code_fences(text)
        text = MarkdownProcessor.normalize_blank_lines(text)
        return text

    @staticmethod
    def strip_markdown(text: str) -> str:
        """Strip markdown formatting and return plain text."""
        lines = text.splitlines()
        processed_lines = []
        
        for line in lines:
            # Skip code fence lines
            if line.strip().startswith('```'):
                continue
                
            # Remove images: ![alt](url)
            line = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', line)
            
            # Remove links but keep text: [text](url) -> text
            line = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', line)
            
            # Remove backticks
            line = line.replace('`', '')
            
            # Remove bold: **text** -> text
            line = re.sub(r'\*\*([^*]*)\*\*', r'\1', line)
            
            # Remove italic: *text* -> text  
            line = re.sub(r'\*([^*]*)\*', r'\1', line)
            
            # Remove headers: ### text -> text
            line = re.sub(r'^[\s]*#+[\s]*', '', line)
            
            # Remove blockquotes: > text -> text
            line = re.sub(r'^[\s]*>[\s]*', '', line)
            
            processed_lines.append(line)
            
        return '\n'.join(processed_lines)

    @staticmethod
    def normalize_blank_lines(text: str) -> str:
        """Collapse multiple blank lines to one, ensure exactly one blank at EOF."""
        if not text:
            return text
            
        lines = text.splitlines()
        normalized_lines = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            
            if is_blank:
                if not prev_blank:
                    normalized_lines.append('')
                prev_blank = True
            else:
                normalized_lines.append(line)
                prev_blank = False
        
        # Ensure exactly one blank line at end if there was content
        if normalized_lines and not prev_blank:
            normalized_lines.append('')
            
        return '\n'.join(normalized_lines)

    @staticmethod
    def extract_section(section_name: str, file_path: str, header: str = "##") -> str:
        """Extract a section from a markdown file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            return ""
            
        lines = content.splitlines()
        
        # Escape section name for regex
        escaped_section = re.escape(section_name)
        
        # Build pattern to find the heading line
        header_pattern = re.compile(rf"^{re.escape(header)}\s*\[?{escaped_section}\]?")
        
        # Find the starting line
        start_line = None
        for i, line in enumerate(lines):
            if header_pattern.match(line):
                start_line = i
                break
                
        if start_line is None:
            return ""
            
        # Count header level
        header_level = len(header)
        
        # Find the end line (next header of same or higher level)
        end_line = len(lines)
        level_pattern = re.compile(rf"^#{{{1},{header_level}}}\s")
        
        for i in range(start_line + 1, len(lines)):
            if level_pattern.match(lines[i]):
                end_line = i
                break
                
        # Return the section
        return '\n'.join(lines[start_line:end_line])

    @staticmethod
    def manage_section(title: str, file_path: str, new_content: str, mode: str, 
                      section: str, header: str = "##") -> str:
        """Manage sections within a markdown file."""
        # Read original content or empty if missing
        try:
            with open(file_path, 'r') as f:
                orig_content = f.read()
            orig_lines = orig_content.splitlines()
        except FileNotFoundError:
            orig_content = ""
            orig_lines = []
            
        # If mode=update but no existing header, fall back to prepend
        section_pattern = re.compile(rf"^{re.escape(header)}\s*{re.escape(section)}(\s|$)")
        has_section = any(section_pattern.match(line) for line in orig_lines)
        
        if mode == "update" and not has_section:
            mode = "prepend"
            
        if mode == "append":
            result_lines = orig_lines.copy()
            result_lines.extend([
                "",
                f"{header} {section}",
                "",
                new_content
            ])
            
        elif mode == "prepend":
            result_lines = []
            
            # Find title line
            title_line = None
            for i, line in enumerate(orig_lines):
                if line.strip() == title.strip():
                    title_line = i
                    break
                    
            if title_line is None:
                # No title found, insert at top
                result_lines = [
                    title,
                    "",
                    f"{header} {section}",
                    "",
                    new_content
                ] + orig_lines
            else:
                # Find insertion point (first same-level header after title)
                header_level = len(header)
                header_pattern = re.compile(rf"^{re.escape(header)}\s")
                
                ins_point = title_line + 1
                for i in range(title_line + 1, len(orig_lines)):
                    if header_pattern.match(orig_lines[i]):
                        ins_point = i
                        break
                        
                # Build result
                result_lines = orig_lines[:ins_point]
                if result_lines and result_lines[-1].strip():
                    result_lines.append("")  # Blank line before new section
                result_lines.extend([
                    f"{header} {section}",
                    "",
                    new_content
                ])
                if not new_content.endswith('\n'):
                    result_lines.append("")
                result_lines.extend(orig_lines[ins_point:])
                
        elif mode == "update":
            result_lines = []
            header_level = len(header)
            in_section = False
            done = False
            
            for line in orig_lines:
                # Start of target section?
                if not done and not in_section and section_pattern.match(line):
                    result_lines.extend([line, "", new_content])
                    in_section = True
                    done = True
                    continue
                    
                # Skip old section content
                if in_section:
                    if re.match(r'^#+', line):
                        # Check if this is a header of same or higher level
                        level_match = re.match(r'^(#+)', line)
                        if level_match and len(level_match.group(1)) <= header_level:
                            in_section = False
                            result_lines.append(line)
                    continue
                    
                result_lines.append(line)
                
        else:
            raise ValueError(f"Invalid mode: {mode}")
            
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            content = '\n'.join(result_lines)
            content = MarkdownProcessor.normalize_blank_lines(content)
            f.write(content)
            return f.name

    @staticmethod
    def append_link(file_path: str, title: str, url: str) -> bool:
        """Append a link to a markdown file."""
        if not url:
            print(f"DEBUG: append_link: URL is empty, skipping", file=sys.stderr)
            return True
            
        link = f"[{title}]({url})"
        
        # Check if link already exists
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            if link in content:
                print(f"DEBUG: append_link: Link already exists: {link}", file=sys.stderr)
                return True
        except FileNotFoundError:
            content = ""
            print(f"DEBUG: append_link: File {file_path} does not exist; creating", file=sys.stderr)
            
        lines = content.splitlines() if content else []
        
        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()
            
        # Add blank line if there was existing content
        if lines:
            lines.append("")
            
        # Append the link and blank line
        lines.extend([link, ""])
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
            
        print(f"DEBUG: append_link: Appended link: {link} to {file_path}", file=sys.stderr)
        return True

    def extract_content(self, content: str, section_name: str) -> str:
        """Extract content from a specific section in markdown."""
        lines = content.splitlines()
        section_found = False
        section_lines = []
        current_level = None
        
        for line in lines:
            # Check if this is a header
            if line.strip().startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('#').strip()
                
                if header_text.lower() == section_name.lower():
                    section_found = True
                    current_level = header_level
                    continue
                elif section_found:
                    # If we find another header at the same or higher level, stop
                    if header_level <= current_level:
                        break
            
            # Add lines if we're in the target section
            if section_found:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()

    def generate_toc(self, content: str) -> str:
        """Generate a table of contents from markdown headers."""
        lines = content.splitlines()
        toc_lines = []
        
        for line in lines:
            if line.strip().startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('#').strip()
                
                # Create anchor link (convert to lowercase, replace spaces with hyphens)
                anchor = header_text.lower().replace(' ', '-').replace('/', '').replace('?', '').replace('!', '')
                anchor = re.sub(r'[^\w\-]', '', anchor)
                
                # Create indentation based on header level
                indent = '  ' * (header_level - 1)
                toc_line = f"{indent}- [{header_text}](#{anchor})"
                toc_lines.append(toc_line)
        
        return '\n'.join(toc_lines)

    def fix_relative_links(self, content: str, base_path: str) -> str:
        """Fix relative links in markdown content."""
        import posixpath
        
        # Pattern to match markdown links: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        def fix_link(match):
            text = match.group(1)
            url = match.group(2)
            
            # Skip absolute URLs (http/https/ftp/mailto)
            if re.match(r'^(https?|ftp|mailto):', url):
                return match.group(0)
            
            # Skip anchor links
            if url.startswith('#'):
                return match.group(0)
            
            # Convert relative path to absolute using POSIX paths (for markdown consistency)
            if not url.startswith('/'):
                # Use posixpath to maintain forward slashes regardless of OS
                fixed_url = posixpath.normpath(posixpath.join(base_path, url))
                return f'[{text}]({fixed_url})'
            
            return match.group(0)
        
        return re.sub(link_pattern, fix_link, content)

    def manage_sections(self, content: str, section_name: str, new_content: str, action: str) -> str:
        """Manage sections in markdown content (replace, append, etc.)."""
        lines = content.splitlines()
        result_lines = []
        section_found = False
        current_level = None
        section_start = None
        section_end = None
        
        # Find the section
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                header_level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('#').strip()
                
                if header_text.lower() == section_name.lower():
                    section_found = True
                    current_level = header_level
                    section_start = i
                    continue
                elif section_found:
                    # If we find another header at the same or higher level, end section
                    if header_level <= current_level:
                        section_end = i
                        break
        
        if not section_found:
            # Section doesn't exist, add it at the end
            if action in ['replace', 'append']:
                result_lines = lines[:]
                if result_lines and result_lines[-1].strip():
                    result_lines.append('')
                result_lines.append(f'# {section_name}')
                result_lines.append('')
                result_lines.extend(new_content.splitlines())
                return '\n'.join(result_lines)
        else:
            # Section exists
            if section_end is None:
                section_end = len(lines)
            
            result_lines = lines[:section_start]
            
            if action == 'replace':
                result_lines.append(f'# {section_name}')
                result_lines.append('')
                result_lines.extend(new_content.splitlines())
            elif action == 'append':
                # Keep existing section and append new content
                result_lines.extend(lines[section_start:section_end])
                if result_lines and result_lines[-1].strip():
                    result_lines.append('')
                result_lines.extend(new_content.splitlines())
            
            # Add remaining content after the section
            if section_end < len(lines):
                if result_lines and result_lines[-1].strip():
                    result_lines.append('')
                result_lines.extend(lines[section_end:])
        
        return '\n'.join(result_lines)

    def clean_markdown(self, content: str) -> str:
        """Clean up markdown formatting issues."""
        lines = content.splitlines()
        cleaned_lines = []
        in_code_block = False
        
        prev_line_blank = True
        
        for line in lines:
            stripped = line.strip()
            
            # Track code block state
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                cleaned_lines.append(line)
                prev_line_blank = False
                continue
            
            # Don't modify lines inside code blocks
            if in_code_block:
                cleaned_lines.append(line)
                prev_line_blank = False
                continue
            
            # Remove multiple consecutive blank lines
            if not stripped:
                if prev_line_blank:
                    continue
                prev_line_blank = True
            else:
                prev_line_blank = False
            
            # Clean up header formatting
            if stripped.startswith('#'):
                # Ensure single space after # symbols
                level = len(stripped) - len(stripped.lstrip('#'))
                header_text = stripped.lstrip('#').strip()
                # Normalize spaces in header text
                header_text = re.sub(r'\s+', ' ', header_text)
                line = '#' * level + ' ' + header_text
            
            # Clean up list formatting
            elif re.match(r'^\s*[\-\*\+]\s+', line):
                # Ensure consistent list formatting
                indent_match = re.match(r'^(\s*)', line)
                indent = indent_match.group(1) if indent_match else ''
                list_content = re.sub(r'^(\s*[\-\*\+]\s+)', '- ', line.lstrip())
                # Normalize spaces in list content
                list_content = re.sub(r'\s+', ' ', list_content.rstrip())
                line = indent + list_content
            
            # Clean up regular text lines (normalize multiple spaces)
            else:
                # Preserve leading whitespace but normalize internal spaces
                leading_space = len(line) - len(line.lstrip())
                if leading_space > 0:
                    line = ' ' * leading_space + re.sub(r'\s+', ' ', line.lstrip().rstrip())
                else:
                    line = re.sub(r'\s+', ' ', line.strip())
            
            cleaned_lines.append(line)
        
        # Remove trailing blank lines
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)