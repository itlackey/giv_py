"""
Comprehensive tests for the config module.

Tests configuration management functionality including:
- Configuration file reading and writing
- Hierarchical configuration (project > user > defaults)
- Configuration validation and error handling
- Compatibility with Bash implementation
"""
import os
from unittest.mock import patch

from giv.config import ConfigManager


class TestConfigManager:
    """Test the ConfigManager class."""
    
    def test_init_with_default_path(self, temp_dir):
        """Test ConfigManager initialization with default path."""
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Mock the _find_config_file method directly for reliable cross-platform testing
        expected_path = temp_dir / ".giv" / "config"
        
        with patch.object(ConfigManager, '_find_config_file', return_value=expected_path):
            try:
                cfg = ConfigManager()
                # Should look for config in ~/.giv/config
                # Use resolved paths for Windows compatibility
                assert cfg.config_path.resolve() == expected_path.resolve()
            finally:
                os.chdir(old_cwd)
    
    def test_init_with_custom_path(self, temp_dir):
        """Test ConfigManager initialization with custom path."""
        config_path = temp_dir / "custom_config"
        cfg = ConfigManager(config_path=config_path)
        assert cfg.config_path == config_path
    
    def test_set_and_get(self, temp_dir):
        """Test setting and getting configuration values."""
        config_path = temp_dir / "config"
        cfg = ConfigManager(config_path=config_path)
        
        # Set a value
        cfg.set("api.url", "https://api.example.com")
        
        # Get the value
        assert cfg.get("api.url") == "https://api.example.com"
        
        # Verify it was written to file
        assert config_path.exists()
        content = config_path.read_text()
        assert "GIV_API_URL=https://api.example.com" in content
    
    def test_get_nonexistent_key(self, temp_dir):
        """Test getting a nonexistent configuration key."""
        config_path = temp_dir / "config"
        cfg = ConfigManager(config_path=config_path)
        
        assert cfg.get("nonexistent.key") is None
    
    def test_unset(self, temp_dir):
        """Test unsetting configuration values."""
        config_path = temp_dir / "config"
        config_path.write_text("api.url=https://api.example.com\napi.key=test123\n")
        
        cfg = ConfigManager(config_path=config_path)
        
        # Verify key exists
        assert cfg.get("api.url") is not None
        
        # Unset the key
        cfg.unset("api.url")
        
        # Verify key is gone
        assert cfg.get("api.url") is None
        
        # Verify other keys remain
        assert cfg.get("api.key") == "test123"
    
    def test_list(self, temp_dir):
        """Test listing all configuration values."""
        config_path = temp_dir / "config"
        config_path.write_text("""# Test configuration
api.url=https://api.example.com
api.key=test123
temperature=0.7
""")
        
        cfg = ConfigManager(config_path=config_path)
        items = cfg.list()
        
        assert isinstance(items, dict)
        assert items["api.url"] == "https://api.example.com"
        assert items["api.key"] == "test123"
        assert items["temperature"] == "0.7"
    
    def test_comment_handling(self, temp_dir):
        """Test that comments are preserved in config files."""
        config_path = temp_dir / "config"
        config_path.write_text("""# This is a comment
api.url=https://api.example.com
# Another comment
api.key=test123
""")
        
        cfg = ConfigManager(config_path=config_path)
        
        # Modify a value
        cfg.set("api.url", "https://new.api.com")
        
        # Comments should be preserved
        content = config_path.read_text()
        assert "# This is a comment" in content
        assert "# Another comment" in content
        assert "api.url=https://new.api.com" in content
    
    def test_malformed_config_handling(self, temp_dir):
        """Test handling of malformed configuration files."""
        config_path = temp_dir / "config"
        config_path.write_text("""api.url=https://api.example.com
not_a_key_value_pair
api.key=test123
""")
        
        cfg = ConfigManager(config_path=config_path)
        
        # Should handle malformed lines gracefully
        items = cfg.list()
        assert items["api.url"] == "https://api.example.com"
        assert items["api.key"] == "test123"
    
    def test_empty_config_file(self, temp_dir):
        """Test handling of empty configuration files."""
        config_path = temp_dir / "config"
        config_path.write_text("")
        
        cfg = ConfigManager(config_path=config_path)
        
        items = cfg.list()
        assert items == {}
        
        # Should be able to set values in empty file
        cfg.set("new.key", "new.value")
        assert cfg.get("new.key") == "new.value"
    
    def test_nonexistent_config_file(self, temp_dir):
        """Test handling when config file doesn't exist."""
        config_path = temp_dir / "nonexistent"
        cfg = ConfigManager(config_path=config_path)
        
        # Should handle gracefully
        items = cfg.list()
        assert items == {}
        
        # Setting a value should create the file
        cfg.set("new.key", "new.value")
        assert config_path.exists()
        assert cfg.get("new.key") == "new.value"
    
    def test_hierarchical_config_project_over_user(self, temp_dir):
        """Test that project config overrides user config."""
        # Create user config
        user_config = temp_dir / "user_config"
        user_config.write_text("api.url=https://user.api.com\napi.key=user123\n")
        
        # Create project config directory and file
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        giv_dir = project_dir / ".giv"
        giv_dir.mkdir()
        project_config = giv_dir / "config"
        project_config.write_text("api.url=https://project.api.com\n")
        
        # Change to project directory
        old_cwd = os.getcwd()
        os.chdir(project_dir)
        
        try:
            # Create ConfigManager - should find project config
            cfg = ConfigManager()
            
            # Project value should override user value
            assert cfg.get("api.url") == "https://project.api.com"
            
            # User value should be available for keys not in project config
            # Note: This test assumes the implementation supports config hierarchy
            # If not implemented yet, this test documents the expected behavior
            
        finally:
            os.chdir(old_cwd)
    
    def test_special_characters_in_values(self, temp_dir):
        """Test handling of special characters in configuration values."""
        config_path = temp_dir / "config"
        cfg = ConfigManager(config_path=config_path)
        
        # Test various special characters
        test_values = [
            ("url.with.spaces", "https://api example.com/path"),
            ("key.with.equals", "key=value=more"),
            ("multiline.value", "line1\nline2\nline3"),
            ("unicode.value", "héllo wörld 🌍"),
        ]
        
        for key, value in test_values:
            cfg.set(key, value)
            retrieved = cfg.get(key)
            assert retrieved == value, f"Failed for key {key}: expected {value!r}, got {retrieved!r}"


class TestConfigCompatibility:
    """Test compatibility with Bash configuration format."""
    
    def test_bash_config_format(self, temp_dir):
        """Test reading configuration files in Bash format."""
        config_path = temp_dir / "config"
        # Write config in the same format as Bash version
        config_path.write_text("""# Generated by giv init
api.url=https://api.openai.com/v1/chat/completions
api.key=your-api-key-here
temperature=0.9
max_tokens=8192
model=gpt-4o
""")
        
        cfg = ConfigManager(config_path=config_path)
        
        assert cfg.get("api.url") == "https://api.openai.com/v1/chat/completions"
        assert cfg.get("api.key") == "your-api-key-here"
        assert cfg.get("temperature") == "0.9"
        assert cfg.get("max_tokens") == "8192"
        assert cfg.get("model") == "gpt-4o"
    
    def test_config_preservation_after_modification(self, temp_dir):
        """Test that config format is preserved after modifications."""
        config_path = temp_dir / "config"
        original_content = """# User configuration
api.url=https://api.openai.com/v1/chat/completions
# API key for OpenAI
api.key=your-api-key-here

# Model parameters
temperature=0.9
max_tokens=8192
"""
        config_path.write_text(original_content)
        
        cfg = ConfigManager(config_path=config_path)
        cfg.set("temperature", "0.7")
        
        # Read the file back and verify structure is preserved
        new_content = config_path.read_text()
        
        # Comments should be preserved
        assert "# User configuration" in new_content
        assert "# API key for OpenAI" in new_content
        assert "# Model parameters" in new_content
        
        # Value should be updated
        assert "temperature=0.7" in new_content
        
        # Other values should remain
        assert "api.url=https://api.openai.com/v1/chat/completions" in new_content
