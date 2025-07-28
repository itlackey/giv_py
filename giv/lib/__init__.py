"""
Normalized library modules for giv CLI.

This package contains normalized utility modules that provide core functionality
for the giv CLI. All modules follow consistent naming conventions and design patterns.
"""

# Re-export key classes for easy importing
from .git import GitRepository
from .llm import LLMClient
from .templates import TemplateEngine
from .output import OutputManager
from .metadata import ProjectMetadata
from .markdown import MarkdownProcessor

__all__ = [
    'GitRepository',
    'LLMClient', 
    'TemplateEngine',
    'OutputManager',
    'ProjectMetadata',
    'MarkdownProcessor',
]