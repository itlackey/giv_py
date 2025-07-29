"""
Init command implementation.

This module implements the init command that initializes giv configuration
and templates in the project directory.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..config import ConfigManager
from ..lib.templates import TemplateEngine
from .base import BaseCommand


class InitCommand(BaseCommand):
    """Initialize giv configuration and templates in project."""
    
    def __init__(self, args: argparse.Namespace, config_manager: ConfigManager):
        """Initialize init command.
        
        Parameters
        ----------
        args : argparse.Namespace
            Parsed command line arguments
        config_manager : ConfigManager
            Configuration manager instance
        """
        super().__init__(args, config_manager)
    
    def run(self) -> int:
        """Execute the init command.
        
        Creates .giv/ directory structure, copies default templates,
        and sets up project-local configuration.
        
        Returns
        -------
        int
            Exit code (0 for success, non-zero for failure)
        """
        try:
            cwd = Path.cwd()
            giv_dir = cwd / ".giv"
            
            # Create .giv directory structure
            giv_dir.mkdir(exist_ok=True)
            
            # Create templates directory
            templates_dir = giv_dir / "templates"
            templates_dir.mkdir(exist_ok=True)
            
            # Copy system templates to project templates directory
            template_mgr = TemplateEngine()
            system_templates_dir = Path(__file__).parent.parent / "templates"
            
            if system_templates_dir.exists():
                copied_count = 0
                for template_file in system_templates_dir.glob("*.md"):
                    dest = templates_dir / template_file.name
                    if not dest.exists():
                        dest.write_text(template_file.read_text(encoding='utf-8'), encoding='utf-8')
                        copied_count += 1
                        if self.args.verbose > 0:
                            print(f"Copied template: {template_file.name}")
                
                if copied_count > 0:
                    print(f"Copied {copied_count} template(s) to {templates_dir}")
                else:
                    print("All templates already exist")
            else:
                print("Warning: System templates directory not found")
            
            # Create basic configuration file if it doesn't exist
            config_file = giv_dir / "config"
            if not config_file.exists():
                self._create_default_config(config_file)
                print(f"Created configuration file: {config_file}")
            else:
                print("Configuration file already exists")
            
            print(f"Initialized giv in {giv_dir}")
            return 0
            
        except Exception as e:
            print(f"Error initializing giv: {e}")
            return 1
    
    def _create_default_config(self, config_path: Path) -> None:
        """Create a default configuration file.
        
        Parameters
        ----------
        config_path : Path
            Path where the configuration file should be created
        """
        default_config = """# Giv Configuration File
# Edit these values to customize giv for your project

# Project metadata
# project.title="My Project"
# project.description="Project description"

# API configuration (prefer environment variables for keys)
# api.url=https://api.openai.com/v1/chat/completions
# api.model.name=gpt-4
# api.model.temperature=0.8
# api.model.max_tokens=8192

# Output configuration
# output.mode=auto
# changelog.file=CHANGELOG.md

# TODO scanning
# todo.pattern=TODO|FIXME|XXX
# todo.files=**/*

# Version detection
# version.file=package.json,pyproject.toml,Cargo.toml
# version.pattern=version\\s*=\\s*["\']([^"\']+)["\']
"""
        config_path.write_text(default_config, encoding='utf-8')