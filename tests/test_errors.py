"""
Comprehensive tests for error handling system.

Tests custom exceptions, error handling utilities, and exit codes.
"""
import io
import sys
from unittest.mock import patch, Mock

import pytest

from giv.errors import (
    GivError, TemplateError, GitError, ConfigError, APIError, OutputError,
    handle_error, print_error, print_warning,
    EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_TEMPLATE_ERROR, EXIT_GIT_ERROR, 
    EXIT_CONFIG_ERROR, EXIT_API_ERROR, EXIT_OUTPUT_ERROR
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_giv_error_default_exit_code(self):
        """Test GivError with default exit code."""
        error = GivError("Test error")
        assert str(error) == "Test error"
        assert error.exit_code == EXIT_GENERAL_ERROR
    
    def test_giv_error_custom_exit_code(self):
        """Test GivError with custom exit code."""
        error = GivError("Test error", EXIT_CONFIG_ERROR)
        assert str(error) == "Test error"
        assert error.exit_code == EXIT_CONFIG_ERROR
    
    def test_template_error(self):
        """Test TemplateError specific behavior."""
        error = TemplateError("Template not found")
        assert str(error) == "Template error: Template not found"
        assert error.exit_code == EXIT_TEMPLATE_ERROR
    
    def test_git_error(self):
        """Test GitError specific behavior."""
        error = GitError("Git command failed")
        assert str(error) == "Git error: Git command failed"
        assert error.exit_code == EXIT_GIT_ERROR
    
    def test_config_error(self):
        """Test ConfigError specific behavior."""
        error = ConfigError("Invalid configuration")
        assert str(error) == "Configuration error: Invalid configuration"
        assert error.exit_code == EXIT_CONFIG_ERROR
    
    def test_api_error(self):
        """Test APIError specific behavior."""
        error = APIError("Connection failed")
        assert str(error) == "API error: Connection failed"
        assert error.exit_code == EXIT_API_ERROR
    
    def test_output_error(self):
        """Test OutputError specific behavior."""
        error = OutputError("Write failed")
        assert str(error) == "Output error: Write failed"
        assert error.exit_code == EXIT_OUTPUT_ERROR


class TestErrorHandling:
    """Test error handling functions."""
    
    def test_handle_giv_error(self, capsys):
        """Test handling of GivError."""
        error = TemplateError("Template not found")
        exit_code = handle_error(error)
        
        captured = capsys.readouterr()
        assert "Error: Template error: Template not found" in captured.err
        assert exit_code == EXIT_TEMPLATE_ERROR
    
    def test_handle_file_not_found_error(self, capsys):
        """Test handling of FileNotFoundError."""
        error = FileNotFoundError("test.txt")
        exit_code = handle_error(error)
        
        captured = capsys.readouterr()
        assert "Error: File not found: test.txt" in captured.err
        assert exit_code == EXIT_GENERAL_ERROR
    
    def test_handle_keyboard_interrupt(self, capsys):
        """Test handling of KeyboardInterrupt."""
        error = KeyboardInterrupt()
        exit_code = handle_error(error)
        
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err
        assert exit_code == EXIT_GENERAL_ERROR
    
    def test_handle_generic_exception_verbose(self, capsys):
        """Test handling of generic exception with verbose mode."""
        error = ValueError("Invalid value")
        
        with patch('traceback.print_exc') as mock_traceback:
            exit_code = handle_error(error, verbose=True)
            mock_traceback.assert_called_once()
        
        assert exit_code == EXIT_GENERAL_ERROR
    
    def test_handle_generic_exception_non_verbose(self, capsys):
        """Test handling of generic exception without verbose mode."""
        error = ValueError("Invalid value")
        exit_code = handle_error(error, verbose=False)
        
        captured = capsys.readouterr()
        assert "Error: Invalid value" in captured.err
        assert exit_code == EXIT_GENERAL_ERROR
    
    def test_print_error_default_prefix(self, capsys):
        """Test print_error with default prefix."""
        print_error("Test message")
        
        captured = capsys.readouterr()
        assert "Error: Test message" in captured.err
    
    def test_print_error_custom_prefix(self, capsys):
        """Test print_error with custom prefix."""
        print_error("Test message", "Warning")
        
        captured = capsys.readouterr()
        assert "Warning: Test message" in captured.err
    
    def test_print_warning(self, capsys):
        """Test print_warning function."""
        print_warning("Test warning")
        
        captured = capsys.readouterr()
        assert "Warning: Test warning" in captured.err


class TestExitCodes:
    """Test exit code constants."""
    
    def test_exit_code_values(self):
        """Test that exit codes have expected values."""
        assert EXIT_SUCCESS == 0
        assert EXIT_GENERAL_ERROR == 1
        assert EXIT_TEMPLATE_ERROR == 2
        assert EXIT_GIT_ERROR == 3
        assert EXIT_CONFIG_ERROR == 4
        assert EXIT_API_ERROR == 5
        assert EXIT_OUTPUT_ERROR == 6
    
    def test_exit_codes_are_unique(self):
        """Test that all exit codes are unique."""
        codes = [
            EXIT_SUCCESS, EXIT_GENERAL_ERROR, EXIT_TEMPLATE_ERROR,
            EXIT_GIT_ERROR, EXIT_CONFIG_ERROR, EXIT_API_ERROR, EXIT_OUTPUT_ERROR
        ]
        assert len(codes) == len(set(codes))


class TestErrorIntegration:
    """Test integration scenarios with error handling."""
    
    def test_chain_giv_errors(self):
        """Test chaining GivError exceptions."""
        try:
            try:
                raise TemplateError("Inner error")
            except TemplateError as e:
                raise ConfigError("Outer error") from e
        except ConfigError as outer:
            assert str(outer) == "Configuration error: Outer error"
            assert outer.exit_code == EXIT_CONFIG_ERROR
            assert isinstance(outer.__cause__, TemplateError)
    
    def test_multiple_error_types_handling(self, capsys):
        """Test handling multiple different error types."""
        errors = [
            TemplateError("Template issue"),
            GitError("Git issue"),
            ConfigError("Config issue"),
            APIError("API issue"),
            OutputError("Output issue")
        ]
        
        expected_codes = [
            EXIT_TEMPLATE_ERROR, EXIT_GIT_ERROR, EXIT_CONFIG_ERROR,
            EXIT_API_ERROR, EXIT_OUTPUT_ERROR
        ]
        
        for error, expected_code in zip(errors, expected_codes):
            exit_code = handle_error(error)
            assert exit_code == expected_code
        
        captured = capsys.readouterr()
        assert "Template error: Template issue" in captured.err
        assert "Git error: Git issue" in captured.err
        assert "Configuration error: Config issue" in captured.err
        assert "API error: API issue" in captured.err
        assert "Output error: Output issue" in captured.err