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

    def find_template(self, template_name: str) -> Path:
        """Find template file using Bash-compatible search hierarchy.
        
        Search order:
        1. Explicit path (if template_name is absolute/relative path)
        2. Project-level .giv/templates/
        3. User-level ~/.giv/templates/
        4. System templates (bundled with package)
        
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
        # 1. Check if it's an explicit path
        if template_name.startswith("/") or template_name.startswith("./") or template_name.startswith("../"):
            template_path = Path(template_name)
            if template_path.exists():
                return template_path
            raise TemplateError(f"Template not found: {template_path}")

        # 2. Check project-level .giv/templates/
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            project_templates = current_dir / ".giv" / "templates" / template_name
            if project_templates.exists():
                return project_templates
            current_dir = current_dir.parent

        # 3. Check user-level ~/.giv/templates/
        home = Path.home()
        user_templates = home / ".giv" / "templates" / template_name
        if user_templates.exists():
            return user_templates

        # 4. Check system templates (bundled with package)
        system_templates = Path(__file__).parent.parent / TEMPLATES_DIR / template_name
        if system_templates.exists():
            return system_templates

        # 5. Check custom template directory if provided
        if self.template_dir:
            custom_template = self.template_dir / template_name
            if custom_template.exists():
                return custom_template

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
        return template_path.read_text(encoding="utf-8")

    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template by replacing tokens with context values.
        
        Supports both {{TOKEN}} and [TOKEN] formats for compatibility.
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
        result = template_content
        
        # Replace {{TOKEN}} format (primary format)
        for key, value in context.items():
            if value is None:
                value = ""
            elif not isinstance(value, str):
                value = str(value)
            
            token_pattern = f"{{{{{key}}}}}"
            result = result.replace(token_pattern, value)
        
        # Replace [TOKEN] format (legacy compatibility)
        for key, value in context.items():
            if value is None:
                value = ""
            elif not isinstance(value, str):
                value = str(value)
            
            token_pattern = f"[{key}]"
            result = result.replace(token_pattern, value)
        
        return result

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
        # Find all {{TOKEN}} patterns
        double_brace_tokens = re.findall(r'\{\{([^}]+)\}\}', template_content)
        
        # Find all [TOKEN] patterns
        square_bracket_tokens = re.findall(r'\[([^]]+)\]', template_content)
        
        return {
            "double_brace_tokens": double_brace_tokens,
            "square_bracket_tokens": square_bracket_tokens,
            "all_tokens": list(set(double_brace_tokens + square_bracket_tokens)),
            "is_valid": True,  # Basic validation - could be enhanced
            "errors": []
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
        system_templates_dir = Path(__file__).parent.parent / TEMPLATES_DIR
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