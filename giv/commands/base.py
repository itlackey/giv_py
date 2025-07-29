"""
Base command class for giv CLI commands.

This module provides the abstract base class that all giv commands inherit from,
establishing common patterns for argument handling, configuration access,
and response generation.
"""
from __future__ import annotations

import argparse
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ..config import ConfigManager
from ..constants import (
    DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_REVISION,
    TEMPERATURE_CREATIVE, CONFIG_TEMPERATURE, CONFIG_MAX_TOKENS,
    CONFIG_TODO_PATTERN, CONFIG_TODO_FILE
)
from ..errors import handle_error, TemplateError
from ..lib.git import GitRepository
from ..lib.llm import LLMClient
from ..lib.output import write_output
from ..lib.metadata import ProjectMetadata
from ..lib.summarization import CommitSummarizer
from ..lib.templates import TemplateEngine

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Abstract base class for all giv commands.
    
    This class provides common functionality shared across commands including:
    - Configuration management
    - Git history access
    - LLM client setup
    - Template rendering
    - Output handling
    """
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize command with parsed arguments and configuration.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        self.args = args
        self.config = config_manager
        self.history = GitRepository()
        self.template_mgr = TemplateEngine()
        self.summarizer = CommitSummarizer(self.history)
    
    @abstractmethod
    def run(self) -> int:
        """Execute the command.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        pass
    
    def get_revision_and_pathspec(self) -> tuple[str, Optional[List[str]]]:
        """Extract revision and pathspec from command arguments.
        
        Returns
        -------
        tuple[str, Optional[List[str]]]
            Revision string and optional pathspec list
        """
        # Check for revision_flag first (--current, --cached flags)
        revision_flag = getattr(self.args, 'revision_flag', None)
        if revision_flag:
            revision = revision_flag
        else:
            revision = getattr(self.args, 'revision', DEFAULT_REVISION) or DEFAULT_REVISION
        
        pathspec = getattr(self.args, 'pathspec', []) or []
        return revision, pathspec if pathspec else None
    
    def build_template_context(self, revision: str, pathspec: Optional[List[str]] = None) -> Dict[str, str]:
        """Build template context with commit summaries and project information.
        
        This implements the core workflow from Section 12.0 of the specification:
        1. Parse commits from revision 
        2. Generate summaries for each commit (with caching)
        3. Build final template context using cached summaries
        
        Parameters
        ----------
        revision : str
            Git revision to analyze
        pathspec : Optional[List[str]]
            Optional path specifications to limit analysis
            
        Returns
        -------
        Dict[str, str]
            Template context dictionary
        """
        # Create LLM client for summarization if needed
        llm_client = self.create_llm_client()
        
        # Use the new summarization workflow
        try:
            # Generate commit summaries (this handles caching automatically)
            commit_summaries = self.summarizer.summarize_target(
                revision or "--current", 
                pathspec, 
                llm_client
            )
        except Exception as e:
            logger.warning(f"Failed to generate commit summaries, falling back to diff: {e}")
            # Fallback to raw diff if summarization fails
            commit_summaries = self.history.get_diff(revision=revision, paths=pathspec)
        
        # Get git metadata for the primary revision
        primary_revision = revision or "HEAD"
        if revision in ("--current", "--cached", ""):
            git_metadata = self.history.build_history_metadata("HEAD")
        else:
            git_metadata = self.history.build_history_metadata(primary_revision)
        
        # Scan for TODO items if enabled and integrate with summary
        todo_content = self._scan_todos()
        
        # If TODO content is found, append it to the commit summaries
        if todo_content and commit_summaries:
            enhanced_summaries = f"{commit_summaries}\n\n{todo_content}"
        elif todo_content:
            enhanced_summaries = todo_content
        else:
            enhanced_summaries = commit_summaries
        
        # Build context with commit summaries as the primary content
        context = {
            "SUMMARY": enhanced_summaries,  # Generated commit summaries + TODO items
            "HISTORY": enhanced_summaries,  # Alias for compatibility
            "REVISION": revision or "HEAD",
            "PROJECT_TITLE": ProjectMetadata.get_title(),
            "VERSION": ProjectMetadata.get_version(),
            "COMMIT_ID": git_metadata["commit_id"],
            "SHORT_COMMIT_ID": git_metadata["short_commit_id"], 
            "DATE": git_metadata["date"],
            "MESSAGE": git_metadata["message"],
            "MESSAGE_BODY": git_metadata["message_body"],
            "AUTHOR": git_metadata["author"],
            "BRANCH": git_metadata["branch"],
            "TODOS": todo_content,  # Also available as separate variable
            "EXAMPLE": "",  # TODO: Add example context if needed
            "RULES": "",   # TODO: Add rules context if needed
        }
        
        return context
    
    def _scan_todos(self) -> str:
        """Scan for TODO items based on configuration.
        
        Returns
        -------
        str
            Formatted TODO items for template inclusion
        """
        # Get TODO scanning configuration
        todo_pattern = (getattr(self.args, 'todo_pattern', None) or 
                       self.config.get(CONFIG_TODO_PATTERN) or 
                       "TODO|FIXME|XXX")
        
        todo_files = (getattr(self.args, 'todo_files', None) or 
                     self.config.get(CONFIG_TODO_FILE) or 
                     "**/*")
        
        try:
            from ..lib.todo import scan_todos
            return scan_todos(pattern=todo_pattern, file_pattern=todo_files)
        except Exception as e:
            logger.warning(f"TODO scanning failed: {e}")
            return ""
    
    def create_llm_client(self, temperature_override: Optional[float] = None) -> LLMClient:
        """Create and configure an LLM client instance.
        
        Parameters
        ----------
        temperature_override : Optional[float]
            Override default temperature if provided
        
        Returns
        -------
        LLMClient
            Configured LLM client
        """
        # Get API configuration
        api_url = self.args.api_url or self.config.get("api_url")
        api_key = self.args.api_key or self.config.get("api_key")
        model = getattr(self.args, 'api_model', None) or getattr(self.args, 'model', None) or self.config.get("api_model")
        
        # Get temperature and context window settings
        if temperature_override is not None:
            temperature = temperature_override
        else:
            temperature = float(self.config.get(CONFIG_TEMPERATURE) or str(DEFAULT_TEMPERATURE))
        max_tokens = int(self.config.get(CONFIG_MAX_TOKENS) or str(DEFAULT_MAX_TOKENS))
        
        return LLMClient(
            api_url=api_url, 
            api_key=api_key, 
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def render_template(self, template_name: str, context: Dict[str, str]) -> str:
        """Render a template with the given context.
        
        Parameters
        ----------
        template_name : str
            Name of the template file
        context : Dict[str, str]
            Template context variables
            
        Returns
        -------
        str
            Rendered template content
            
        Raises
        ------
        FileNotFoundError
            If template cannot be found
        """
        try:
            return self.template_mgr.render_template_file(template_name, context)
        except FileNotFoundError as e:
            raise TemplateError(f"Template not found: {e}")
    
    def handle_output(self, content: str, output_file: Optional[str] = None, 
                     output_mode: str = "auto", output_version: Optional[str] = None) -> bool:
        """Handle output using the configured output management.
        
        Parameters
        ----------
        content : str
            Content to output
        output_file : Optional[str]
            Output file path (defaults to args.output_file)
        output_mode : str
            Output mode (defaults to args.output_mode or "auto") 
        output_version : Optional[str]
            Version for section updates (defaults to args.output_version)
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Use provided values or fall back to command arguments/config
        output_file = output_file or getattr(self.args, 'output_file', None)
        output_mode = getattr(self.args, 'output_mode', None) or output_mode
        output_version = getattr(self.args, 'output_version', None) or output_version or ProjectMetadata.get_version()
        
        return write_output(
            content=content,
            output_file=output_file,
            output_mode=output_mode,
            output_version=output_version,
            dry_run=getattr(self.args, 'dry_run', False)
        )


class DocumentGeneratingCommand(BaseCommand):
    """Base class for commands that generate documents using LLM."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager, 
                 template_name: str, default_temperature: float = TEMPERATURE_CREATIVE):
        """Initialize document generating command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        template_name : str
            Name of the template file to use
        default_temperature : float
            Default temperature for LLM generation
        """
        super().__init__(args, config_manager)
        self.template_name = template_name
        self.default_temperature = default_temperature
    
    def create_llm_client(self) -> LLMClient:
        """Create LLM client with command-specific temperature."""
        # Use parent method with command-specific temperature override
        default_temp = float(self.config.get(CONFIG_TEMPERATURE) or str(self.default_temperature))
        return super().create_llm_client(temperature_override=default_temp)
    
    def run(self) -> int:
        """Standard document generation workflow."""
        try:
            # Get revision and pathspec
            revision, pathspec = self.get_revision_and_pathspec()
            
            # Build template context
            context = self.build_template_context(revision, pathspec)
            
            # Apply any command-specific context modifications
            context = self.customize_context(context)
            
            # Render template
            prompt = self.render_template(self.template_name, context)
            
            # Create LLM client
            llm = self.create_llm_client()
            
            if getattr(self.args, 'dry_run', False):
                # Show what would be written
                print(f"Dry run: Generated {self.__class__.__name__.lower()} content:")
                print("=" * 50)
                response = llm.generate(prompt, dry_run=True)
                content = response.get("content", prompt)
                
                # Show how it would be written
                success = self.handle_output(content)
                return 0 if success else 1
            
            # Generate content
            response = llm.generate(prompt, dry_run=False)
            content = response.get("content", "")
            
            if not content:
                print("Error: No content generated", file=sys.stderr)
                return 1
            
            # Handle output
            success = self.handle_output(content)
            return 0 if success else 1
            
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return handle_error(e)
    
    def customize_context(self, context: Dict[str, str]) -> Dict[str, str]:
        """Override to customize template context for specific commands.
        
        Parameters
        ----------
        context : Dict[str, str]
            Base template context
            
        Returns
        -------
        Dict[str, str]
            Modified context
        """
        return context