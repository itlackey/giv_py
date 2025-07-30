"""
Tests for TODO scanning functionality.

This module tests the TODO scanning and extraction utilities.
"""
import pytest
import tempfile
from pathlib import Path

from giv.lib.todo import TodoScanner, scan_todos


class TestTodoScanner:
    """Test TodoScanner class functionality."""
    
    def test_scanner_initialization(self):
        """Test TodoScanner initialization with defaults."""
        scanner = TodoScanner()
        assert scanner.pattern == "TODO|FIXME|XXX"
        assert scanner.file_pattern == "**/*"
        assert scanner.regex.pattern == "TODO|FIXME|XXX"
    
    def test_scanner_custom_pattern(self):
        """Test TodoScanner with custom patterns."""
        scanner = TodoScanner(pattern="HACK|BUG", file_pattern="*.py")
        assert scanner.pattern == "HACK|BUG"
        assert scanner.file_pattern == "*.py"
    
    def test_binary_file_detection(self):
        """Test binary file detection."""
        scanner = TodoScanner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create text file
            text_file = tmpdir / "test.py"
            text_file.write_text("# TODO: implement this")
            assert not scanner._is_binary_file(text_file)
            
            # Create binary-like file with null bytes
            binary_file = tmpdir / "test.bin"
            binary_file.write_bytes(b"\\x00\\x01\\x02\\x03")
            assert scanner._is_binary_file(binary_file)
            
            # Test by extension
            jpg_file = tmpdir / "test.jpg"
            jpg_file.write_text("fake jpg")
            assert scanner._is_binary_file(jpg_file)
    
    def test_scan_single_file(self):
        """Test scanning a single file for TODOs."""
        scanner = TodoScanner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name
            f.write("""# TODO: implement feature A
def function():
    # FIXME: this is broken
    pass
    
# XXX: remove this hack
print("hello")
""")
            f.flush()
        
        try:
            todos = scanner.scan_file(Path(temp_path))
            
            assert len(todos) == 3
            assert todos[0] == (1, "# TODO: implement feature A")
            assert todos[1] == (3, "# FIXME: this is broken")  # No indentation in stripped line
            assert todos[2] == (6, "# XXX: remove this hack")
        finally:
            # Clean up the temporary file
            Path(temp_path).unlink(missing_ok=True)
    
    def test_scan_directory(self):
        """Test scanning a directory for TODOs."""
        scanner = TodoScanner(pattern="TODO", file_pattern="*.py")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create Python file with TODO
            py_file = tmpdir / "test.py"
            py_file.write_text("# TODO: test todo\nprint('hello')")
            
            # Create JS file with TODO (should be ignored)
            js_file = tmpdir / "test.js" 
            js_file.write_text("// TODO: js todo\nconsole.log('hello');")
            
            todos_by_file = scanner.scan_directory(tmpdir)
            
            assert len(todos_by_file) == 1
            assert "test.py" in todos_by_file
            assert todos_by_file["test.py"] == [(1, "# TODO: test todo")]
    
    def test_format_todos(self):
        """Test formatting TODO items."""
        scanner = TodoScanner()
        
        todos_by_file = {
            "file1.py": [(1, "# TODO: item 1"), (5, "# FIXME: item 2")],
            "file2.py": [(10, "# XXX: item 3")]
        }
        
        formatted = scanner.format_todos(todos_by_file)
        
        assert "## TODO Items" in formatted
        assert "### file1.py" in formatted
        assert "### file2.py" in formatted
        assert "Line 1: # TODO: item 1" in formatted
        assert "Line 5: # FIXME: item 2" in formatted
        assert "Line 10: # XXX: item 3" in formatted
    
    def test_empty_todos(self):
        """Test handling of empty TODO results."""
        scanner = TodoScanner()
        
        formatted = scanner.format_todos({})
        assert formatted == ""


class TestScanTodosFunction:
    """Test the convenience scan_todos function."""
    
    def test_scan_todos_convenience_function(self):
        """Test the scan_todos convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create file with TODO
            test_file = tmpdir / "test.py"
            test_file.write_text("# TODO: test convenience function")
            
            result = scan_todos(pattern="TODO", file_pattern="*.py", directory=tmpdir)
            
            assert "## TODO Items" in result
            assert "test.py" in result
            assert "TODO: test convenience function" in result
    
    def test_scan_todos_no_results(self):
        """Test scan_todos with no matching items."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create file without TODOs using a pattern that won't match
            test_file = tmpdir / "test.py"
            test_file.write_text("print('no todos here')")
            
            result = scan_todos(pattern="NONEXISTENT", file_pattern="*.py", directory=tmpdir)
            
            assert result == ""


class TestTodoPatternMatching:
    """Test various TODO pattern matching scenarios."""
    
    def test_case_insensitive_matching(self):
        """Test that TODO patterns are case insensitive."""
        scanner = TodoScanner(pattern="todo")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
            f.write("# TODO: uppercase\n# todo: lowercase\n# Todo: mixed case")
            f.flush()
        
        try:
            todos = scanner.scan_file(Path(temp_path))
            assert len(todos) == 3
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_custom_patterns(self):
        """Test custom TODO patterns."""
        scanner = TodoScanner(pattern="HACK|BUG|NOTE")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
            f.write("# HACK: dirty hack\n# BUG: known bug\n# NOTE: important note\n# TODO: ignored")
            f.flush()
        
        try:
            todos = scanner.scan_file(Path(temp_path))
            
            assert len(todos) == 3
            assert any("HACK" in todo[1] for todo in todos)
            assert any("BUG" in todo[1] for todo in todos)
            assert any("NOTE" in todo[1] for todo in todos)
            assert not any("TODO: ignored" in todo[1] for todo in todos)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_complex_regex_patterns(self):
        """Test complex regex patterns."""
        # Test pattern that matches TODO with optional username
        scanner = TodoScanner(pattern=r"TODO\([^)]+\)|TODO")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
            f.write("# TODO(alice): assigned todo\n# TODO: unassigned todo")
            f.flush()
        
        try:
            todos = scanner.scan_file(Path(temp_path))
            assert len(todos) == 2
        finally:
            Path(temp_path).unlink(missing_ok=True)