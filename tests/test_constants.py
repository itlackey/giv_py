"""
Comprehensive tests for constants module.

Tests all constants and their usage patterns.
"""
import pytest
from giv.constants import (
    # LLM settings
    DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, DEFAULT_API_TIMEOUT,
    TEMPERATURE_CREATIVE, TEMPERATURE_FACTUAL,
    
    # Output file defaults
    DEFAULT_CHANGELOG_FILE, DEFAULT_RELEASE_NOTES_FILE, DEFAULT_ANNOUNCEMENT_FILE,
    
    # Configuration keys
    CONFIG_API_URL, CONFIG_API_KEY, CONFIG_API_MODEL, CONFIG_TEMPERATURE,
    CONFIG_MAX_TOKENS, CONFIG_OUTPUT_MODE, CONFIG_OUTPUT_VERSION,
    CONFIG_CHANGELOG_FILE, CONFIG_RELEASE_NOTES_FILE, CONFIG_ANNOUNCEMENT_FILE,
    
    # Git revision defaults
    DEFAULT_REVISION,
    
    # Template names
    TEMPLATE_MESSAGE, TEMPLATE_SUMMARY, TEMPLATE_CHANGELOG,
    TEMPLATE_RELEASE_NOTES, TEMPLATE_ANNOUNCEMENT,
    
    # Output modes
    OUTPUT_MODE_AUTO, OUTPUT_MODE_APPEND, OUTPUT_MODE_PREPEND,
    OUTPUT_MODE_UPDATE, OUTPUT_MODE_OVERWRITE,
    
    # Buffer sizes
    BUFFER_SIZE_DEFAULT, BUFFER_SIZE_LARGE, BUFFER_SIZE_SMALL,
    
    # Environment and directories
    ENV_PREFIX, CONFIG_DIR, TEMPLATES_DIR
)


class TestLLMConstants:
    """Test LLM-related constants."""
    
    def test_default_temperature(self):
        """Test default temperature value."""
        assert DEFAULT_TEMPERATURE == 0.9
        assert isinstance(DEFAULT_TEMPERATURE, float)
    
    def test_default_max_tokens(self):
        """Test default max tokens value."""
        assert DEFAULT_MAX_TOKENS == 8192
        assert isinstance(DEFAULT_MAX_TOKENS, int)
    
    def test_default_api_timeout(self):
        """Test default API timeout value."""
        assert DEFAULT_API_TIMEOUT == 30
        assert isinstance(DEFAULT_API_TIMEOUT, int)
    
    def test_temperature_presets(self):
        """Test temperature preset values."""
        assert TEMPERATURE_CREATIVE == 0.9
        assert TEMPERATURE_FACTUAL == 0.7
        assert TEMPERATURE_CREATIVE > TEMPERATURE_FACTUAL
    
    def test_temperature_range(self):
        """Test temperature values are in valid range."""
        assert 0.0 <= TEMPERATURE_CREATIVE <= 1.0
        assert 0.0 <= TEMPERATURE_FACTUAL <= 1.0
        assert 0.0 <= DEFAULT_TEMPERATURE <= 1.0


class TestOutputFileConstants:
    """Test output file constants."""
    
    def test_default_file_names(self):
        """Test default output file names."""
        assert DEFAULT_CHANGELOG_FILE == "CHANGELOG.md"
        assert DEFAULT_RELEASE_NOTES_FILE == "RELEASE_NOTES.md"
        assert DEFAULT_ANNOUNCEMENT_FILE == "ANNOUNCEMENT.md"
    
    def test_file_extensions(self):
        """Test all default files have .md extension."""
        files = [DEFAULT_CHANGELOG_FILE, DEFAULT_RELEASE_NOTES_FILE, DEFAULT_ANNOUNCEMENT_FILE]
        for file in files:
            assert file.endswith(".md")
    
    def test_file_names_are_strings(self):
        """Test file names are strings."""
        files = [DEFAULT_CHANGELOG_FILE, DEFAULT_RELEASE_NOTES_FILE, DEFAULT_ANNOUNCEMENT_FILE]
        for file in files:
            assert isinstance(file, str)
            assert len(file) > 0


class TestConfigurationKeys:
    """Test configuration key constants."""
    
    def test_api_config_keys(self):
        """Test API configuration keys."""
        assert CONFIG_API_URL == "api.url"
        assert CONFIG_API_KEY == "api.key"
        assert CONFIG_API_MODEL == "api.model.name"
    
    def test_llm_config_keys(self):
        """Test LLM configuration keys."""
        assert CONFIG_TEMPERATURE == "api.model.temperature"
        assert CONFIG_MAX_TOKENS == "api.model.max_tokens"
    
    def test_output_config_keys(self):
        """Test output configuration keys."""
        assert CONFIG_OUTPUT_MODE == "output.mode"
        assert CONFIG_OUTPUT_VERSION == "output_version"
    
    def test_file_config_keys(self):
        """Test file-specific configuration keys."""
        assert CONFIG_CHANGELOG_FILE == "changelog.file"
        assert CONFIG_RELEASE_NOTES_FILE == "release_notes_file" 
        assert CONFIG_ANNOUNCEMENT_FILE == "announcement_file"
    
    def test_config_keys_consistency(self):
        """Test config keys follow naming convention."""
        keys = [
            CONFIG_API_URL, CONFIG_API_KEY, CONFIG_API_MODEL,
            CONFIG_TEMPERATURE, CONFIG_MAX_TOKENS, CONFIG_OUTPUT_MODE,
            CONFIG_OUTPUT_VERSION, CONFIG_CHANGELOG_FILE,
            CONFIG_RELEASE_NOTES_FILE, CONFIG_ANNOUNCEMENT_FILE
        ]
        
        for key in keys:
            assert isinstance(key, str)
            assert "_" in key or key.islower()  # snake_case or lowercase
            assert not key.startswith("_")
            assert not key.endswith("_")


class TestGitConstants:
    """Test Git-related constants."""
    
    def test_default_revision(self):
        """Test default Git revision."""
        assert DEFAULT_REVISION == "--current"
        assert isinstance(DEFAULT_REVISION, str)


class TestTemplateConstants:
    """Test template name constants."""
    
    def test_template_names(self):
        """Test template name values."""
        assert TEMPLATE_MESSAGE == "commit_message_prompt.md"
        assert TEMPLATE_SUMMARY == "summary_prompt.md"
        assert TEMPLATE_CHANGELOG == "changelog_prompt.md"
        assert TEMPLATE_RELEASE_NOTES == "release_notes_prompt.md"
        assert TEMPLATE_ANNOUNCEMENT == "announcement_prompt.md"
    
    def test_template_extensions(self):
        """Test all templates have .md extension."""
        templates = [
            TEMPLATE_MESSAGE, TEMPLATE_SUMMARY, TEMPLATE_CHANGELOG,
            TEMPLATE_RELEASE_NOTES, TEMPLATE_ANNOUNCEMENT
        ]
        for template in templates:
            assert template.endswith(".md")
    
    def test_template_naming_pattern(self):
        """Test template names follow naming pattern."""
        templates = [
            TEMPLATE_MESSAGE, TEMPLATE_SUMMARY, TEMPLATE_CHANGELOG,
            TEMPLATE_RELEASE_NOTES, TEMPLATE_ANNOUNCEMENT
        ]
        for template in templates:
            assert isinstance(template, str)
            assert "_prompt.md" in template or template == "summary_prompt.md"


class TestOutputModeConstants:
    """Test output mode constants."""
    
    def test_output_mode_values(self):
        """Test output mode values."""
        assert OUTPUT_MODE_AUTO == "auto"
        assert OUTPUT_MODE_APPEND == "append"
        assert OUTPUT_MODE_PREPEND == "prepend"
        assert OUTPUT_MODE_UPDATE == "update"
        assert OUTPUT_MODE_OVERWRITE == "overwrite"
    
    def test_output_modes_are_unique(self):
        """Test all output modes are unique."""
        modes = [
            OUTPUT_MODE_AUTO, OUTPUT_MODE_APPEND, OUTPUT_MODE_PREPEND,
            OUTPUT_MODE_UPDATE, OUTPUT_MODE_OVERWRITE
        ]
        assert len(modes) == len(set(modes))
    
    def test_output_modes_are_strings(self):
        """Test all output modes are strings."""
        modes = [
            OUTPUT_MODE_AUTO, OUTPUT_MODE_APPEND, OUTPUT_MODE_PREPEND,
            OUTPUT_MODE_UPDATE, OUTPUT_MODE_OVERWRITE
        ]
        for mode in modes:
            assert isinstance(mode, str)
            assert len(mode) > 0


class TestBufferSizeConstants:
    """Test buffer size constants."""
    
    def test_buffer_size_values(self):
        """Test buffer size values."""
        assert BUFFER_SIZE_DEFAULT == 4096
        assert BUFFER_SIZE_LARGE == 8192
        assert BUFFER_SIZE_SMALL == 2048
    
    def test_buffer_size_relationships(self):
        """Test buffer size relationships."""
        assert BUFFER_SIZE_SMALL < BUFFER_SIZE_DEFAULT < BUFFER_SIZE_LARGE
        assert BUFFER_SIZE_LARGE == 2 * BUFFER_SIZE_DEFAULT
        assert BUFFER_SIZE_DEFAULT == 2 * BUFFER_SIZE_SMALL
    
    def test_buffer_sizes_are_powers_of_two(self):
        """Test buffer sizes are powers of two."""
        sizes = [BUFFER_SIZE_SMALL, BUFFER_SIZE_DEFAULT, BUFFER_SIZE_LARGE]
        for size in sizes:
            assert isinstance(size, int)
            assert size > 0
            assert (size & (size - 1)) == 0  # Check if power of 2


class TestEnvironmentAndDirectoryConstants:
    """Test environment and directory constants."""
    
    def test_env_prefix(self):
        """Test environment prefix."""
        assert ENV_PREFIX == "GIV_"
        assert ENV_PREFIX.endswith("_")
        assert ENV_PREFIX.isupper()
    
    def test_config_dir(self):
        """Test configuration directory."""
        assert CONFIG_DIR == ".giv"
        assert CONFIG_DIR.startswith(".")
    
    def test_templates_dir(self):
        """Test templates directory."""
        assert TEMPLATES_DIR == "templates"
        assert isinstance(TEMPLATES_DIR, str)
        assert not TEMPLATES_DIR.startswith(".")


class TestConstantsIntegration:
    """Test integration and consistency across constants."""
    
    def test_temperature_constants_consistency(self):
        """Test temperature constants are consistent."""
        # Default should be creative temperature
        assert DEFAULT_TEMPERATURE == TEMPERATURE_CREATIVE
        
        # Both should be valid temperature values
        assert 0.0 <= TEMPERATURE_CREATIVE <= 1.0
        assert 0.0 <= TEMPERATURE_FACTUAL <= 1.0
    
    def test_file_and_config_key_consistency(self):
        """Test file defaults match config keys."""
        # Config keys should be related to default files
        assert "changelog" in CONFIG_CHANGELOG_FILE
        assert "release_notes" in CONFIG_RELEASE_NOTES_FILE
        assert "announcement" in CONFIG_ANNOUNCEMENT_FILE
    
    def test_all_constants_have_values(self):
        """Test all constants have non-None values."""
        import giv.constants as constants
        
        for name in dir(constants):
            if not name.startswith("_"):  # Skip private attributes
                value = getattr(constants, name)
                assert value is not None
                
                # Test that strings are not empty
                if isinstance(value, str):
                    assert len(value) > 0
                
                # Test that numbers are reasonable
                if isinstance(value, (int, float)):
                    assert value >= 0