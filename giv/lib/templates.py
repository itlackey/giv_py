"""
Template system and rendering engine.

This module provides comprehensive template management that matches the
Bash implementation exactly, including:
- Template discovery (project .giv/templates > system templates)
- Token replacement engine supporting {{TOKEN}} format
- Template validation and error handling
- Template inheritance and overrides
- Support for all tokens used in Bash version
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..constants import TEMPLATES_DIR
from ..errors import TemplateError


class TemplateEngine:
    """Template discovery, loading, and rendering engine.
    
    This class provides a normalized interface to template operations,
    replacing the original TemplateManager class with more consistent naming.
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """Initialize template engine with optional custom template directory.
        
        Parameters
        ----------
        template_dir : Optional[Path]
            Custom template directory to search in addition to standard locations
        """
        self.template_dir = template_dir
        self._base_template_dir: Optional[Path] = None
        
        # Compile regex patterns for performance optimization
        self._brace_pattern = re.compile(r'\{([^{}]+)\}')
        self._bracket_pattern = re.compile(r'\[([^\[\]]+)\]')
        self._double_brace_pattern = re.compile(r'\{\{([^{}]+)\}\}')

    @property
    def base_template_dir(self) -> Path:
        """Get the base (system) template directory."""
        if self._base_template_dir is not None:
            return self._base_template_dir
        return Path(__file__).parent.parent / TEMPLATES_DIR

    @base_template_dir.setter
    def base_template_dir(self, value: Path) -> None:
        """Set the base template directory (mainly for testing)."""
        self._base_template_dir = value

    @base_template_dir.deleter
    def base_template_dir(self) -> None:
        """Delete the base template directory override."""
        self._base_template_dir = None

    def find_template_file(self, template_name: str) -> Path:
        """Alias for find_template() for backwards compatibility."""
        return self.find_template(template_name)

    def find_template(self, template_name: str) -> Path:
        """Find template file using Bash-compatible search hierarchy.
        
        Search order:
        1. Explicit path (if template_name is absolute/relative path)
        2. Custom template directory (if provided)
        3. Project-level .giv/templates/
        4. User-level ~/.giv/templates/
        5. System templates (bundled with package)
        
        Parameters
        ----------
        template_name : str
            Template filename or path
            
        Returns
        -------
        Path
            Path to the template file
            
        Raises
        ------
        FileNotFoundError
            If template cannot be found in any location
        """
        # 1. Security: Validate template name to prevent path traversal attacks
        if not self._is_safe_template_name(template_name):
            raise TemplateError(f"Invalid template name: {template_name}")
        
        # Handle explicit paths securely
        if template_name.startswith("/") or template_name.startswith("./") or template_name.startswith("../"):
            template_path = Path(template_name).resolve()
            
            # Security: Only allow absolute paths within safe directories
            safe_directories = [
                Path.home() / ".giv" / "templates",
                Path.cwd() / ".giv" / "templates"
            ]
            
            # Add current template directory if set
            if self.template_dir:
                safe_directories.append(self.template_dir.resolve())
            
            # Check if resolved path is within allowed directories
            is_safe = any(
                self._is_path_within_directory(template_path, safe_dir) 
                for safe_dir in safe_directories
            )
            
            if not is_safe:
                raise TemplateError(f"Template path not allowed: {template_path}")
            
            if template_path.exists():
                return template_path
            raise TemplateError(f"Template not found: {template_path}")

        # 2. Check custom template directory if provided (highest precedence)
        if self.template_dir:
            custom_template = self.template_dir / template_name
            if custom_template.exists():
                return custom_template

        # 3. Check project-level .giv/templates/
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            project_templates = current_dir / ".giv" / "templates" / template_name
            if project_templates.exists():
                return project_templates
            current_dir = current_dir.parent

        # 4. Check user-level ~/.giv/templates/
        home = Path.home()
        user_templates = home / ".giv" / "templates" / template_name
        if user_templates.exists():
            return user_templates

        # 5. Check system templates (bundled with package)
        system_templates = self.base_template_dir / template_name
        if system_templates.exists():
            return system_templates

        raise TemplateError(f"Template not found: {template_name}")

    def load_template(self, template_name: str) -> str:
        """Load template content from file.
        
        Parameters
        ----------
        template_name : str
            Template filename or path
            
        Returns
        -------
        str
            Template content
            
        Raises
        ------
        FileNotFoundError
            If template cannot be found
        """
        template_path = self.find_template(template_name)
        try:
            return template_path.read_text(encoding="utf-8")
        except (OSError, IOError, PermissionError) as e:
            raise TemplateError(f"Template not found: {e}")

    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template by replacing tokens with context values.
        
        Optimized single-pass implementation using regex substitution.
        Supports {TOKEN} and [TOKEN] formats for compatibility.
        Unknown tokens are left intact.
        
        Parameters
        ----------
        template_content : str
            Template content with tokens
        context : Dict[str, Any]
            Context values for token replacement
            
        Returns
        -------
        str
            Rendered template with tokens replaced
        """
        if not context:
            return template_content
        
        # Normalize context values to strings once
        normalized_context = {}
        for key, value in context.items():
            if value is None:
                normalized_context[key] = "None"
            elif not isinstance(value, str):
                normalized_context[key] = str(value)
            else:
                normalized_context[key] = value
        
        # Replace single braces but preserve double braces
        result = self._replace_tokens_optimized(template_content, normalized_context)
        
        # Replace [TOKEN] format (legacy compatibility) using regex
        def replace_bracket(match):
            token = match.group(1)
            return normalized_context.get(token, match.group(0))
        
        result = self._bracket_pattern.sub(replace_bracket, result)
        
        return result
    
    def _replace_tokens_optimized(self, content: str, context: Dict[str, str]) -> str:
        """Optimized token replacement handling single and double braces correctly."""
        # Use a single regex substitution with proper double-brace handling
        def replacer(match):
            full_match = match.group(0)
            
            # Check if this is part of a double brace pattern
            # Look backwards and forwards to detect double braces
            start = match.start()
            end = match.end()
            
            # Check for preceding and following braces
            if (start > 0 and content[start-1] == '{' and 
                end < len(content) and content[end] == '}'):
                # This is part of a double brace pattern, don't replace
                return full_match
            
            token = match.group(1)
            return context.get(token, full_match)
        
        return self._brace_pattern.sub(replacer, content)

    def render_template_file(self, template_name: str, context: Dict[str, Any]) -> str:
        """Load and render a template file.
        
        Parameters
        ----------
        template_name : str
            Template filename or path
        context : Dict[str, Any]
            Context values for token replacement
            
        Returns
        -------
        str
            Rendered template content
        """
        template_content = self.load_template(template_name)
        return self.render_template(template_content, context)

    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template and extract information about tokens.
        
        Parameters
        ----------
        template_content : str
            Template content to validate
            
        Returns
        -------
        Dict[str, Any]
            Validation results including found tokens and any issues
        """
        # Find all {TOKEN} patterns (single brace) - exclude double braces
        single_brace_tokens = re.findall(r'(?<!\{)\{([^{}]+)\}(?!\})', template_content)
        
        # Find all [TOKEN] patterns
        square_bracket_tokens = re.findall(r'\[([^]]+)\]', template_content)
        
        # Combine all tokens while preserving order and removing duplicates
        all_tokens = []
        seen = set()
        for token in single_brace_tokens + square_bracket_tokens:
            if token not in seen:
                all_tokens.append(token)
                seen.add(token)
        
        return {
            "single_brace_tokens": single_brace_tokens,
            "square_bracket_tokens": square_bracket_tokens,
            "tokens": all_tokens,
            "all_tokens": all_tokens,  # Keep for backward compatibility
            "valid": True,  # Basic validation - could be enhanced
            "is_valid": True,  # Keep for backward compatibility
            "issues": [],
            "errors": []  # Keep for backward compatibility
        }

    def list_available_templates(self) -> Dict[str, Path]:
        """List all available templates from all search locations.
        
        Returns
        -------
        Dict[str, Path]
            Mapping of template names to their paths
        """
        templates = {}
        
        # System templates
        system_templates_dir = self.base_template_dir
        if system_templates_dir.exists():
            for template_file in system_templates_dir.glob("*.md"):
                templates[template_file.name] = template_file

        # User templates
        user_templates_dir = Path.home() / ".giv" / "templates"
        if user_templates_dir.exists():
            for template_file in user_templates_dir.glob("*.md"):
                templates[template_file.name] = template_file

        # Project templates (search up directory tree)
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            project_templates_dir = current_dir / ".giv" / "templates"
            if project_templates_dir.exists():
                for template_file in project_templates_dir.glob("*.md"):
                    templates[template_file.name] = template_file
                break  # Stop at first .giv/templates found
            current_dir = current_dir.parent

        # Custom template directory
        if self.template_dir and self.template_dir.exists():
            for template_file in self.template_dir.glob("*.md"):
                templates[template_file.name] = template_file

        return templates

    def _is_safe_template_name(self, template_name: str) -> bool:
        """Validate template name for security.
        
        Parameters
        ----------
        template_name : str
            Template name to validate
            
        Returns
        -------
        bool
            True if template name is safe
        """
        import re
        
        # Reject names with null bytes, control characters, or directory traversal patterns
        if '\x00' in template_name or any(ord(c) < 32 for c in template_name):
            return False
        
        # Reject obvious directory traversal attempts
        dangerous_patterns = ['../', '..\\', '.\\', '~/', '/etc/', '/var/', '/usr/', '/proc/']
        template_lower = template_name.lower()
        if any(pattern in template_lower for pattern in dangerous_patterns):
            return False
        
        # Reject names that are too long (potential buffer overflow)
        if len(template_name) > 255:
            return False
        
        # Allow only reasonable template filename characters
        if not re.match(r'^[a-zA-Z0-9._/\-]+$', template_name):
            return False
        
        return True
    
    def _is_path_within_directory(self, path: Path, directory: Path) -> bool:
        """Check if a path is within a given directory.
        
        Parameters
        ----------
        path : Path
            Path to check (should be resolved)
        directory : Path
            Parent directory to check against
            
        Returns
        -------
        bool
            True if path is within directory
        """
        try:
            # Resolve both paths to handle symlinks and relative components
            resolved_path = path.resolve()
            resolved_directory = directory.resolve()
            
            # Check if path starts with directory
            return str(resolved_path).startswith(str(resolved_directory) + '/')
        except (OSError, ValueError):
            # If resolution fails, err on the side of caution
            return False


# Backward compatibility aliases
TemplateManager = TemplateEngine

# Default template engine instance
default_template_engine = TemplateEngine()


def render_template(template_path: Union[Path, str], context: Dict[str, Any]) -> str:
    """Convenience function for rendering templates.
    
    This function provides backward compatibility with the existing code.
    
    Parameters
    ----------
    template_path : Union[Path, str]
        Path to template file or template name
    context : Dict[str, Any]
        Template context variables
        
    Returns
    -------
    str
        Rendered template content
    """
    if isinstance(template_path, str):
        return default_template_engine.render_template_file(template_path, context)
    else:
        template_content = template_path.read_text(encoding="utf-8")
        return default_template_engine.render_template(template_content, context)