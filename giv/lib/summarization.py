"""
Commit summarization and caching functionality.

This module implements the core multi-commit workflow with caching that matches
the functionality described in the shell script reference implementation.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import List, Optional

from .git import GitRepository
from .llm import LLMClient
from .metadata import ProjectMetadata
from .templates import TemplateEngine

logger = logging.getLogger(__name__)


class CommitSummarizer:
    """Handles commit summarization with caching using the reference workflow."""
    
    def __init__(self, git_repo: Optional[GitRepository] = None):
        """Initialize commit summarizer.
        
        Parameters
        ---------- 
        git_repo : Optional[GitRepository]
            Git repository instance. If None, creates a new one.
        """
        self.git = git_repo or GitRepository()
        self.template_engine = TemplateEngine()
    
    def summarize_commit(self, commit: str, pathspec: Optional[List[str]] = None, 
                        llm_client: Optional[LLMClient] = None) -> str:
        """Summarize a single commit with caching.
        
        This is the core function that matches summarize_commit from the shell script.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
        pathspec : Optional[List[str]]
            Optional path specifications to limit analysis
        llm_client : Optional[LLMClient]
            LLM client for generating summaries
            
        Returns
        -------
        str
            Commit summary with metadata header
        """
        logger.debug(f"Starting summarization for commit: {commit}")
        
        # Check cache first
        cached_summary = self.git.get_cached_summary(commit)
        if cached_summary:
            return cached_summary
        
        # Generate new summary
        if not llm_client:
            raise ValueError("LLM client required for generating new summaries")
        
        # Build commit history 
        history_content = self.git.build_commit_history(commit, pathspec)
        
        # Get commit version
        try:
            version = ProjectMetadata.get_version(commit)
        except Exception:
            version = "unknown"
        
        # Build summary prompt using commit_summary_prompt.md template
        prompt = self._build_summary_prompt(version, history_content)
        
        # Generate summary using LLM
        try:
            response = llm_client.generate(prompt)
            summary_content = response.get("content", "")
        except Exception as e:
            logger.error(f"Failed to generate summary for commit {commit}: {e}")
            summary_content = f"Error generating summary: {e}"
        
        # Prepend commit metadata
        metadata_header = self._build_commit_metadata(commit)
        full_summary = f"{metadata_header}\n{summary_content}"
        
        # Cache the result
        self.git.cache_summary(commit, full_summary)
        
        return full_summary
    
    def summarize_target(self, target: str, pathspec: Optional[List[str]] = None,
                        llm_client: Optional[LLMClient] = None) -> str:
        """Summarize a target revision (single commit, range, or special revision).
        
        This matches the summarize_target function from the shell script.
        
        Parameters
        ----------
        target : str
            Target revision specification
        pathspec : Optional[List[str]]
            Optional path specifications
        llm_client : Optional[LLMClient]
            LLM client for generating summaries
            
        Returns
        -------
        str
            Combined summaries for all commits in the target
        """
        logger.debug(f"Starting summarize_target for: {target}")
        
        if not target:
            target = "--current"
        
        try:
            # Parse the target into individual commits
            commits = self.git.parse_commit_list(target)
            logger.debug(f"Parsed {len(commits)} commits from target: {target}")
        except ValueError as e:
            logger.error(f"Invalid target specification: {e}")
            return f"Error: {e}"
        
        # Summarize each commit
        summaries = []
        for commit in commits:
            try:
                summary = self.summarize_commit(commit, pathspec, llm_client)
                summaries.append(summary)
                summaries.append("")  # Add separator between commits
            except Exception as e:
                logger.error(f"Failed to summarize commit {commit}: {e}")
                summaries.append(f"Error summarizing commit {commit}: {e}")
                summaries.append("")
        
        return "\n".join(summaries)
    
    def _build_summary_prompt(self, version: str, history_content: str) -> str:
        """Build prompt for commit summary generation.
        
        Parameters
        ----------
        version : str
            Project version
        history_content : str
            Commit history content
            
        Returns
        -------
        str
            Formatted prompt for LLM
        """
        try:
            # Build context for template
            context = {
                "VERSION": version,
                "HISTORY": history_content,
                "SUMMARY": history_content,  # Alias for compatibility
                "PROJECT_TITLE": ProjectMetadata.get_title(),
            }
            
            # Use commit_summary_prompt.md template
            return self.template_engine.render_template_file("commit_summary_prompt.md", context)
        except Exception as e:
            logger.error(f"Failed to build summary prompt: {e}")
            # Fallback to simple prompt
            return f"""Please summarize the following commit:

{history_content}

Provide a clear, concise summary focusing on the key changes and their impact."""
    
    def _build_commit_metadata(self, commit: str) -> str:
        """Build commit metadata header for cached summaries.
        
        Parameters
        ----------
        commit : str
            Commit hash or reference
            
        Returns
        -------
        str
            Formatted metadata header
        """
        try:
            date = self.git.get_commit_date(commit)
            message = self.git.get_commit_message(commit) or "No commit message"
            
            return f"""Commit: {commit}
Date: {date}
Message: {message}"""
        except Exception as e:
            logger.warning(f"Failed to build metadata for commit {commit}: {e}")
            return f"Commit: {commit}"
    
    def clear_cache(self, commit: Optional[str] = None) -> None:
        """Clear commit summaries from cache.
        
        Parameters
        ----------
        commit : Optional[str]
            Specific commit to clear, or None to clear all
        """
        giv_home = Path.cwd() / ".giv"
        cache_dir = giv_home / "cache"
        
        if not cache_dir.exists():
            return
        
        if commit:
            # Clear specific commit
            summary_cache = cache_dir / f"{commit}-summary.md"
            history_cache = cache_dir / f"{commit}-history.md"
            
            for cache_file in [summary_cache, history_cache]:
                if cache_file.exists():
                    try:
                        cache_file.unlink()
                        logger.debug(f"Cleared cache: {cache_file}")
                    except OSError as e:
                        logger.warning(f"Failed to clear cache {cache_file}: {e}")
        else:
            # Clear all cache files
            for cache_file in cache_dir.glob("*-summary.md"):
                try:
                    cache_file.unlink()
                    logger.debug(f"Cleared cache: {cache_file}")
                except OSError as e:
                    logger.warning(f"Failed to clear cache {cache_file}: {e}")
            
            for cache_file in cache_dir.glob("*-history.md"):
                try:
                    cache_file.unlink()
                    logger.debug(f"Cleared cache: {cache_file}")
                except OSError as e:
                    logger.warning(f"Failed to clear cache {cache_file}: {e}")
    
    def get_cached_commits(self) -> List[str]:
        """Get list of commits that have cached summaries.
        
        Returns
        -------
        List[str]
            List of commit hashes with cached summaries
        """
        giv_home = Path.cwd() / ".giv"
        cache_dir = giv_home / "cache"
        
        if not cache_dir.exists():
            return []
        
        commits = []
        for cache_file in cache_dir.glob("*-summary.md"):
            commit = cache_file.stem.replace("-summary", "")
            commits.append(commit)
        
        return sorted(commits)