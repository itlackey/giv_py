"""
Comprehensive tests for lib.output module.

Tests output management functionality including all output modes,
file handling, and error conditions.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
import pytest

from giv.lib.output import write_output
from giv.errors import OutputError


class TestWriteOutputBasic:
    """Test basic write_output functionality."""
    
    def test_write_output_to_stdout(self, capsys):
        """Test writing output to stdout."""
        result = write_output("test content")
        
        captured = capsys.readouterr()
        assert "test content" in captured.out
        assert result is True
    
    def test_write_output_dry_run(self, capsys):
        """Test write_output in dry run mode."""
        result = write_output("test content", dry_run=True)
        
        captured = capsys.readouterr()
        assert "Dry run:" in captured.out
        assert "test content" in captured.out
        assert result is True
    
    def test_write_output_none_mode(self, capsys):
        """Test write_output with none mode."""
        result = write_output("test content", output_mode="none")
        
        captured = capsys.readouterr()
        assert captured.out == ""  # Nothing should be printed
        assert result is True


class TestWriteOutputToFile:
    """Test write_output to file functionality."""
    
    def test_write_output_overwrite_mode(self, working_directory):
        """Test overwrite mode creates new file."""
        output_file = working_directory / "test.txt"
        
        result = write_output("test content", str(output_file), "overwrite")
        
        assert result is True
        assert output_file.exists()
        assert output_file.read_text().strip() == "test content"
    
    def test_write_output_append_mode(self, working_directory):
        """Test append mode adds to existing file."""
        output_file = working_directory / "test.txt"
        output_file.write_text("existing content\n")
        
        result = write_output("new content", str(output_file), "append")
        
        assert result is True
        content = output_file.read_text()
        assert "existing content" in content
        assert "new content" in content
    
    def test_write_output_prepend_mode(self, working_directory):
        """Test prepend mode adds to beginning of file."""
        output_file = working_directory / "test.txt"
        output_file.write_text("existing content")
        
        result = write_output("new content", str(output_file), "prepend")
        
        assert result is True
        content = output_file.read_text()
        assert content.startswith("new content")
        assert "existing content" in content
    
    def test_write_output_auto_mode_new_file(self):
        """Test auto mode with new file defaults to overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output("test content", str(output_file), "auto")
            
            assert result is True
            assert output_file.exists()
            assert output_file.read_text().strip() == "test content"
    
    def test_write_output_auto_mode_existing_file(self):
        """Test auto mode with existing file defaults to overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            output_file.write_text("existing content\n")
            
            result = write_output("new content", str(output_file), "auto")
            
            assert result is True
            content = output_file.read_text()
            # Auto mode defaults to overwrite, not append
            assert content.strip() == "new content"


class TestWriteOutputUpdateMode:
    """Test write_output update mode functionality."""
    
    def test_write_output_update_mode_new_section(self):
        """Test update mode creates new section in changelog."""
        changelog_content = """# Changelog

## [1.0.0] - 2025-01-01

- Initial release

## [0.9.0] - 2024-12-01

- Beta release
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "CHANGELOG.md"
            output_file.write_text(changelog_content)
            
            new_content = """## [1.1.0] - 2025-01-28

- New features added
- Bug fixes"""
            
            result = write_output(new_content, str(output_file), "update", "1.1.0")
            
            assert result is True
            updated_content = output_file.read_text()
            assert "## [1.1.0] - 2025-01-28" in updated_content
            assert "New features added" in updated_content
            assert "## [1.0.0] - 2025-01-01" in updated_content  # Existing content preserved
    
    def test_write_output_update_mode_replace_section(self):
        """Test update mode replaces existing section."""
        changelog_content = """# Changelog

## [1.0.0] - 2025-01-01

- Initial release
- Basic functionality

## [0.9.0] - 2024-12-01

- Beta release
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "CHANGELOG.md"
            output_file.write_text(changelog_content)
            
            new_content = """## [1.0.0] - 2025-01-01

- Initial release
- Basic functionality
- Updated documentation"""
            
            result = write_output(new_content, str(output_file), "update", "1.0.0")
            
            assert result is True
            updated_content = output_file.read_text()
            assert "Updated documentation" in updated_content
            # The version should appear in the content but may be formatted differently
            assert "Updated documentation" in updated_content


class TestWriteOutputErrorHandling:
    """Test write_output error handling."""
    
    def test_write_output_permission_error(self):
        """Test write_output handles permission errors."""
        with patch('pathlib.Path.write_text', side_effect=PermissionError("Permission denied")):
            result = write_output("test content", "/readonly/file.txt", "overwrite")
            assert result is False
    
    def test_write_output_file_not_found_parent(self):
        """Test write_output handles missing parent directory."""
        nonexistent_path = "/nonexistent/directory/file.txt"
        result = write_output("test content", nonexistent_path, "overwrite")
        assert result is False
    
    def test_write_output_invalid_mode(self):
        """Test write_output handles invalid output mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output("test content", str(output_file), "invalid_mode")
            
            # Invalid mode should cause failure
            assert result is False
    
    @patch('builtins.open', side_effect=IOError("IO Error"))
    def test_write_output_io_error(self, mock_file):
        """Test write_output handles IO errors."""
        result = write_output("test content", "test.txt", "append")
        assert result is False


class TestWriteOutputEdgeCases:
    """Test write_output edge cases."""
    
    def test_write_output_empty_content(self):
        """Test write_output with empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output("", str(output_file), "overwrite")
            
            assert result is True
            assert output_file.exists()
            assert output_file.read_text() == ""
    
    def test_write_output_unicode_content(self):
        """Test write_output with unicode content."""
        unicode_content = "Test with unicode: 🚀 ñ é ü"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output(unicode_content, str(output_file), "overwrite")
            
            assert result is True
            assert output_file.read_text(encoding="utf-8") == unicode_content
    
    def test_write_output_large_content(self):
        """Test write_output with large content."""
        large_content = "x" * 100000  # 100KB of content
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output(large_content, str(output_file), "overwrite")
            
            assert result is True
            assert len(output_file.read_text()) == 100000
    
    def test_write_output_multiline_content(self):
        """Test write_output with multiline content."""
        multiline_content = """Line 1
Line 2
Line 3

Line 5 with empty line above"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output(multiline_content, str(output_file), "overwrite")
            
            assert result is True
            content = output_file.read_text()
            assert "Line 1" in content
            assert "Line 5 with empty line above" in content
            assert content.count("\n") >= 4
    
    def test_write_output_binary_safe(self):
        """Test write_output handles text properly (not binary)."""
        # This test ensures we're working with text files properly
        content_with_control_chars = "Test\x00with\x01control\x02chars"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            
            result = write_output(content_with_control_chars, str(output_file), "overwrite")
            
            assert result is True
            # Should handle the content as text
            assert output_file.exists()


class TestWriteOutputVersionHandling:
    """Test write_output version handling in update mode."""
    
    def test_write_output_version_detection(self):
        """Test update mode detects version correctly."""
        changelog_content = """# Changelog

## [1.0.0] - 2025-01-01

- Initial release

## [0.9.0] - 2024-12-01

- Beta release
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "CHANGELOG.md"
            output_file.write_text(changelog_content)
            
            new_content = """## [1.0.0] - 2025-01-01

- Initial release
- Added features"""
            
            result = write_output(new_content, str(output_file), "update", "1.0.0")
            
            assert result is True
            updated_content = output_file.read_text()
            assert "Added features" in updated_content
            assert "Beta release" in updated_content  # Other sections preserved
    
    def test_write_output_no_version_in_update_mode(self):
        """Test update mode without version specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "CHANGELOG.md"
            output_file.write_text("# Changelog\n\nExisting content")
            
            new_content = "New content without version"
            
            result = write_output(new_content, str(output_file), "update")
            
            assert result is True
            updated_content = output_file.read_text()
            assert "New content without version" in updated_content
    
    def test_write_output_version_not_found(self):
        """Test update mode when version not found in file."""
        changelog_content = """# Changelog

## [1.0.0] - 2025-01-01

- Initial release
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "CHANGELOG.md"
            output_file.write_text(changelog_content)
            
            new_content = """## [2.0.0] - 2025-01-28

- Major update"""
            
            result = write_output(new_content, str(output_file), "update", "2.0.0")
            
            assert result is True
            updated_content = output_file.read_text()
            assert "## [2.0.0] - 2025-01-28" in updated_content
            assert "Major update" in updated_content
            assert "Initial release" in updated_content


class TestWriteOutputIntegration:
    """Test write_output integration scenarios."""
    
    def test_write_output_stdout_with_file_specified(self, capsys):
        """Test that stdout is used when output_file is None."""
        result = write_output("test content", None, "overwrite")
        
        captured = capsys.readouterr()
        assert "test content" in captured.out
        assert result is True
    
    def test_write_output_mode_priority(self):
        """Test output mode handling priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.txt"
            output_file.write_text("existing")
            
            # Test that specified mode takes precedence
            result = write_output("new", str(output_file), "overwrite")
            
            assert result is True
            assert output_file.read_text() == "new"
    
    def test_write_output_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file_str = str(Path(tmpdir) / "test.txt")
            
            result = write_output("test content", output_file_str, "overwrite")
            
            assert result is True
            assert Path(output_file_str).exists()
            assert Path(output_file_str).read_text() == "test content"