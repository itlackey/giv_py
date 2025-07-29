"""
Tests for versioned output file naming functionality.

This module tests that commands use proper versioned file naming as per specification.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import argparse

from giv.commands.release_notes import ReleaseNotesCommand
from giv.commands.announcement import AnnouncementCommand
from giv.commands.document import DocumentCommand
from giv.config import ConfigManager


class TestVersionedFileNaming:
    """Test versioned file naming for output commands."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing."""
        mock_config = Mock(spec=ConfigManager)
        mock_config.get.return_value = None  # No custom config values
        return mock_config
    
    @pytest.fixture
    def basic_args(self):
        """Basic argument namespace for testing."""
        args = argparse.Namespace()
        args.output_file = None
        args.output_mode = None
        args.output_version = None
        args.prompt_file = "test_prompt.md"  # Required for document command
        return args
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_release_notes_default_filename(self, mock_get_version, basic_args, mock_config_manager):
        """Test release notes uses {VERSION}_release_notes.md format."""
        mock_get_version.return_value = "1.2.3"
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "1.2.3_release_notes.md"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_announcement_default_filename(self, mock_get_version, basic_args, mock_config_manager):
        """Test announcement uses {VERSION}_announcement.md format."""
        mock_get_version.return_value = "2.0.0"
        
        cmd = AnnouncementCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "2.0.0_announcement.md"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_document_default_filename(self, mock_get_version, basic_args, mock_config_manager):
        """Test document uses {VERSION}_document.md format."""
        mock_get_version.return_value = "0.1.0"
        
        cmd = DocumentCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "0.1.0_document.md"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_version_fallback_unknown(self, mock_get_version, basic_args, mock_config_manager):
        """Test fallback to 'unknown' when version cannot be determined."""
        mock_get_version.return_value = None
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "unknown_release_notes.md"
    
    def test_explicit_output_file_overrides_default(self, basic_args, mock_config_manager):
        """Test that explicit --output-file overrides versioned naming."""
        basic_args.output_file = "custom_output.md"
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "custom_output.md"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_config_file_overrides_default(self, mock_get_version, basic_args, mock_config_manager):
        """Test that config file setting overrides versioned naming."""
        mock_get_version.return_value = "1.0.0"
        mock_config_manager.get.side_effect = lambda key: {
            "release_notes_file": "CUSTOM_RELEASE.md"
        }.get(key)
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "CUSTOM_RELEASE.md"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_output_version_override(self, mock_get_version, basic_args, mock_config_manager):
        """Test that output_version parameter overrides detected version."""
        mock_get_version.return_value = "1.0.0"
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content", output_version="2.5.0")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "2.5.0_release_notes.md"


class TestVersionedOutputModes:
    """Test that versioned commands use correct output modes."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing."""
        mock_config = Mock(spec=ConfigManager)
        mock_config.get.return_value = None
        return mock_config
    
    @pytest.fixture  
    def basic_args(self):
        """Basic argument namespace for testing."""
        args = argparse.Namespace()
        args.output_file = None
        args.output_mode = None
        args.output_version = None
        args.prompt_file = "test_prompt.md"  # Required for document command
        return args
    
    def test_release_notes_auto_mode_becomes_overwrite(self, basic_args, mock_config_manager):
        """Test release notes maps auto mode to overwrite."""
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content", output_mode="auto")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_mode'] == "overwrite"
    
    def test_announcement_auto_mode_becomes_overwrite(self, basic_args, mock_config_manager):
        """Test announcement maps auto mode to overwrite."""
        cmd = AnnouncementCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content", output_mode="auto")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_mode'] == "overwrite"
    
    def test_document_auto_mode_becomes_overwrite(self, basic_args, mock_config_manager):
        """Test document maps auto mode to overwrite."""
        cmd = DocumentCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            cmd.handle_output("test content", output_mode="auto")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_mode'] == "overwrite"