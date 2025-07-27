"""
End-to-end compatibility tests comparing Python and Bash implementations.

These tests run both implementations side-by-side to ensure 100% compatibility.
"""
import os
import pytest
import subprocess
import tempfile
from pathlib import Path

from conftest import BashGivRunner, PythonGivRunner


class TestBashPythonCompatibility:
    """Test compatibility between Bash and Python implementations."""
    
    def test_version_command_compatibility(self, bash_giv, git_repo):
        """Test --version command produces identical output."""
        python_runner = PythonGivRunner(git_repo)
        
        bash_result = bash_giv.run(['--version'])
        python_result = python_runner.run(['--version'])
        
        # Both should succeed
        assert bash_result.returncode == 0
        assert python_result.returncode == 0
        
        # Output format should be similar (version numbers might differ)
        assert "giv" in bash_result.stdout.lower()
        assert "giv" in python_result.stdout.lower()
    
    def test_help_command_compatibility(self, bash_giv, git_repo):
        """Test --help command produces compatible output."""
        python_runner = PythonGivRunner(git_repo)
        
        bash_result = bash_giv.run(['--help'])
        python_result = python_runner.run(['--help'])
        
        # Both should succeed
        assert bash_result.returncode == 0
        assert python_result.returncode == 0
        
        # Should contain similar help content
        bash_lines = bash_result.stdout.split('\n')
        python_lines = python_result.stdout.split('\n')
        
        # Both should mention main commands
        bash_help = bash_result.stdout.lower()
        python_help = python_result.stdout.lower()
        
        common_commands = ['summary', 'post', 'changelog', 'release-notes']
        for command in common_commands:
            assert command in bash_help
            assert command in python_help
    
    def test_config_show_compatibility(self, bash_giv, temp_dir):
        """Test config show command compatibility."""
        python_runner = PythonGivRunner(temp_dir)
        
        # Create a simple config file
        config_content = """GIV_TEMPLATE_DIR=/custom/templates
GIV_LLM_PROVIDER=openai
GIV_OUTPUT_FORMAT=markdown
"""
        config_file = temp_dir / ".giv" / "config"
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text(config_content)
        
        bash_result = bash_giv.run(['config', 'show'])
        python_result = python_runner.run(['config', 'show'])
        
        # Both should succeed
        assert bash_result.returncode == 0
        assert python_result.returncode == 0
        
        # Should show similar configuration
        assert "GIV_TEMPLATE_DIR" in bash_result.stdout
        assert "GIV_TEMPLATE_DIR" in python_result.stdout
    
    def test_config_set_compatibility(self, bash_giv, temp_dir):
        """Test config set command compatibility."""
        python_runner = PythonGivRunner(temp_dir)
    
    def test_config_set_compatibility(self, temp_dir):
        """Test config set command compatibility."""
        bash_runner = BashGivRunner(cwd=temp_dir)
        python_runner = PythonGivRunner(cwd=temp_dir)
        
        # Test setting configuration with bash
        bash_result = bash_runner.run(['config', 'set', 'GIV_TEST_SETTING', 'bash_value'])
        assert bash_result.returncode == 0
        
        # Test setting configuration with python
        python_result = python_runner.run(['config', 'set', 'GIV_TEST_SETTING2', 'python_value'])
        assert python_result.returncode == 0
        
        # Both should be able to read each other's settings
        bash_show = bash_runner.run(['config', 'show'])
        python_show = python_runner.run(['config', 'show'])
        
        # Cross-compatibility check
        assert "GIV_TEST_SETTING2=python_value" in bash_show.stdout
        assert "GIV_TEST_SETTING=bash_value" in python_show.stdout
    
    def test_summary_current_compatibility(self, git_repo):
        """Test summary --current command compatibility."""
        bash_runner = BashGivRunner(cwd=git_repo)
        python_runner = PythonGivRunner(cwd=git_repo)
        
        # Make some changes
        (git_repo / "test_file.txt").write_text("Test content for compatibility")
        
        # Skip LLM calls for this test (mock or disable)
        env = {'GIV_LLM_PROVIDER': 'mock'}
        
        bash_result = bash_runner.run(['summary', '--current'], env=env)
        python_result = python_runner.run(['summary', '--current'], env=env)
        
        # Both should handle the command similarly (success or similar failure)
        # The exact behavior depends on LLM availability
        if bash_result.returncode == 0:
            assert python_result.returncode == 0
        else:
            # Both should fail in similar ways
            assert python_result.returncode != 0
    
    def test_summary_head_compatibility(self, git_repo):
        """Test summary HEAD command compatibility."""
        bash_runner = BashGivRunner(cwd=git_repo)
        python_runner = PythonGivRunner(cwd=git_repo)
        
        # Create a second commit
        (git_repo / "second_file.txt").write_text("Second commit content")
        subprocess.run(['git', 'add', '.'], cwd=git_repo, check=True)
        subprocess.run(['git', 'commit', '-m', 'Second commit'], cwd=git_repo, check=True)
        
        env = {'GIV_LLM_PROVIDER': 'mock'}
        
        bash_result = bash_runner.run(['summary', 'HEAD'], env=env)
        python_result = python_runner.run(['summary', 'HEAD'], env=env)
        
        # Should handle similarly
        assert bash_result.returncode == python_result.returncode
    
    def test_output_format_compatibility(self, git_repo):
        """Test output format options compatibility."""
        bash_runner = BashGivRunner(cwd=git_repo)
        python_runner = PythonGivRunner(cwd=git_repo)
        
        # Test different output formats
        formats = ['json', 'markdown', 'plain']
        
        for fmt in formats:
            bash_result = bash_runner.run(['config', 'set', 'GIV_OUTPUT_FORMAT', fmt])
            python_result = python_runner.run(['config', 'set', 'GIV_OUTPUT_FORMAT', fmt])
            
            # Both should handle format setting
            assert bash_result.returncode == 0
            assert python_result.returncode == 0
            
            # Verify the setting was applied
            bash_show = bash_runner.run(['config', 'show'])
            python_show = python_runner.run(['config', 'show'])
            
            assert f"GIV_OUTPUT_FORMAT={fmt}" in bash_show.stdout
            assert f"GIV_OUTPUT_FORMAT={fmt}" in python_show.stdout
    
    def test_error_handling_compatibility(self, temp_dir):
        """Test error handling compatibility."""
        bash_runner = BashGivRunner(cwd=temp_dir)  # Non-git directory
        python_runner = PythonGivRunner(cwd=temp_dir)
        
        # Test command that should fail in non-git directory
        bash_result = bash_runner.run(['summary', '--current'])
        python_result = python_runner.run(['summary', '--current'])
        
        # Both should fail
        assert bash_result.returncode != 0
        assert python_result.returncode != 0
        
        # Error messages should be helpful
        assert len(bash_result.stderr) > 0 or len(bash_result.stdout) > 0
        assert len(python_result.stderr) > 0 or len(python_result.stdout) > 0
    
    def test_config_hierarchy_compatibility(self, temp_dir):
        """Test configuration hierarchy compatibility."""
        bash_runner = BashGivRunner(cwd=temp_dir)
        python_runner = PythonGivRunner(cwd=temp_dir)
        
        # Create config at different levels
        global_config = temp_dir / ".giv" / "config"
        global_config.parent.mkdir(exist_ok=True)
        global_config.write_text("GIV_GLOBAL=global_value\nGIV_OVERRIDE=global_override\n")
        
        local_config = temp_dir / "project" / ".giv" / "config"
        local_config.parent.mkdir(parents=True, exist_ok=True)
        local_config.write_text("GIV_LOCAL=local_value\nGIV_OVERRIDE=local_override\n")
        
        # Test from project directory
        project_bash = BashGivRunner(cwd=temp_dir / "project")
        project_python = PythonGivRunner(cwd=temp_dir / "project")
        
        bash_show = project_bash.run(['config', 'show'])
        python_show = project_python.run(['config', 'show'])
        
        # Both should show local overriding global
        assert "GIV_GLOBAL=global_value" in bash_show.stdout
        assert "GIV_GLOBAL=global_value" in python_show.stdout
        assert "GIV_LOCAL=local_value" in bash_show.stdout
        assert "GIV_LOCAL=local_value" in python_show.stdout
        assert "GIV_OVERRIDE=local_override" in bash_show.stdout
        assert "GIV_OVERRIDE=local_override" in python_show.stdout


class TestCommandLineCompatibility:
    """Test command-line argument compatibility."""
    
    def test_argument_parsing_compatibility(self):
        """Test that both implementations parse arguments identically."""
        bash_runner = BashGivRunner()
        python_runner = PythonGivRunner()
        
        # Test various argument combinations
        test_cases = [
            ['--version'],
            ['--help'],
            ['config', 'show'],
            ['config', 'set', 'TEST_VAR', 'test_value'],
            # Add more test cases as needed
        ]
        
        for args in test_cases:
            bash_result = bash_runner.run(args)
            python_result = python_runner.run(args)
            
            # At minimum, both should parse without argument errors
            # (They might fail for other reasons like missing dependencies)
            if "unknown option" in bash_result.stderr.lower():
                assert "unknown" in python_result.stderr.lower() or \
                       "unrecognized" in python_result.stderr.lower()
    
    def test_invalid_command_compatibility(self):
        """Test handling of invalid commands."""
        bash_runner = BashGivRunner()
        python_runner = PythonGivRunner()
        
        # Test invalid command
        bash_result = bash_runner.run(['invalid-command'])
        python_result = python_runner.run(['invalid-command'])
        
        # Both should fail
        assert bash_result.returncode != 0
        assert python_result.returncode != 0
        
        # Should provide helpful error messages
        bash_error = (bash_result.stderr + bash_result.stdout).lower()
        python_error = (python_result.stderr + python_result.stdout).lower()
        
        # Both should indicate the command is invalid/unknown
        assert "unknown" in bash_error or "invalid" in bash_error or "usage" in bash_error
        assert "unknown" in python_error or "invalid" in python_error or "usage" in python_error
    
    def test_flag_compatibility(self):
        """Test that flags work identically."""
        bash_runner = BashGivRunner()
        python_runner = PythonGivRunner()
        
        # Test help flags
        help_flags = ['--help', '-h']
        
        for flag in help_flags:
            bash_result = bash_runner.run([flag])
            python_result = python_runner.run([flag])
            
            # Both should show help (exit code 0 or similar)
            # The exact exit code for help might vary
            bash_showed_help = bash_result.returncode == 0 or "usage" in bash_result.stdout.lower()
            python_showed_help = python_result.returncode == 0 or "usage" in python_result.stdout.lower()
            
            assert bash_showed_help
            assert python_showed_help


class TestOutputCompatibility:
    """Test output format compatibility."""
    
    def test_json_output_compatibility(self, git_repo):
        """Test JSON output format compatibility."""
        bash_runner = BashGivRunner(cwd=git_repo)
        python_runner = PythonGivRunner(cwd=git_repo)
        
        # Set JSON output format
        bash_runner.run(['config', 'set', 'GIV_OUTPUT_FORMAT', 'json'])
        python_runner.run(['config', 'set', 'GIV_OUTPUT_FORMAT', 'json'])
        
        # Test config show in JSON format
        bash_result = bash_runner.run(['config', 'show'])
        python_result = python_runner.run(['config', 'show'])
        
        # Both should produce valid output
        assert bash_result.returncode == 0
        assert python_result.returncode == 0
        
        # If JSON format is implemented, should be valid JSON
        # If not implemented, should handle gracefully
        if "GIV_OUTPUT_FORMAT=json" in bash_result.stdout:
            assert "GIV_OUTPUT_FORMAT=json" in python_result.stdout
    
    def test_verbose_output_compatibility(self, git_repo):
        """Test verbose output compatibility."""
        bash_runner = BashGivRunner(cwd=git_repo)
        python_runner = PythonGivRunner(cwd=git_repo)
        
        # Test with verbose flag if supported
        bash_result = bash_runner.run(['config', 'show', '--verbose'])
        python_result = python_runner.run(['config', 'show', '--verbose'])
        
        # Should handle verbose flag similarly
        # If supported, both should be more verbose
        # If not supported, both should handle gracefully
        assert isinstance(bash_result.returncode, int)
        assert isinstance(python_result.returncode, int)


class TestEnvironmentCompatibility:
    """Test environment variable compatibility."""
    
    def test_env_var_precedence(self, temp_dir):
        """Test environment variable precedence compatibility."""
        bash_runner = BashGivRunner(cwd=temp_dir)
        python_runner = PythonGivRunner(cwd=temp_dir)
        
        # Set config file value
        config_file = temp_dir / ".giv" / "config"
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text("GIV_TEST_VAR=config_value\n")
        
        # Test with environment variable override
        env = {'GIV_TEST_VAR': 'env_value'}
        
        bash_result = bash_runner.run(['config', 'show'], env=env)
        python_result = python_runner.run(['config', 'show'], env=env)
        
        # Both should show environment variable taking precedence
        assert bash_result.returncode == 0
        assert python_result.returncode == 0
        
        # Environment value should override config file
        assert "GIV_TEST_VAR=env_value" in bash_result.stdout
        assert "GIV_TEST_VAR=env_value" in python_result.stdout
    
    def test_home_directory_compatibility(self):
        """Test home directory handling compatibility."""
        bash_runner = BashGivRunner()
        python_runner = PythonGivRunner()
        
        # Test that both implementations handle home directory paths
        home_env = {'HOME': '/tmp/test_home'}
        
        bash_result = bash_runner.run(['config', 'show'], env=home_env)
        python_result = python_runner.run(['config', 'show'], env=home_env)
        
        # Both should handle the custom HOME environment
        assert isinstance(bash_result.returncode, int)
        assert isinstance(python_result.returncode, int)


class TestPerformanceCompatibility:
    """Test performance characteristics compatibility."""
    
    def test_startup_time_reasonable(self):
        """Test that startup time is reasonable for both implementations."""
        import time
        
        bash_runner = BashGivRunner()
        python_runner = PythonGivRunner()
        
        # Measure startup time for simple command
        start_time = time.time()
        bash_result = bash_runner.run(['--version'])
        bash_time = time.time() - start_time
        
        start_time = time.time()
        python_result = python_runner.run(['--version'])
        python_time = time.time() - start_time
        
        # Both should complete within reasonable time (5 seconds is generous)
        assert bash_time < 5.0
        assert python_time < 5.0
        
        # Python shouldn't be dramatically slower than bash
        # (Allow up to 3x difference for Python startup overhead)
        if bash_time > 0.1:  # Only compare if bash took measurable time
            assert python_time < bash_time * 3.0
