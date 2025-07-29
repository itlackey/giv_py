"""
Comprehensive tests for main module.

Tests entry point functionality, argument preprocessing, and main() function.
"""
import sys
from unittest.mock import patch, Mock
import pytest

from giv.main import main, _preprocess_args


class TestPreprocessArgs:
    """Test argument preprocessing functionality."""
    
    def test_preprocess_args_empty(self):
        """Test preprocessing empty arguments."""
        result = _preprocess_args([])
        assert result == []
    
    def test_preprocess_args_none(self):
        """Test preprocessing None arguments."""
        result = _preprocess_args(None)
        assert result is None
    
    def test_preprocess_args_no_config(self):
        """Test preprocessing arguments without config command."""
        args = ["message", "--dry-run", "HEAD"]
        result = _preprocess_args(args)
        assert result == args
    
    def test_preprocess_args_config_list(self):
        """Test preprocessing config list command."""
        args = ["config"]
        result = _preprocess_args(args)
        assert result == ["config", "--list"]
    
    def test_preprocess_args_config_get(self):
        """Test preprocessing config get command."""
        args = ["config", "api.url"]
        result = _preprocess_args(args)
        assert result == ["config", "--get", "api.url"]
    
    def test_preprocess_args_config_set(self):
        """Test preprocessing config set command."""
        args = ["config", "api.url", "http://localhost:11434"]
        result = _preprocess_args(args)
        assert result == ["config", "--set", "api.url", "http://localhost:11434"]
    
    def test_preprocess_args_config_unset(self):
        """Test preprocessing config unset command."""
        args = ["config", "--unset", "api.url"]
        result = _preprocess_args(args)
        assert result == ["config", "--unset", "api.url"]
    
    def test_preprocess_args_config_with_global_flags(self):
        """Test preprocessing config with global flags."""
        args = ["--verbose", "config", "api.url", "test"]
        result = _preprocess_args(args)
        assert result == ["--verbose", "config", "--set", "api.url", "test"]
    
    def test_preprocess_args_config_already_processed(self):
        """Test preprocessing already processed config arguments."""
        args = ["config", "--get", "api.url"]
        result = _preprocess_args(args)
        assert result == args  # Should not modify already processed args
    
    def test_preprocess_args_config_position_detection(self):
        """Test config position detection with various flags."""
        # Test with different global flags
        test_cases = [
            (["--dry-run", "config", "api.url"], 1),
            (["--verbose", "--dry-run", "config", "api.url"], 2),
            (["config", "api.url"], 0),
        ]
        
        for args, expected_pos in test_cases:
            result = _preprocess_args(args)
            # Verify that config command was found and processed
            assert "--get" in result or "--set" in result
            assert any(key in result for key in ["--get", "--set"])
    
    def test_preprocess_args_config_edge_cases(self):
        """Test preprocessing config edge cases."""
        # Config not actually a command (e.g., as argument to another command)
        args = ["message", "--output-file", "config.txt"]
        result = _preprocess_args(args)
        assert result == args  # Should not modify
        
        # Config at end without arguments
        args = ["--verbose", "config"]
        result = _preprocess_args(args)
        assert result == ["--verbose", "config", "--list"]


class TestMainFunction:
    """Test main() function functionality."""
    
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_success(self, mock_build_parser, mock_run_command):
        """Test successful main execution."""
        # Setup mocks
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_run_command.return_value = 0
        
        # Test with no arguments (uses sys.argv)
        with patch('sys.argv', ['giv', 'message']):
            result = main()
        
        assert result == 0
        mock_build_parser.assert_called_once()
        mock_parser.parse_args.assert_called_once_with(['message'])
        mock_run_command.assert_called_once_with(mock_args)
    
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_with_argv(self, mock_build_parser, mock_run_command):
        """Test main with explicit argv."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_run_command.return_value =0
        
        result = main(['summary', '--dry-run'])
        
        assert result == 0
        mock_parser.parse_args.assert_called_once_with(['summary', '--dry-run'])
    
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_preprocessing(self, mock_build_parser, mock_run_command):
        """Test main with argument preprocessing."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_run_command.return_value = 0
        
        # Test that config arguments are preprocessed
        result = main(['config', 'api.url', 'test'])
        
        assert result == 0
        # Verify preprocessed arguments were passed to parser
        call_args = mock_parser.parse_args.call_args[0][0]
        assert '--set' in call_args
        assert 'api.url' in call_args
    
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_command_failure(self, mock_build_parser, mock_run_command):
        """Test main with command failure."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_run_command.return_value = 1  # Command failed
        
        result = main(['message'])
        
        assert result == 1
    
    @patch('giv.main.build_parser')
    def test_main_parser_error(self, mock_build_parser):
        """Test main with parser error."""
        mock_parser = Mock()
        mock_parser.parse_args.side_effect = SystemExit(2)  # argparse error
        mock_build_parser.return_value = mock_parser
        
        result = main(['--invalid-option'])
        
        assert result == 1  # Parser errors are converted to return code 1
    
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_exception_handling(self, mock_build_parser, mock_run_command):
        """Test main exception handling."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        mock_run_command.side_effect = Exception("Unexpected error")
        
        # Main should not let exceptions bubble up in normal usage
        with patch('giv.main.logger') as mock_logger:
            result = main(['message'])
            
            # Should log error and return error code
            mock_logger.exception.assert_called_once()
            assert result == 1


class TestMainIntegration:
    """Test main integration scenarios."""
    
    @patch('giv.main.run_command')
    def test_main_full_integration(self, mock_run_command):
        """Test main with full integration (real parser)."""
        mock_run_command.return_value = 0
        
        # Test actual argument parsing
        result = main(['--dry-run', 'message'])
        
        assert result == 0
        # Verify run_command was called with parsed args
        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert hasattr(args, 'command')
        assert hasattr(args, 'dry_run')
        assert args.dry_run is True
    
    @patch('giv.main.run_command')
    def test_main_config_integration(self, mock_run_command):
        """Test main with config command integration."""
        mock_run_command.return_value = 0
        
        result = main(['config', 'api.url', 'http://test:11434'])
        
        assert result == 0
        args = mock_run_command.call_args[0][0]
        assert args.command == 'config'
        assert args.set is True  # Using individual flags now
        assert args.key == 'api.url'
        assert args.value == 'http://test:11434'
    
    @patch('giv.main.run_command')
    def test_main_error_codes(self, mock_run_command):
        """Test main returns correct error codes."""
        # Test different error codes
        for error_code in [1, 2, 3, 4, 5]:
            mock_run_command.return_value = error_code
            result = main(['message'])
            assert result == error_code
    
    def test_main_sys_argv_usage(self):
        """Test main uses sys.argv correctly."""
        with patch('sys.argv', ['giv', 'message', '--help']):
            with patch('giv.main.run_command') as mock_run_command:
                # --help should cause main to return 0 (help was displayed)
                result = main()
                assert result == 0
                
                # run_command should not be called due to --help
                mock_run_command.assert_not_called()


class TestMainErrorHandling:
    """Test main error handling scenarios."""
    
    # @patch('giv.main.build_parser')
    # def test_main_keyboard_interrupt(self, mock_build_parser):
    #     """Test main handling KeyboardInterrupt."""
    #     mock_parser = Mock()
    #     mock_parser.parse_args.side_effect = KeyboardInterrupt()
    #     mock_build_parser.return_value = mock_parser
        
    #     with patch('giv.main.logger') as mock_logger:
    #         result = main(['message'])
            
    #         # Should handle gracefully
    #         assert result == 1
    #         mock_logger.info.assert_called_once_with("Operation cancelled by user")
    
    # @patch('giv.main.run_command')
    # @patch('giv.main.build_parser')
    # def test_main_memory_error(self, mock_build_parser, mock_run_command):
    #     """Test main handling MemoryError."""
    #     mock_parser = Mock()
    #     mock_args = Mock()
    #     mock_parser.parse_args.return_value = mock_args
    #     mock_build_parser.return_value = mock_parser
    #     mock_run_command.side_effect = MemoryError("Out of memory")
        
    #     with patch('giv.main.logger') as mock_logger:
    #         result = main(['message'])
            
    #         assert result == 1
    #         mock_logger.exception.assert_called_once()
    
    # @patch('giv.main.run_command')
    # @patch('giv.main.build_parser')
    # def test_main_system_exit(self, mock_build_parser, mock_run_command):
    #     """Test main handling SystemExit from commands."""
    #     mock_parser = Mock()
    #     mock_args = Mock()
    #     mock_parser.parse_args.return_value = mock_args
    #     mock_build_parser.return_value = mock_parser
    #     mock_run_command.side_effect = SystemExit(42)
        
    #     # SystemExit should bubble up
    #     with pytest.raises(SystemExit) as exc_info:
    #         main(['message'])
        
    #     assert exc_info.value.code == 42


class TestMainEdgeCases:
    """Test main edge cases."""
    
    def test_main_empty_argv(self):
        """Test main with empty argv."""
        with patch('giv.main.run_command') as mock_run_command:
            mock_run_command.return_value = 0
            
            result = main([])
            
            assert result == 0
            # Should call with empty args, which triggers default command
            mock_run_command.assert_called_once()
    
    def test_main_none_argv(self):
        """Test main with None argv."""
        with patch('sys.argv', ['giv', 'message']):
            with patch('giv.main.run_command') as mock_run_command:
                mock_run_command.return_value = 0
                
                result = main(None)
                
                assert result == 0
                # Should use sys.argv
                args = mock_run_command.call_args[0][0]
                assert args.command == 'message'
    
    @patch('giv.main._preprocess_args')
    @patch('giv.main.run_command')
    def test_main_preprocessing_none_result(self, mock_run_command, mock_preprocess):
        """Test main when preprocessing returns None."""
        mock_preprocess.return_value = None
        mock_run_command.return_value = 0
        
        result = main(['message'])
        
        # Should handle None from preprocessing
        assert result == 0
        mock_run_command.assert_called_once()   

class TestMainLogging:
    """Test main function logging behavior."""
    
    @patch('giv.main.logger')
    @patch('giv.main.run_command')
    @patch('giv.main.build_parser')
    def test_main_logs_exceptions(self, mock_build_parser, mock_run_command, mock_logger):
        """Test that main logs exceptions properly."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser
        
        # Test different exception types
        exceptions = [
            ValueError("Test error"),
            RuntimeError("Runtime error"),
            IOError("IO error"),
        ]
        
        for exception in exceptions:
            mock_run_command.side_effect = exception
            result = main(['message'])
            
            assert result == 1
            mock_logger.exception.assert_called()
            mock_logger.reset_mock()
    
    # @patch('giv.main.logger')
    # def test_main_logs_keyboard_interrupt(self, mock_logger):
    #     """Test that main logs KeyboardInterrupt appropriately."""
    #     with patch('giv.main.build_parser') as mock_build_parser:
    #         mock_parser = Mock()
    #         mock_parser.parse_args.side_effect = KeyboardInterrupt()
    #         mock_build_parser.return_value = mock_parser
            
    #         result = main(['message'])
            
    #         assert result == 1
    #         mock_logger.info.assert_called_once_with("Operation cancelled by user")