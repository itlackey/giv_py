"""
Comprehensive integration tests for all command modules.

Tests command execution, error handling, and edge cases for each command.
"""
import argparse
from unittest.mock import Mock, patch, MagicMock
import pytest

from giv.config import ConfigManager
from giv.commands import (
    MessageCommand, SummaryCommand, DocumentCommand, ChangelogCommand,
    ReleaseNotesCommand, AnnouncementCommand, ConfigCommand
)
from giv.errors import TemplateError, ConfigError
from giv.constants import (
    TEMPLATE_MESSAGE, TEMPLATE_SUMMARY, TEMPLATE_CHANGELOG,
    TEMPLATE_RELEASE_NOTES, TEMPLATE_ANNOUNCEMENT
)


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager for testing."""
    config = Mock()
    config.get.return_value = None
    config.list.return_value = {}
    config.list_all.return_value = {}
    config.set.return_value = None
    config.unset.return_value = None
    return config


@pytest.fixture
def basic_args():
    """Create basic command arguments."""
    args = argparse.Namespace()
    args.revision = None
    args.pathspec = []
    args.api_url = None
    args.api_key = None
    args.api_model = None
    args.output_file = None
    args.output_mode = None
    args.output_version = None
    args.dry_run = False
    args.verbose = False
    return args


class TestMessageCommandIntegration:
    """Integration tests for MessageCommand."""
    
    def test_message_command_initialization(self, basic_args, mock_config_manager):
        """Test MessageCommand initialization."""
        cmd = MessageCommand(basic_args, mock_config_manager)
        assert cmd.template_name == TEMPLATE_MESSAGE
        assert cmd.default_temperature == 0.9
    
    @patch('giv.commands.base.GitRepository')
    @patch('giv.commands.base.TemplateEngine')
    @patch('giv.commands.base.LLMClient')
    @patch('giv.commands.base.write_output')
    def test_message_command_success(self, mock_write, mock_llm_cls, mock_template_cls, 
                                   mock_git_cls, basic_args, mock_config_manager):
        """Test successful message command execution."""
        # Setup mocks
        mock_git = Mock()
        mock_git.get_diff.return_value = "test diff"
        mock_git.build_history_metadata.return_value = {
            'commit_id': 'abc123', 'short_commit_id': 'abc123', 'date': '2025-01-28',
            'message': 'test', 'message_body': 'test body', 'author': 'Test User', 'branch': 'main'
        }
        mock_git_cls.return_value = mock_git
        
        mock_template = Mock()
        mock_template.render_template_file.return_value = "rendered template"
        mock_template_cls.return_value = mock_template
        
        mock_llm = Mock()
        mock_llm.generate.return_value = {"content": "Generated commit message"}
        mock_llm_cls.return_value = mock_llm
        
        mock_write.return_value = True
        
        # Execute command
        cmd = MessageCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        # Verify success
        assert result == 0
        mock_write.assert_called_once()
        mock_llm.generate.assert_called_once()
    
    @patch('giv.commands.base.GitRepository')
    @patch('giv.commands.base.TemplateEngine')
    def test_message_command_template_error(self, mock_template_cls, mock_git_cls,
                                          basic_args, mock_config_manager):
        """Test message command with template error."""
        # Setup git mock
        mock_git = Mock()
        mock_git.get_diff.return_value = "test diff"
        mock_git.build_history_metadata.return_value = {
            'commit_id': 'abc123', 'short_commit_id': 'abc123', 'date': '2025-01-28',
            'message': 'test', 'message_body': 'test body', 'author': 'Test User', 'branch': 'main'
        }
        mock_git_cls.return_value = mock_git
        
        mock_template = Mock()
        mock_template.render_template_file.side_effect = TemplateError("Template not found")
        mock_template_cls.return_value = mock_template
        
        cmd = MessageCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 2  # EXIT_TEMPLATE_ERROR
    
    def test_message_command_customize_context(self, basic_args, mock_config_manager):
        """Test message command context customization."""
        cmd = MessageCommand(basic_args, mock_config_manager)
        context = {"TEST": "value"}
        result = cmd.customize_context(context)
        
        # Message command doesn't modify context
        assert result == context


class TestSummaryCommandIntegration:
    """Integration tests for SummaryCommand."""
    
    def test_summary_command_initialization(self, basic_args, mock_config_manager):
        """Test SummaryCommand initialization."""
        cmd = SummaryCommand(basic_args, mock_config_manager)
        assert cmd.template_name == TEMPLATE_SUMMARY
        assert cmd.default_temperature == 0.9
    
    @patch('giv.commands.base.GitRepository')
    @patch('giv.commands.base.TemplateEngine')
    @patch('giv.commands.base.LLMClient')
    @patch('giv.commands.base.write_output')
    def test_summary_command_dry_run(self, mock_write, mock_llm_cls, mock_template_cls, 
                                   mock_git_cls, basic_args, mock_config_manager):
        """Test summary command in dry run mode."""
        basic_args.dry_run = True
        
        # Setup mocks
        mock_git = Mock()
        mock_git.get_diff.return_value = "test diff"
        mock_git.build_history_metadata.return_value = {
            'commit_id': 'abc123', 'short_commit_id': 'abc123', 'date': '2025-01-28',
            'message': 'test', 'message_body': 'test body', 'author': 'Test User', 'branch': 'main'
        }
        mock_git_cls.return_value = mock_git
        
        mock_template = Mock()
        mock_template.render_template_file.return_value = "rendered template"
        mock_template_cls.return_value = mock_template
        
        mock_llm = Mock()
        mock_llm.generate.return_value = {"content": "Generated summary"}
        mock_llm_cls.return_value = mock_llm
        
        mock_write.return_value = True
        
        # Execute command
        cmd = SummaryCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        # Verify dry run behavior
        assert result == 0
        mock_llm.generate.assert_called_once_with("rendered template", dry_run=True)


class TestDocumentCommandIntegration:
    """Integration tests for DocumentCommand."""
    
    def test_document_command_missing_prompt_file(self, basic_args, mock_config_manager):
        """Test DocumentCommand without prompt file raises error."""
        with pytest.raises(ConfigError, match="--prompt-file is required"):
            DocumentCommand(basic_args, mock_config_manager)
    
    def test_document_command_with_prompt_file(self, basic_args, mock_config_manager):
        """Test DocumentCommand with prompt file."""
        basic_args.prompt_file = "custom_template.md"
        cmd = DocumentCommand(basic_args, mock_config_manager)
        assert cmd.template_name == "custom_template.md"
        assert cmd.default_temperature == 0.9
    
    @patch('giv.commands.base.GitRepository')
    @patch('giv.commands.base.TemplateEngine')
    @patch('giv.commands.base.LLMClient')
    @patch('giv.commands.base.write_output')
    def test_document_command_execution(self, mock_write, mock_llm_cls, mock_template_cls, 
                                      mock_git_cls, basic_args, mock_config_manager):
        """Test document command execution."""
        basic_args.prompt_file = "custom_template.md"
        
        # Setup mocks
        mock_git = Mock()
        mock_git.get_diff.return_value = "test diff"
        mock_git.build_history_metadata.return_value = {
            'commit_id': 'abc123', 'short_commit_id': 'abc123', 'date': '2025-01-28',
            'message': 'test', 'message_body': 'test body', 'author': 'Test User', 'branch': 'main'
        }
        mock_git_cls.return_value = mock_git
        
        mock_template = Mock()
        mock_template.render_template_file.return_value = "rendered template"
        mock_template_cls.return_value = mock_template
        
        mock_llm = Mock()
        mock_llm.generate.return_value = {"content": "Generated document"}
        mock_llm_cls.return_value = mock_llm
        
        mock_write.return_value = True
        
        # Execute command
        cmd = DocumentCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0
        from unittest.mock import ANY
        mock_template.render_template_file.assert_called_once_with("custom_template.md", ANY)


class TestChangelogCommandIntegration:
    """Integration tests for ChangelogCommand."""
    
    def test_changelog_command_initialization(self, basic_args, mock_config_manager):
        """Test ChangelogCommand initialization."""
        cmd = ChangelogCommand(basic_args, mock_config_manager)
        assert cmd.template_name == TEMPLATE_CHANGELOG
        assert cmd.default_temperature == 0.7
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_changelog_command_context_customization(self, mock_get_version, 
                                                    basic_args, mock_config_manager):
        """Test changelog command context customization."""
        mock_get_version.return_value = "1.0.0"
        basic_args.output_version = "2.0.0"
        
        cmd = ChangelogCommand(basic_args, mock_config_manager)
        context = {"VERSION": "1.0.0"}
        result = cmd.customize_context(context)
        
        assert result["VERSION"] == "2.0.0"
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_changelog_command_output_handling(self, mock_get_version,
                                              basic_args, mock_config_manager):
        """Test changelog command output handling."""
        mock_get_version.return_value = "1.0.0"
        
        cmd = ChangelogCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            result = cmd.handle_output("test content")
            
            # Verify changelog-specific defaults
            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "CHANGELOG.md"
            assert call_args[1]['output_mode'] == "update"


class TestReleaseNotesCommandIntegration:
    """Integration tests for ReleaseNotesCommand."""
    
    def test_release_notes_command_initialization(self, basic_args, mock_config_manager):
        """Test ReleaseNotesCommand initialization."""
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        assert cmd.template_name == TEMPLATE_RELEASE_NOTES
        assert cmd.default_temperature == 0.7
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_release_notes_output_mode_auto(self, mock_get_version,
                                          basic_args, mock_config_manager):
        """Test release notes auto output mode mapping."""
        mock_get_version.return_value = "1.0.0"
        
        cmd = ReleaseNotesCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            result = cmd.handle_output("test content", output_mode="auto")
            
            # Verify auto maps to overwrite for release notes
            call_args = mock_write.call_args
            assert call_args[1]['output_mode'] == "overwrite"


class TestAnnouncementCommandIntegration:
    """Integration tests for AnnouncementCommand."""
    
    def test_announcement_command_initialization(self, basic_args, mock_config_manager):
        """Test AnnouncementCommand initialization."""
        cmd = AnnouncementCommand(basic_args, mock_config_manager)
        assert cmd.template_name == TEMPLATE_ANNOUNCEMENT
        assert cmd.default_temperature == 0.9
    
    @patch('giv.lib.metadata.ProjectMetadata.get_version')
    def test_announcement_command_config_defaults(self, mock_get_version,
                                                 basic_args, mock_config_manager):
        """Test announcement command uses config defaults."""
        mock_get_version.return_value = "1.0.0"
        mock_config_manager.get.side_effect = lambda key: {
            "announcement_file": "CUSTOM_ANNOUNCEMENT.md",
            "output.mode": "prepend"
        }.get(key)
        
        cmd = AnnouncementCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.write_output') as mock_write:
            mock_write.return_value = True
            result = cmd.handle_output("test content")
            
            call_args = mock_write.call_args
            assert call_args[1]['output_file'] == "CUSTOM_ANNOUNCEMENT.md"
            assert call_args[1]['output_mode'] == "prepend"


class TestConfigCommandIntegration:
    """Integration tests for ConfigCommand."""
    
    def test_config_command_initialization(self, basic_args, mock_config_manager):
        """Test ConfigCommand initialization."""
        cmd = ConfigCommand(basic_args, mock_config_manager)
        assert cmd.config == mock_config_manager
    
    def test_config_command_list_all(self, basic_args, mock_config_manager):
        """Test config command list all values."""
        mock_config_manager.list.return_value = {
            "api.url": "http://localhost:11434",
            "api.model": "llama3.2"
        }
        
        # Set flag-style attributes for config command
        basic_args.list = True
        basic_args.get = False
        basic_args.set = False
        basic_args.unset = False
        basic_args.key = None
        basic_args.value = None
        
        cmd = ConfigCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0
        mock_config_manager.list.assert_called_once()
    
    def test_config_command_get_value(self, basic_args, mock_config_manager, capsys):
        """Test config command get specific value."""
        mock_config_manager.get.return_value = "test_value"
        
        # Set flag-style attributes for config command
        basic_args.list = False
        basic_args.get = True
        basic_args.set = False
        basic_args.unset = False
        basic_args.key = "api.url"
        basic_args.value = None
        
        cmd = ConfigCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "test_value" in captured.out
    
    def test_config_command_set_value(self, basic_args, mock_config_manager):
        """Test config command set value."""
        # Set flag-style attributes for config command
        basic_args.list = False
        basic_args.get = False
        basic_args.set = True
        basic_args.unset = False
        basic_args.key = "api.url"
        basic_args.value = "http://new-url:11434"
        
        cmd = ConfigCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0
        mock_config_manager.set.assert_called_once_with("api.url", "http://new-url:11434")
    
    def test_config_command_unset_value(self, basic_args, mock_config_manager):
        """Test config command unset value."""
        # Set flag-style attributes for config command
        basic_args.list = False
        basic_args.get = False
        basic_args.set = False
        basic_args.unset = True
        basic_args.key = "api.url"
        basic_args.value = None
        
        # Mock unset to not raise any errors
        mock_config_manager.unset.return_value = None
        
        cmd = ConfigCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0
        mock_config_manager.unset.assert_called_once_with("api.url")
    
    def test_config_command_default_list(self, basic_args, mock_config_manager):
        """Test config command defaults to list when no operation specified."""
        # Since no operation defaults to list, mock list properly
        mock_config_manager.list.return_value = {"api.url": "http://localhost:11434"}
        
        # No flags set - should default to list
        basic_args.list = False
        basic_args.get = False
        basic_args.set = False
        basic_args.unset = False
        basic_args.key = None
        basic_args.value = None
        
        cmd = ConfigCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 0  # Should succeed with list action


class TestConfigCommandIsolated:
    """Integration tests for ConfigCommand using isolated configuration."""
    
    def test_config_command_with_isolated_manager(self, basic_args, isolated_config_manager):
        """Test config command with fully isolated configuration."""
        # Verify initial state
        initial_config = isolated_config_manager.list()
        assert "api.url" in initial_config
        assert initial_config["api.url"] == "https://api.example.test"
        
        # Set flag-style attributes for config command
        basic_args.list = False
        basic_args.get = False
        basic_args.set = True
        basic_args.unset = False
        basic_args.key = "test.isolation"
        basic_args.value = "working"
        
        cmd = ConfigCommand(basic_args, isolated_config_manager)
        result = cmd.run()
        
        assert result == 0
        assert isolated_config_manager.get("test.isolation") == "working"
    
    def test_config_isolation_between_tests(self, basic_args, isolated_config_manager):
        """Test that configuration is properly isolated between tests."""
        # This test should not see changes from the previous test
        config = isolated_config_manager.list()
        
        # Should have default test config, not modifications from other tests
        assert "test.isolation" not in config
        assert config["api.url"] == "https://api.example.test"


class TestCommandErrorHandling:
    """Test error handling across all commands."""
    
    @patch('giv.commands.base.GitRepository')
    def test_command_git_error_handling(self, mock_git_cls, basic_args, mock_config_manager):
        """Test command handling of Git errors."""
        mock_git = Mock()
        mock_git.get_diff.side_effect = Exception("Git command failed")
        mock_git_cls.return_value = mock_git
        
        cmd = MessageCommand(basic_args, mock_config_manager)
        result = cmd.run()
        
        assert result == 1  # Generic error
    
    @patch('giv.commands.base.LLMClient')
    def test_command_llm_empty_response(self, mock_llm_cls, basic_args, mock_config_manager):
        """Test command handling of empty LLM response."""
        with patch('giv.commands.base.GitRepository'), \
             patch('giv.commands.base.TemplateEngine') as mock_template_cls:
            
            mock_template = Mock()
            mock_template.render_template_file.return_value = "template"
            mock_template_cls.return_value = mock_template
            
            mock_llm = Mock()
            mock_llm.generate.return_value = {"content": ""}  # Empty response
            mock_llm_cls.return_value = mock_llm
            
            cmd = MessageCommand(basic_args, mock_config_manager)
            result = cmd.run()
            
            assert result == 1  # Error due to no content
    
    def test_command_config_access_patterns(self, basic_args, mock_config_manager):
        """Test command configuration access patterns."""
        # Test that commands access config correctly
        mock_config_manager.get.side_effect = lambda key: {
            "api_url": "http://localhost:11434",
            "api_key": "test_key",
            "api_model": "llama3.2",
            "temperature": "0.8",
            "max_tokens": "4096"
        }.get(key)
        
        cmd = MessageCommand(basic_args, mock_config_manager)
        
        with patch('giv.commands.base.GitRepository'), \
             patch('giv.commands.base.TemplateEngine'), \
             patch('giv.commands.base.LLMClient') as mock_llm_cls:
            
            llm_client = cmd.create_llm_client()
            
            # Verify LLMClient was called with config values
            mock_llm_cls.assert_called_once()
            call_args = mock_llm_cls.call_args
            assert call_args[1]['api_url'] == "http://localhost:11434"
            assert call_args[1]['api_key'] == "test_key"
            assert call_args[1]['model'] == "llama3.2"