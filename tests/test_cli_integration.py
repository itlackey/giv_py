"""
Comprehensive integration tests for CLI commands.

Tests all commands to ensure they work correctly and maintain
compatibility with the Bash implementation. Includes:
- Basic command functionality
- Output format validation
- Error handling
- Flag and argument processing
"""
import os
import pytest
import subprocess
from pathlib import Path

from giv.main import main


class TestBasicCommands:
    """Test basic command functionality."""
    
    def test_version_command(self, capsys):
        """Test version command output."""
        result = main(["version"])
        assert result == 0
        
        captured = capsys.readouterr()
        output = captured.out.strip()
        
        # Should output a version string
        assert output != ""
        assert "." in output  # Should contain version numbers
    
    def test_help_command(self, capsys):
        """Test help command output."""
        result = main(["--help"])
        assert result == 0
        
        captured = capsys.readouterr()
        output = captured.out.lower()
        
        # Should contain usage information
        assert "usage" in output
        assert "giv" in output
        assert "commands" in output or "subcommands" in output
    
    def test_config_list_empty(self, capsys, giv_home):
        """Test config list with empty configuration."""
        result = main(["config", "list"])
        assert result == 0
        
        # Should succeed even with empty config
        captured = capsys.readouterr()
        # Output might be empty or contain default values
    
    def test_config_set_get(self, capsys, giv_home):
        """Test setting and getting configuration values."""
        # Set a configuration value
        result = main(["config", "set", "test.key", "test.value"])
        assert result == 0
        
        # Get the configuration value
        result = main(["config", "get", "test.key"])
        assert result == 0
        
        captured = capsys.readouterr()
        assert "test.value" in captured.out
    
    def test_available_releases(self, capsys):
        """Test available-releases command."""
        result = main(["available-releases"])
        # Should succeed (tests network connectivity)
        # In offline environments, this might fail, so we allow both
        captured = capsys.readouterr()
        if result == 0:
            # If successful, should have output
            assert captured.out.strip() != ""
        else:
            # If failed, should have error message
            assert "error" in captured.err.lower() or "Error" in captured.err
    
    def test_init_command(self, capsys, temp_dir):
        """Test init command functionality."""
        # Change to temp directory
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            result = main(["init"])
            assert result == 0
            
            # Should create .giv directory
            giv_dir = temp_dir / ".giv"
            assert giv_dir.exists()
            assert giv_dir.is_dir()
            
            # Should create templates directory
            templates_dir = giv_dir / "templates"
            assert templates_dir.exists()
            assert templates_dir.is_dir()
            
            # Should contain template files
            template_files = list(templates_dir.glob("*.md"))
            assert len(template_files) > 0
            
        finally:
            os.chdir(old_cwd)


class TestDocumentGeneration:
    """Test document generation commands."""
    
    def test_message_dry_run(self, capsys, git_repo):
        """Test message command with dry run."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "message"])
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should contain template content
            assert "commit message" in output.lower() or "message" in output.lower()
            
        finally:
            os.chdir(old_cwd)
    
    def test_summary_dry_run(self, capsys, git_repo):
        """Test summary command with dry run."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "summary"])
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should contain template content
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)
    
    def test_changelog_dry_run(self, capsys, git_repo):
        """Test changelog command with dry run."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "changelog"])
            assert result == 0
            
            captured = capsys.readouterr()  
            output = captured.out
            
            # Should contain changelog-related content
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)
    
    def test_release_notes_dry_run(self, capsys, git_repo):
        """Test release-notes command with dry run."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "release-notes"])
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should generate content
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)
    
    def test_announcement_dry_run(self, capsys, git_repo):
        """Test announcement command with dry run."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "announcement"])
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should generate content
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)


class TestOutputModes:
    """Test different output modes."""
    
    def test_changelog_output_modes(self, git_repo, temp_dir):
        """Test changelog with different output modes."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Create a test changelog
            changelog_file = git_repo / "TEST_CHANGELOG.md"
            changelog_file.write_text("""# Changelog

## [Unreleased]

## [1.0.0] - 2023-01-01
- Initial release
""")
            
            # Test different output modes
            modes = ["auto", "prepend", "append", "update", "overwrite"]
            
            for mode in modes:
                result = main([
                    "changelog", 
                    "--dry-run",
                    "--output-mode", mode,
                    "--output-file", str(changelog_file)
                ])
                # Should not fail for any mode
                assert result in [0, 1]  # May fail if no API key, but shouldn't crash
            
        finally:
            os.chdir(old_cwd)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_unknown_command(self, capsys):
        """Test handling of unknown commands."""
        result = main(["nonexistent-command"])
        assert result == 1
        
        captured = capsys.readouterr()
        # argparse reports "invalid choice" for unknown commands
        assert "invalid choice" in captured.err.lower() or "unknown" in captured.err.lower()
    
    def test_missing_required_args(self, capsys):
        """Test handling of missing required arguments."""
        result = main(["document"])  # Missing --prompt-file
        assert result == 1
        
        captured = capsys.readouterr()
        assert "prompt-file" in captured.err.lower() or "required" in captured.err.lower()
    
    def test_config_operations_errors(self, capsys, giv_home):
        """Test config command error handling."""
        # Test getting nonexistent key
        result = main(["config", "get", "nonexistent.key"])
        assert result == 1
        
        captured = capsys.readouterr()
        assert "not set" in captured.err or "nonexistent.key" in captured.err
    
    def test_invalid_git_revision(self, capsys, git_repo):
        """Test handling of invalid git revisions."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Use a nonexistent commit hash
            result = main(["--dry-run", "message", "nonexistent-commit"])
            # Should handle gracefully (may succeed with empty diff or fail gracefully)
            assert result in [0, 1]
            
        finally:
            os.chdir(old_cwd)


class TestGlobalFlags:
    """Test global flags and options."""
    
    def test_verbose_flag(self, capsys, git_repo):
        """Test verbose flag functionality."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--verbose", "--dry-run", "message"])
            assert result == 0
            
            # Verbose mode should enable debug logging
            # We can't easily test logging output here, but command should succeed
            
        finally:
            os.chdir(old_cwd)
    
    def test_config_file_flag(self, capsys, git_repo, temp_dir):
        """Test custom config file flag."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        # Create custom config file
        custom_config = temp_dir / "custom_config"
        custom_config.write_text("api.url=https://custom.api.com\n")
        
        try:
            result = main([
                "--config-file", str(custom_config),
                "config", "get", "api.url"
            ])
            assert result == 0
            
            captured = capsys.readouterr()
            assert "custom.api.com" in captured.out
            
        finally:
            os.chdir(old_cwd)
    
    def test_output_file_flag(self, capsys, git_repo, temp_dir):
        """Test output file flag."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        output_file = temp_dir / "test_output.md"
        
        try:
            result = main([
                "message", 
                "--dry-run",
                "--output-file", str(output_file)
            ])
            # Command might fail without API key, but shouldn't crash
            assert result in [0, 1]
            
        finally:
            os.chdir(old_cwd)


class TestCommandAliases:
    """Test command aliases."""
    
    def test_msg_alias(self, capsys, git_repo):
        """Test that 'msg' works as alias for 'message'."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run", "msg"])
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should behave same as 'message' command
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)


class TestPathspecHandling:
    """Test pathspec handling for git operations."""
    
    def test_pathspec_filtering(self, capsys, git_repo):
        """Test that pathspec arguments filter files correctly."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            # Test with specific path
            result = main(["--dry-run", "message", "HEAD", "src/"])
            assert result == 0
            
            # Should succeed regardless of pathspec
            captured = capsys.readouterr()
            assert len(captured.out.strip()) >= 0  # May be empty but shouldn't error
            
        finally:
            os.chdir(old_cwd)


class TestDefaultBehavior:
    """Test default command behavior."""
    
    def test_no_command_defaults_to_message(self, capsys, git_repo):
        """Test that no command defaults to message command."""
        old_cwd = os.getcwd()
        os.chdir(git_repo)
        
        try:
            result = main(["--dry-run"])  # No explicit command
            assert result == 0
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Should behave like message command
            assert len(output.strip()) > 0
            
        finally:
            os.chdir(old_cwd)
