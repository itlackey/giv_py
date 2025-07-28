"""
Comprehensive tests for lib.templates module.

Tests template discovery, loading, rendering, and error handling.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from giv.lib.templates import TemplateEngine, render_template
from giv.errors import TemplateError
from giv.constants import TEMPLATES_DIR


class TestTemplateEngineInit:
    """Test TemplateEngine initialization."""
    
    def test_template_engine_default_init(self):
        """Test TemplateEngine with default template directory."""
        engine = TemplateEngine()
        assert engine.template_dir is None
        assert engine.base_template_dir.name == TEMPLATES_DIR
    
    def test_template_engine_custom_init(self):
        """Test TemplateEngine with custom template directory."""
        custom_dir = Path("/custom/templates")
        engine = TemplateEngine(custom_dir)
        assert engine.template_dir == custom_dir


class TestTemplateDiscovery:
    """Test template file discovery."""
    
    def test_find_template_file_custom_dir(self):
        """Test finding template in custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "test_template.md"
            template_file.write_text("Custom template")
            
            engine = TemplateEngine(template_dir)
            found_path = engine.find_template_file("test_template.md")
            
            assert found_path == template_file
            assert found_path.exists()
    
    def test_find_template_file_project_level(self):
        """Test finding template in project .giv/templates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project structure
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()
            giv_dir = project_dir / ".giv" / TEMPLATES_DIR
            giv_dir.mkdir(parents=True)
            template_file = giv_dir / "test_template.md"
            template_file.write_text("Project template")
            
            # Change to project directory
            with patch('pathlib.Path.cwd', return_value=project_dir):
                engine = TemplateEngine()
                found_path = engine.find_template_file("test_template.md")
                
                assert found_path == template_file
    
    def test_find_template_file_user_level(self):
        """Test finding template in user ~/.giv/templates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            user_home = Path(tmpdir)
            giv_dir = user_home / ".giv" / TEMPLATES_DIR
            giv_dir.mkdir(parents=True)
            template_file = giv_dir / "test_template.md"
            template_file.write_text("User template")
            
            with patch('pathlib.Path.home', return_value=user_home), \
                 patch('pathlib.Path.cwd', return_value=Path("/other/dir")):
                engine = TemplateEngine()
                found_path = engine.find_template_file("test_template.md")
                
                assert found_path == template_file
    
    def test_find_template_file_system_level(self):
        """Test finding template in system templates directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the system templates directory
            system_templates_dir = Path(tmpdir) / TEMPLATES_DIR
            system_templates_dir.mkdir()
            template_file = system_templates_dir / "test_template.md"
            template_file.write_text("System template")
            
            with patch.object(Path, 'parent', new_callable=lambda: property(lambda self: Path(tmpdir))):
                engine = TemplateEngine()
                # Directly set the base template dir for testing
                engine.base_template_dir = system_templates_dir
                found_path = engine.find_template_file("test_template.md")
                
                assert found_path == template_file
    
    def test_find_template_file_not_found(self):
        """Test template not found raises error."""
        engine = TemplateEngine()
        
        with pytest.raises(TemplateError, match="Template not found"):
            engine.find_template_file("nonexistent_template.md")
    
    def test_find_template_file_precedence(self):
        """Test template discovery precedence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create custom directory (highest precedence)
            custom_dir = Path(tmpdir) / "custom"
            custom_dir.mkdir()
            custom_template = custom_dir / "test.md"
            custom_template.write_text("Custom")
            
            # Create project directory  
            project_dir = Path(tmpdir) / "project"
            giv_dir = project_dir / ".giv" / TEMPLATES_DIR
            giv_dir.mkdir(parents=True)
            project_template = giv_dir / "test.md"
            project_template.write_text("Project")
            
            with patch('pathlib.Path.cwd', return_value=project_dir):
                engine = TemplateEngine(custom_dir)
                found_path = engine.find_template_file("test.md")
                
                # Should find custom template (highest precedence)
                assert found_path == custom_template
                assert found_path.read_text() == "Custom"


class TestTemplateLoading:
    """Test template loading functionality."""
    
    def test_load_template_success(self):
        """Test successful template loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "test.md"
            template_content = "Hello {NAME}!"
            template_file.write_text(template_content)
            
            engine = TemplateEngine(template_dir)
            loaded_content = engine.load_template("test.md")
            
            assert loaded_content == template_content
    
    def test_load_template_file_not_found(self):
        """Test loading non-existent template."""
        engine = TemplateEngine()
        
        with pytest.raises(TemplateError, match="Template not found"):
            engine.load_template("nonexistent.md")
    
    def test_load_template_permission_error(self):
        """Test loading template with permission error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "test.md"
            template_file.write_text("test content")
            
            engine = TemplateEngine(template_dir)
            
            with patch.object(Path, 'read_text', side_effect=PermissionError()):
                with pytest.raises(TemplateError, match="Template not found"):
                    engine.load_template("test.md")


class TestTemplateRendering:
    """Test template rendering functionality."""
    
    def test_render_template_simple_substitution(self):
        """Test simple token substitution."""
        engine = TemplateEngine()
        template = "Hello {NAME}!"
        context = {"NAME": "World"}
        
        result = engine.render_template(template, context)
        assert result == "Hello World!"
    
    def test_render_template_multiple_tokens(self):
        """Test multiple token substitution."""
        engine = TemplateEngine()
        template = "Project: {PROJECT}, Version: {VERSION}, Author: {AUTHOR}"
        context = {
            "PROJECT": "giv-cli",
            "VERSION": "1.0.0", 
            "AUTHOR": "Developer"
        }
        
        result = engine.render_template(template, context)
        assert result == "Project: giv-cli, Version: 1.0.0, Author: Developer"
    
    def test_render_template_repeated_tokens(self):
        """Test repeated token substitution."""
        engine = TemplateEngine()
        template = "{NAME} says hello to {NAME}"
        context = {"NAME": "Alice"}
        
        result = engine.render_template(template, context)
        assert result == "Alice says hello to Alice"
    
    def test_render_template_missing_token(self):
        """Test handling of missing tokens."""
        engine = TemplateEngine()
        template = "Hello {NAME}! Your score is {SCORE}."
        context = {"NAME": "Alice"}  # Missing SCORE
        
        result = engine.render_template(template, context)
        # Missing tokens should remain unchanged
        assert result == "Hello Alice! Your score is {SCORE}."
    
    def test_render_template_empty_context(self):
        """Test rendering with empty context."""
        engine = TemplateEngine()
        template = "Hello {NAME}!"
        context = {}
        
        result = engine.render_template(template, context)
        assert result == "Hello {NAME}!"  # Token unchanged
    
    def test_render_template_no_tokens(self):
        """Test rendering template with no tokens."""
        engine = TemplateEngine()
        template = "This is a plain template without tokens."
        context = {"NAME": "Alice"}
        
        result = engine.render_template(template, context)
        assert result == template  # Unchanged
    
    def test_render_template_special_characters(self):
        """Test rendering with special characters."""
        engine = TemplateEngine()
        template = "Message: {MESSAGE}"
        context = {"MESSAGE": "Special chars: éñü 🚀 $@#%"}
        
        result = engine.render_template(template, context)
        assert result == "Message: Special chars: éñü 🚀 $@#%"
    
    def test_render_template_multiline(self):
        """Test rendering multiline template."""
        engine = TemplateEngine()
        template = """# {TITLE}

Author: {AUTHOR}
Date: {DATE}

## Summary

{SUMMARY}"""
        context = {
            "TITLE": "Test Document",
            "AUTHOR": "John Doe", 
            "DATE": "2025-01-28",
            "SUMMARY": "This is a test document."
        }
        
        result = engine.render_template(template, context)
        assert "# Test Document" in result
        assert "Author: John Doe" in result
        assert "This is a test document." in result


class TestTemplateFileRendering:
    """Test rendering template files."""
    
    def test_render_template_file_success(self):
        """Test successful template file rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "test.md"
            template_file.write_text("Hello {NAME}!")
            
            engine = TemplateEngine(template_dir)
            result = engine.render_template_file("test.md", {"NAME": "World"})
            
            assert result == "Hello World!"
    
    def test_render_template_file_complex(self):
        """Test rendering complex template file."""
        template_content = """# Commit Message

Project: {PROJECT_TITLE}
Version: {VERSION}
Branch: {BRANCH}

## Changes

{SUMMARY}

## Metadata

Commit: {COMMIT_ID}
Date: {DATE}"""
        
        context = {
            "PROJECT_TITLE": "giv-cli",
            "VERSION": "1.0.0",
            "BRANCH": "main",
            "SUMMARY": "Added new features",
            "COMMIT_ID": "abc123",
            "DATE": "2025-01-28"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "commit.md"
            template_file.write_text(template_content)
            
            engine = TemplateEngine(template_dir)
            result = engine.render_template_file("commit.md", context)
            
            assert "Project: giv-cli" in result
            assert "Version: 1.0.0" in result
            assert "Added new features" in result
            assert "Commit: abc123" in result


class TestTemplateValidation:
    """Test template validation functionality."""
    
    def test_validate_template_success(self):
        """Test successful template validation."""
        engine = TemplateEngine()
        template = "Hello {NAME}! Your score is {SCORE}."
        
        result = engine.validate_template(template)
        
        assert result["valid"] is True
        assert result["tokens"] == ["NAME", "SCORE"]
        assert len(result["issues"]) == 0
    
    def test_validate_template_no_tokens(self):
        """Test validating template with no tokens."""
        engine = TemplateEngine()
        template = "This is a plain template."
        
        result = engine.validate_template(template)
        
        assert result["valid"] is True
        assert result["tokens"] == []
        assert len(result["issues"]) == 0
    
    def test_validate_template_malformed_tokens(self):
        """Test validating template with malformed tokens."""
        engine = TemplateEngine()
        template = "Hello {NAME! Missing closing brace."
        
        result = engine.validate_template(template)
        
        assert result["valid"] is True  # Still valid, just won't substitute
        assert "NAME" not in result["tokens"]  # Malformed token not detected
    
    def test_validate_template_duplicate_tokens(self):
        """Test validating template with duplicate tokens."""
        engine = TemplateEngine()
        template = "Hello {NAME}! Goodbye {NAME}!"
        
        result = engine.validate_template(template)
        
        assert result["valid"] is True
        assert "NAME" in result["tokens"]
        assert result["tokens"].count("NAME") == 1  # Duplicates removed


class TestTemplateListAvailable:
    """Test listing available templates."""
    
    def test_list_available_templates_empty(self):
        """Test listing when no templates available."""
        with patch('pathlib.Path.home', return_value=Path("/nonexistent")), \
             patch('pathlib.Path.cwd', return_value=Path("/nonexistent")):
            engine = TemplateEngine()
            
            # Mock system templates directory to be empty
            with patch.object(engine, 'base_template_dir', Path("/nonexistent")):
                templates = engine.list_available_templates()
                assert templates == {}
    
    def test_list_available_templates_multiple_sources(self):
        """Test listing templates from multiple sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create system templates
            system_dir = Path(tmpdir) / "system" / TEMPLATES_DIR
            system_dir.mkdir(parents=True)
            (system_dir / "system.md").write_text("System template")
            
            # Create user templates
            user_home = Path(tmpdir) / "user"
            user_giv = user_home / ".giv" / TEMPLATES_DIR
            user_giv.mkdir(parents=True)
            (user_giv / "user.md").write_text("User template")
            (user_giv / "override.md").write_text("User override")
            
            # Create project templates
            project_dir = Path(tmpdir) / "project"
            project_giv = project_dir / ".giv" / TEMPLATES_DIR
            project_giv.mkdir(parents=True)
            (project_giv / "project.md").write_text("Project template")
            (project_giv / "override.md").write_text("Project override")
            
            with patch('pathlib.Path.home', return_value=user_home), \
                 patch('pathlib.Path.cwd', return_value=project_dir):
                engine = TemplateEngine()
                engine.base_template_dir = system_dir
                
                templates = engine.list_available_templates()
                
                # Should have templates from all sources
                assert "system.md" in templates
                assert "user.md" in templates
                assert "project.md" in templates
                assert "override.md" in templates
                
                # Project should override user template
                assert templates["override.md"] == project_giv / "override.md"
    
    def test_list_available_templates_custom_dir(self):
        """Test listing templates with custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir)
            (custom_dir / "custom1.md").write_text("Custom 1")
            (custom_dir / "custom2.md").write_text("Custom 2")
            
            engine = TemplateEngine(custom_dir)
            templates = engine.list_available_templates()
            
            assert "custom1.md" in templates
            assert "custom2.md" in templates
            assert templates["custom1.md"] == custom_dir / "custom1.md"


class TestRenderTemplateFunction:
    """Test the standalone render_template function."""
    
    def test_render_template_function_success(self):
        """Test render_template function success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            template_file = template_dir / "test.md"
            template_file.write_text("Hello {NAME}!")
            
            # Create a default engine with custom directory
            with patch('giv.lib.templates.default_template_engine') as mock_engine:
                mock_engine.render_template_file.return_value = "Hello World!"
                
                result = render_template("test.md", {"NAME": "World"})
                assert result == "Hello World!"
                mock_engine.render_template_file.assert_called_once_with("test.md", {"NAME": "World"})
    
    def test_render_template_function_error(self):
        """Test render_template function error handling."""
        with patch('giv.lib.templates.default_template_engine') as mock_engine:
            mock_engine.render_template_file.side_effect = TemplateError("Template not found")
            
            with pytest.raises(TemplateError):
                render_template("nonexistent.md", {})


class TestTemplateErrorHandling:
    """Test template error handling scenarios."""
    
    def test_template_engine_with_invalid_path(self):
        """Test TemplateEngine with invalid custom path."""
        invalid_path = Path("/nonexistent/invalid/path")
        engine = TemplateEngine(invalid_path)
        
        # Should still initialize but fail on template loading
        with pytest.raises(TemplateError):
            engine.load_template("test.md")
    
    def test_template_rendering_edge_cases(self):
        """Test template rendering edge cases."""
        engine = TemplateEngine()
        
        # Empty template
        assert engine.render_template("", {"NAME": "test"}) == ""
        
        # Template with only tokens
        assert engine.render_template("{NAME}", {"NAME": "Alice"}) == "Alice"
        
        # Template with nested braces (should not substitute)
        result = engine.render_template("{{NAME}}", {"NAME": "Alice"})
        assert result == "{{NAME}}"  # Nested braces not supported
        
        # Context with non-string values
        result = engine.render_template("Count: {COUNT}", {"COUNT": 42})
        assert result == "Count: 42"
        
        # Context with None values
        result = engine.render_template("Value: {VALUE}", {"VALUE": None})
        assert result == "Value: None"