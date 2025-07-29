"""
Comprehensive tests for CLI module argument parsing, command dispatch, and error handling.
"""
import argparse
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import pytest

from giv.cli import build_parser, run_command, _add_common_args
from giv.errors import handle_error


class TestAddCommonArgs:
    """Test _add_common_args function."""
    
    def test_add_common_args(self):
        """Test adding common arguments to parser."""
        parser = argparse.ArgumentParser()
        _add_common_args(parser)
        
        # Note: _add_common_args is now empty as global args are handled at top level
        # This test just verifies the function doesn't crash
        args = parser.parse_args([])
        assert hasattr(args, '__dict__')  # Basic validation that parsing works
    
    def test_add_common_args_defaults(self):
        """Test common arguments have correct defaults."""
        parser = argparse.ArgumentParser()
        _add_common_args(parser)
        
        # Since _add_common_args is now empty, just test it doesn't crash
        args = parser.parse_args([])
        assert hasattr(args, '__dict__')
    
    def test_add_common_args_output_mode_choices(self):
        """Test that _add_common_args is empty (output-mode now in global parser)."""
        parser = argparse.ArgumentParser()
        _add_common_args(parser)
        
        # Since _add_common_args is now empty, test should pass with no args
        args = parser.parse_args([])
        
        # Verify no output-mode argument is added by _add_common_args
        with pytest.raises(SystemExit):
            parser.parse_args(['--output-mode', 'append'])


class TestBuildParser:
    """Test build_parser function."""
    
    def test_build_parser_basic(self):
        """Test basic parser construction."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'giv'
    
    def test_build_parser_default_command(self):
        """Test parser with no command specified."""
        parser = build_parser()
        args = parser.parse_args([])
        # Parser itself doesn't set default - this is handled in main()
        assert args.command is None
    
    def test_build_parser_message_command(self):
        """Test message command parsing."""
        parser = build_parser()
        # Global args like --dry-run should come before subcommand
        args = parser.parse_args(['--dry-run', 'message'])
        assert args.command == 'message'
        assert args.dry_run is True
    
    def test_build_parser_summary_command(self):
        """Test summary command parsing."""
        parser = build_parser()
        # Global args must come before subcommand
        args = parser.parse_args(['--output-file', 'summary.md', 'summary'])
        assert args.command == 'summary'
        assert args.output_file == 'summary.md'
    
    def test_build_parser_changelog_command(self):
        """Test changelog command parsing."""
        parser = build_parser()
        # Global args must come before subcommand
        args = parser.parse_args(['--output-version', '1.2.3', 'changelog'])
        assert args.command == 'changelog'
        assert args.output_version == '1.2.3'
    
    def test_build_parser_release_notes_command(self):
        """Test release-notes command parsing."""
        parser = build_parser()
        # Global args must come before subcommand
        args = parser.parse_args(['--output-mode', 'overwrite', 'release-notes'])
        assert args.command == 'release-notes'
        assert args.output_mode == 'overwrite'
    
    def test_build_parser_announcement_command(self):
        """Test announcement command parsing."""
        parser = build_parser()
        # Global args must come before subcommand
        args = parser.parse_args(['--api-model', 'gpt-4', 'announcement'])
        assert args.command == 'announcement'
        assert args.api_model == 'gpt-4'
    
    def test_build_parser_document_command(self):
        """Test document command parsing."""
        parser = build_parser()
        args = parser.parse_args(['document', '--prompt-file', 'custom.md'])
        assert args.command == 'document'
        assert args.prompt_file == 'custom.md'
    
    def test_build_parser_config_command(self):
        """Test config command parsing."""
        parser = build_parser()
        args = parser.parse_args(['config', '--set', 'api.url', 'test'])
        assert args.command == 'config'
        assert args.set is True
        assert args.key == 'api.url'
        assert args.value == 'test'
    
    def test_build_parser_global_options(self):
        """Test global options work with all commands."""
        parser = build_parser()
        
        # Test with different commands - global args must come before subcommand
        commands = ['message', 'summary', 'changelog', 'config']
        for cmd in commands:
            args = parser.parse_args(['--verbose', '--api-url', 'http://test:11434', cmd])
            assert args.command == cmd
            assert args.verbose == 1
            assert args.api_url == 'http://test:11434'
    
    def test_build_parser_revision_parsing(self):
        """Test revision parsing."""
        parser = build_parser()
        
        # Test various revision formats - revision is a positional argument
        # Note: --current is handled as default, but can't be passed directly due to argparse limitations
        test_cases = [
            (['message', 'HEAD'], 'HEAD'),
            (['message', 'HEAD~5'], 'HEAD~5'),
            (['message', 'main..develop'], 'main..develop'),
        ]
        
        for args_list, expected_revision in test_cases:
            args = parser.parse_args(args_list)
            assert args.revision == expected_revision
        
        # Test default revision (when no revision provided)
        args = parser.parse_args(['message'])
        assert args.revision == '--current'  # Default value
    
    def test_build_parser_pathspec_parsing(self):
        """Test pathspec parsing."""
        parser = build_parser()
        args = parser.parse_args(['message', 'HEAD', 'src/', '*.py', 'README.md'])
        assert args.revision == 'HEAD'
        assert args.pathspec == ['src/', '*.py', 'README.md']
    
    def test_build_parser_help(self):
        """Test help functionality."""
        parser = build_parser()
        
        # Help flag should be parsed as a boolean, not trigger SystemExit
        # because add_help=False
        args = parser.parse_args(['--help'])
        assert args.help is True
        assert args.command is None
        
        # Test help flag with command
        args = parser.parse_args(['--help', 'message'])
        assert args.help is True
        assert args.command == 'message'


class TestRunCommand:
    """Test run_command function."""
    
    def test_run_command_message(self):
        """Test running message command."""
        # Use the actual parser to get a proper args object with all defaults
        parser = build_parser()
        args = parser.parse_args(['message'])
        args.dry_run = True  # Override specific test settings
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
            MockCommand.assert_called_once()
            mock_cmd.run.assert_called_once()
    
    def test_run_command_summary(self):
        """Test running summary command."""
        parser = build_parser()
        args = parser.parse_args(['summary'])
        args.dry_run = False  # Override specific test settings
        
        with patch('giv.cli.SummaryCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_document(self):
        """Test running document command."""
        parser = build_parser()
        args = parser.parse_args(['document', '--prompt-file', 'test.md'])
        
        with patch('giv.cli.DocumentCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_changelog(self):
        """Test running changelog command."""
        parser = build_parser()
        args = parser.parse_args(['changelog'])
        
        with patch('giv.cli.ChangelogCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_release_notes(self):
        """Test running release-notes command."""
        parser = build_parser()
        args = parser.parse_args(['release-notes'])
        
        with patch('giv.cli.ReleaseNotesCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_announcement(self):
        """Test running announcement command."""
        parser = build_parser()
        args = parser.parse_args(['announcement'])
        
        with patch('giv.cli.AnnouncementCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_config(self):
        """Test running config command."""
        parser = build_parser()
        args = parser.parse_args(['config', 'list'])
        
        with patch('giv.cli.ConfigCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_unknown(self, capsys):
        """Test running unknown command."""
        parser = build_parser()
        args = parser.parse_args(['message'])  # Use valid command but override
        args.command = 'unknown'  # Override to test unknown command handling
        
        result = run_command(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown subcommand 'unknown'" in captured.err
    
    def test_run_command_verbose_logging(self):
        """Test verbose logging setup."""
        parser = build_parser()
        args = parser.parse_args(['--verbose', 'message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand, \
             patch('logging.basicConfig') as mock_logging:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
            # Verify logging was configured for verbose mode
            mock_logging.assert_called()
    
    def test_run_command_config_manager_creation(self):
        """Test that ConfigManager is created correctly."""
        parser = build_parser()
        args = parser.parse_args(['message'])
        
        with patch('giv.cli.ConfigManager') as MockConfigManager, \
             patch('giv.cli.MessageCommand') as MockCommand:
            mock_config = Mock()
            MockConfigManager.return_value = mock_config
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
            MockConfigManager.assert_called_once()
            MockCommand.assert_called_once_with(args, mock_config)


class TestRunCommandErrorHandling:
    """Test run_command error handling."""
    
    def test_run_command_exception_handling(self):
        """Test run_command handles exceptions."""
        parser = build_parser()
        args = parser.parse_args(['message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            MockCommand.side_effect = Exception("Test error")
            
            with patch('giv.errors.handle_error') as mock_handle_error:
                mock_handle_error.return_value = 1
                
                result = run_command(args)
                
                assert result == 1
                mock_handle_error.assert_called_once()
    
    def test_run_command_keyboard_interrupt(self):
        """Test run_command handles KeyboardInterrupt."""
        parser = build_parser()
        args = parser.parse_args(['message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            MockCommand.side_effect = KeyboardInterrupt()
            
            with patch('giv.errors.handle_error') as mock_handle_error:
                mock_handle_error.return_value = 1
                
                result = run_command(args)
                
                assert result == 1
                mock_handle_error.assert_called_once()
                
                # Verify KeyboardInterrupt was passed to handle_error
                call_args = mock_handle_error.call_args[0]
                assert isinstance(call_args[0], KeyboardInterrupt)
    
    def test_run_command_command_failure(self):
        """Test run_command when command returns error code."""
        parser = build_parser()
        args = parser.parse_args(['message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 2  # Command failed
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 2


class TestRunCommandAdvanced:
    """Test advanced run_command scenarios."""
    
    def test_run_command_all_commands(self):
        """Test that all commands can be dispatched."""
        test_cases = [
            (['message'], 'MessageCommand'),
            (['msg'], 'MessageCommand'),
            (['summary'], 'SummaryCommand'),
            (['document', '--prompt-file', 'test.md'], 'DocumentCommand'),
            (['changelog'], 'ChangelogCommand'),
            (['release-notes'], 'ReleaseNotesCommand'),
            (['announcement'], 'AnnouncementCommand'),
            (['config', 'list'], 'ConfigCommand')
        ]
        
        parser = build_parser()
        
        for command_args, command_class in test_cases:
            args = parser.parse_args(command_args)
            
            with patch(f'giv.cli.{command_class}') as MockCommand:
                mock_cmd = Mock()
                mock_cmd.run.return_value = 0
                MockCommand.return_value = mock_cmd
                
                result = run_command(args)
                
                assert result == 0, f"Command {command_args[0]} failed"
    
    def test_run_command_argument_passing(self):
        """Test that arguments are passed correctly to commands."""
        parser = build_parser()
        args = parser.parse_args(['--dry-run', '--api-url', 'http://test:11434', '--api-key', 'test_key', '--output-file', 'output.md', 'message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand, \
             patch('giv.cli.ConfigManager') as MockConfigManager:
            mock_config = Mock()
            MockConfigManager.return_value = mock_config
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
            # Verify command was created with correct arguments
            MockCommand.assert_called_once_with(args, mock_config)
    
    def test_run_command_config_integration(self):
        """Test run_command config integration."""
        parser = build_parser()
        args = parser.parse_args(['config', '--set', 'api.url', 'http://localhost:11434'])
        
        with patch('giv.cli.ConfigCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
            # Config command should be called
            MockCommand.assert_called_once()


class TestCLIIntegration:
    """Test CLI integration scenarios."""
    
    def test_full_cli_integration_message(self):
        """Test full CLI integration for message command."""
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            parser = build_parser()
            args = parser.parse_args(['--dry-run', 'message'])
            result = run_command(args)
            
            assert result == 0
            assert args.command == 'message'
            assert args.dry_run is True
    
    def test_full_cli_integration_config(self):
        """Test full CLI integration for config command."""
        with patch('giv.cli.ConfigCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            parser = build_parser()
            args = parser.parse_args(['config', '--get', 'api.url'])
            result = run_command(args)
            
            assert result == 0
            assert args.command == 'config'
            assert args.get is True
            assert args.key == 'api.url'
    
    def test_cli_with_complex_arguments(self):
        """Test CLI with complex argument combinations."""
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            parser = build_parser()
            args = parser.parse_args([
                '--verbose',
                '--dry-run',
                '--api-url', 'http://localhost:11434',
                '--api-key', 'test_key',
                '--api-model', 'llama3.2',
                '--output-file', 'commit.txt',
                '--output-mode', 'overwrite',
                'message',
                'HEAD~5',
                'src/',
                '*.py'
            ])
            
            result = run_command(args)
            
            assert result == 0
            assert args.verbose == 1
            assert args.dry_run is True
            assert args.api_url == 'http://localhost:11434'
            assert args.api_key == 'test_key'
            assert args.api_model == 'llama3.2'
            assert args.output_file == 'commit.txt'
            assert args.output_mode == 'overwrite'
            assert args.revision == 'HEAD~5'
            assert args.pathspec == ['src/', '*.py']


class TestCLIEdgeCases:
    """Test CLI edge cases."""
    
    def test_parser_with_empty_args(self):
        """Test parser with empty arguments."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None  # No default in parser itself
    
    def test_parser_with_only_global_flags(self):
        """Test parser with only global flags."""
        parser = build_parser()
        args = parser.parse_args(['--verbose'])
        assert args.command is None  # No default in parser itself
        assert args.verbose == 1
        # Remove duplicate assertion
    
    def test_run_command_with_minimal_args(self):
        """Test run_command with minimal arguments."""
        parser = build_parser()
        args = parser.parse_args(['message'])
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_parser_argument_conflicts(self):
        """Test parser handles argument conflicts gracefully."""
        parser = build_parser()
        
        # These should not conflict
        args = parser.parse_args(['--dry-run', '--verbose', 'message'])
        assert args.dry_run is True
        assert args.verbose == 1
    
    def test_unicode_in_arguments(self):
        """Test parser handles unicode in arguments."""
        parser = build_parser()
        args = parser.parse_args(['--output-file', 'commit_ñ.md', 'message'])
        assert args.output_file == 'commit_ñ.md'


class TestCLIErrorMessages:
    """Test CLI error messages."""
    
    def test_unknown_command_error_message(self, capsys):
        """Test error message for unknown command."""
        parser = build_parser()
        args = parser.parse_args(['message'])  # Use valid command but override
        args.command = 'nonexistent'  # Override to test unknown command handling
        
        result = run_command(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown subcommand 'nonexistent'" in captured.err
        assert "Use -h or --help for usage information" in captured.err
    
    def test_parser_invalid_option(self):
        """Test parser error for invalid option."""
        parser = build_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--nonexistent-option'])
    
    def test_parser_invalid_choice(self):
        """Test parser error for invalid choice."""
        parser = build_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--output-mode', 'invalid_mode'])