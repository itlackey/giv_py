"""
Comprehensive tests for CLI module.

Tests CLI argument parsing, command dispatch, and error handling.
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
        
        # Test that common arguments are added
        args = parser.parse_args(['--verbose', '--dry-run'])
        assert args.verbose is True
        assert args.dry_run is True
    
    def test_add_common_args_defaults(self):
        """Test common arguments have correct defaults."""
        parser = argparse.ArgumentParser()
        _add_common_args(parser)
        
        args = parser.parse_args([])
        assert args.verbose is False
        assert args.dry_run is False
        assert args.output_mode is None
    
    def test_add_common_args_output_mode_choices(self):
        """Test output mode choices."""
        parser = argparse.ArgumentParser()
        _add_common_args(parser)
        
        # Valid choice
        args = parser.parse_args(['--output-mode', 'append'])
        assert args.output_mode == 'append'
        
        # Invalid choice should raise error
        with pytest.raises(SystemExit):
            parser.parse_args(['--output-mode', 'invalid'])


class TestBuildParser:
    """Test build_parser function."""
    
    def test_build_parser_basic(self):
        """Test basic parser construction."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == 'giv'
    
    def test_build_parser_default_command(self):
        """Test parser with default command."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command == 'message'  # Default command
    
    def test_build_parser_message_command(self):
        """Test message command parsing."""
        parser = build_parser()
        args = parser.parse_args(['message', '--dry-run'])
        assert args.command == 'message'
        assert args.dry_run is True
    
    def test_build_parser_summary_command(self):
        """Test summary command parsing."""
        parser = build_parser()
        args = parser.parse_args(['summary', '--output-file', 'summary.md'])
        assert args.command == 'summary'
        assert args.output_file == 'summary.md'
    
    def test_build_parser_changelog_command(self):
        """Test changelog command parsing."""
        parser = build_parser()
        args = parser.parse_args(['changelog', '--output-version', '1.2.3'])
        assert args.command == 'changelog'
        assert args.output_version == '1.2.3'
    
    def test_build_parser_release_notes_command(self):
        """Test release-notes command parsing."""
        parser = build_parser()
        args = parser.parse_args(['release-notes', '--output-mode', 'overwrite'])
        assert args.command == 'release-notes'
        assert args.output_mode == 'overwrite'
    
    def test_build_parser_announcement_command(self):
        """Test announcement command parsing."""
        parser = build_parser()
        args = parser.parse_args(['announcement', '--api-model', 'gpt-4'])
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
        args = parser.parse_args(['config', '--action', 'set', '--key', 'api.url', '--value', 'test'])
        assert args.command == 'config'
        assert args.action == 'set'
        assert args.key == 'api.url'
        assert args.value == 'test'
    
    def test_build_parser_global_options(self):
        """Test global options work with all commands."""
        parser = build_parser()
        
        # Test with different commands
        commands = ['message', 'summary', 'changelog', 'config']
        for cmd in commands:
            args = parser.parse_args([cmd, '--verbose', '--api-url', 'http://test:11434'])
            assert args.command == cmd
            assert args.verbose is True
            assert args.api_url == 'http://test:11434'
    
    def test_build_parser_revision_parsing(self):
        """Test revision parsing."""
        parser = build_parser()
        
        # Test various revision formats
        test_cases = [
            (['message', 'HEAD'], 'HEAD'),
            (['message', 'HEAD~5'], 'HEAD~5'),
            (['message', 'main..develop'], 'main..develop'),
            (['message', '--current'], '--current'),
        ]
        
        for args_list, expected_revision in test_cases:
            args = parser.parse_args(args_list)
            assert args.revision == expected_revision
    
    def test_build_parser_pathspec_parsing(self):
        """Test pathspec parsing."""
        parser = build_parser()
        args = parser.parse_args(['message', 'HEAD', 'src/', '*.py', 'README.md'])
        assert args.revision == 'HEAD'
        assert args.pathspec == ['src/', '*.py', 'README.md']
    
    def test_build_parser_help(self):
        """Test help functionality."""
        parser = build_parser()
        
        # Main help should work
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--help'])
        assert exc_info.value.code == 0
        
        # Subcommand help should work
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['message', '--help'])
        assert exc_info.value.code == 0


class TestRunCommand:
    """Test run_command function."""
    
    def test_run_command_message(self):
        """Test running message command."""
        args = argparse.Namespace()
        args.command = 'message'
        args.dry_run = True
        args.verbose = False
        
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
        args = argparse.Namespace()
        args.command = 'summary'
        args.dry_run = False
        args.verbose = False
        
        with patch('giv.cli.SummaryCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_document(self):
        """Test running document command."""
        args = argparse.Namespace()
        args.command = 'document'
        args.prompt_file = 'test.md'
        
        with patch('giv.cli.DocumentCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_changelog(self):
        """Test running changelog command."""
        args = argparse.Namespace()
        args.command = 'changelog'
        
        with patch('giv.cli.ChangelogCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_release_notes(self):
        """Test running release-notes command."""
        args = argparse.Namespace()
        args.command = 'release-notes'
        
        with patch('giv.cli.ReleaseNotesCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_announcement(self):
        """Test running announcement command."""
        args = argparse.Namespace()
        args.command = 'announcement'
        
        with patch('giv.cli.AnnouncementCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_config(self):
        """Test running config command."""
        args = argparse.Namespace()
        args.command = 'config'
        args.action = 'list'
        
        with patch('giv.cli.ConfigCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            result = run_command(args)
            
            assert result == 0
    
    def test_run_command_unknown(self, capsys):
        """Test running unknown command."""
        args = argparse.Namespace()
        args.command = 'unknown'
        
        result = run_command(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown subcommand 'unknown'" in captured.err
    
    def test_run_command_verbose_logging(self):
        """Test verbose logging setup."""
        args = argparse.Namespace()
        args.command = 'message'
        args.verbose = True
        args.dry_run = False
        
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
        args = argparse.Namespace()
        args.command = 'message'
        args.dry_run = False
        args.verbose = False
        
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
        args = argparse.Namespace()
        args.command = 'message'
        args.verbose = False
        
        with patch('giv.cli.MessageCommand') as MockCommand:
            MockCommand.side_effect = Exception("Test error")
            
            with patch('giv.errors.handle_error') as mock_handle_error:
                mock_handle_error.return_value = 1
                
                result = run_command(args)
                
                assert result == 1
                mock_handle_error.assert_called_once()
    
    def test_run_command_keyboard_interrupt(self):
        """Test run_command handles KeyboardInterrupt."""
        args = argparse.Namespace()
        args.command = 'message'
        args.verbose = False
        
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
        args = argparse.Namespace()
        args.command = 'message'
        args.verbose = False
        
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
        commands = [
            'message', 'msg', 'summary', 'document', 'changelog',
            'release-notes', 'announcement', 'config'
        ]
        
        for command in commands:
            args = argparse.Namespace()
            args.command = command
            args.verbose = False
            
            # Mock the appropriate command class
            command_name = command.replace('-', '_').title() + 'Command'
            if command == 'msg':
                command_name = 'MessageCommand'
            
            with patch(f'giv.cli.{command_name}') as MockCommand:
                mock_cmd = Mock()
                mock_cmd.run.return_value = 0
                MockCommand.return_value = mock_cmd
                
                result = run_command(args)
                
                assert result == 0, f"Command {command} failed"
    
    def test_run_command_argument_passing(self):
        """Test that arguments are passed correctly to commands."""
        args = argparse.Namespace()
        args.command = 'message'
        args.verbose = False
        args.dry_run = True
        args.api_url = 'http://test:11434'
        args.api_key = 'test_key'
        args.output_file = 'output.md'
        
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
        args = argparse.Namespace()
        args.command = 'config'
        args.verbose = False
        args.action = 'set'
        args.key = 'api.url'
        args.value = 'http://localhost:11434'
        
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
            args = parser.parse_args(['message', '--dry-run'])
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
            args = parser.parse_args(['config', '--action', 'get', '--key', 'api.url'])
            result = run_command(args)
            
            assert result == 0
            assert args.command == 'config'
            assert args.action == 'get'
            assert args.key == 'api.url'
    
    def test_cli_with_complex_arguments(self):
        """Test CLI with complex argument combinations."""
        with patch('giv.cli.MessageCommand') as MockCommand:
            mock_cmd = Mock()
            mock_cmd.run.return_value = 0
            MockCommand.return_value = mock_cmd
            
            parser = build_parser()
            args = parser.parse_args([
                'message',
                '--verbose',
                '--dry-run',
                '--api-url', 'http://localhost:11434',
                '--api-key', 'test_key',
                '--api-model', 'llama3.2',
                '--output-file', 'commit.txt',
                '--output-mode', 'overwrite',
                'HEAD~5',
                'src/',
                '*.py'
            ])
            
            result = run_command(args)
            
            assert result == 0
            assert args.verbose is True
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
        assert args.command == 'message'  # Default
    
    def test_parser_with_only_global_flags(self):
        """Test parser with only global flags."""
        parser = build_parser()
        args = parser.parse_args(['--verbose'])
        assert args.command == 'message'  # Default command
        assert args.verbose is True
    
    def test_run_command_with_minimal_args(self):
        """Test run_command with minimal arguments."""
        args = argparse.Namespace()
        args.command = 'message'
        # Don't set verbose - should not exist
        
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
        args = parser.parse_args(['message', '--dry-run', '--verbose'])
        assert args.dry_run is True
        assert args.verbose is True
    
    def test_unicode_in_arguments(self):
        """Test parser handles unicode in arguments."""
        parser = build_parser()
        args = parser.parse_args(['message', '--output-file', 'commit_ñ.md'])
        assert args.output_file == 'commit_ñ.md'


class TestCLIErrorMessages:
    """Test CLI error messages."""
    
    def test_unknown_command_error_message(self, capsys):
        """Test error message for unknown command."""
        args = argparse.Namespace()
        args.command = 'nonexistent'
        
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