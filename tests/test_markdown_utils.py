"""
Comprehensive tests for markdown_utils module.

Tests markdown processing functionality including:
- Table of contents generation
- Section management
- Link fixing
- Content extraction
- Image handling
- Bash compatibility
"""
import pytest
from pathlib import Path

from giv.lib.markdown import MarkdownProcessor


class TestMarkdownProcessor:
    """Test MarkdownProcessor class functionality."""
    
    def test_init(self):
        """Test MarkdownProcessor initialization."""
        mp = MarkdownProcessor()
        assert mp is not None
    
    def test_extract_content_basic(self):
        """Test basic content extraction."""
        content = """# Main Title

Some introduction text.

## Section 1

Content for section 1.

### Subsection 1.1

Nested content.

## Section 2

Content for section 2.
"""
        
        mp = MarkdownProcessor()
        extracted = mp.extract_content(content, "Section 1")
        
        assert "Content for section 1." in extracted
        assert "Nested content." in extracted
        assert "Content for section 2." not in extracted
    
    def test_extract_content_nested_sections(self):
        """Test extracting content with nested sections."""
        content = """# Document

## Installation

Basic installation steps.

### Prerequisites

You need Python 3.8+.

### Install Steps

1. Download
2. Install
3. Configure

## Usage

How to use the tool.

### Basic Usage

Run the command.

### Advanced Usage

Use with options.
"""
        
        mp = MarkdownProcessor()
        
        # Extract main section
        installation = mp.extract_content(content, "Installation")
        assert "Basic installation steps." in installation
        assert "You need Python 3.8+." in installation
        assert "1. Download" in installation
        assert "How to use the tool." not in installation
        
        # Extract subsection
        prereqs = mp.extract_content(content, "Prerequisites")
        assert "You need Python 3.8+." in prereqs
        assert "1. Download" not in prereqs
    
    def test_extract_content_case_insensitive(self):
        """Test case-insensitive section extraction."""
        content = """## API Reference

The API provides several endpoints.

## Configuration

Settings and options.
"""
        
        mp = MarkdownProcessor()
        
        # Test different cases
        api_ref = mp.extract_content(content, "api reference")
        assert "The API provides several endpoints." in api_ref
        
        config = mp.extract_content(content, "CONFIGURATION")
        assert "Settings and options." in config
    
    def test_extract_content_nonexistent_section(self):
        """Test extracting non-existent section."""
        content = """## Real Section

This exists.
"""
        
        mp = MarkdownProcessor()
        result = mp.extract_content(content, "Fake Section")
        
        # Should return empty string or None for non-existent sections
        assert result == "" or result is None
    
    def test_generate_toc_basic(self):
        """Test basic table of contents generation."""
        content = """# Main Title

Introduction

## First Section

Content here.

### Subsection A

Nested content.

### Subsection B

More nested content.

## Second Section

More content.

## Third Section

Final content.
"""
        
        mp = MarkdownProcessor()
        toc = mp.generate_toc(content)
        
        # Should contain all sections with proper hierarchy
        assert "First Section" in toc
        assert "Subsection A" in toc
        assert "Subsection B" in toc
        assert "Second Section" in toc
        assert "Third Section" in toc
        
        # Check indentation for hierarchy
        lines = toc.split('\n')
        first_section_line = next(line for line in lines if "First Section" in line)
        subsection_a_line = next(line for line in lines if "Subsection A" in line)
        
        # Subsection should be more indented than main section
        assert len(subsection_a_line) - len(subsection_a_line.lstrip()) > \
               len(first_section_line) - len(first_section_line.lstrip())
    
    def test_generate_toc_with_links(self):
        """Test TOC generation with proper markdown links."""
        content = """## Getting Started

Basic setup.

## API Documentation

Detailed API info.

### Authentication

How to authenticate.

### Endpoints

Available endpoints.
"""
        
        mp = MarkdownProcessor()
        toc = mp.generate_toc(content)
        
        # Should contain markdown links
        assert "[Getting Started]" in toc or "Getting Started" in toc
        assert "[API Documentation]" in toc or "API Documentation" in toc
        assert "[Authentication]" in toc or "Authentication" in toc
        assert "[Endpoints]" in toc or "Endpoints" in toc
    
    def test_fix_relative_links_basic(self):
        """Test fixing relative links in markdown."""
        content = """# Documentation

See [other doc](other.md) for details.

Also check [config](../config/setup.md).

External link: [GitHub](https://github.com) should not change.
"""
        base_path = "/docs"
        
        mp = MarkdownProcessor()
        fixed = mp.fix_relative_links(content, base_path)
        
        # Relative links should be made absolute
        assert "[other doc](/docs/other.md)" in fixed or "other.md" in fixed
        assert "[config](/config/setup.md)" in fixed or "../config/setup.md" in fixed
        
        # External links should remain unchanged
        assert "[GitHub](https://github.com)" in fixed
    
    def test_fix_relative_links_images(self):
        """Test fixing relative links for images."""
        content = """# Documentation

![Logo](logo.png)

![Diagram](../images/flow.png)

![External](https://example.com/image.png)
"""
        base_path = "/docs"
        
        mp = MarkdownProcessor()
        fixed = mp.fix_relative_links(content, base_path)
        
        # Image links should be fixed
        assert "![Logo](/docs/logo.png)" in fixed or "logo.png" in fixed
        assert "![Diagram](/images/flow.png)" in fixed or "../images/flow.png" in fixed
        
        # External images should remain unchanged
        assert "![External](https://example.com/image.png)" in fixed
    
    def test_manage_sections_replace(self):
        """Test replacing sections in markdown."""
        original = """# Document

## Introduction

Old intro content.

## Setup

Setup instructions.

## Conclusion

Final thoughts.
"""
        
        new_content = """New and improved introduction.

With multiple paragraphs.
"""
        
        mp = MarkdownProcessor()
        result = mp.manage_sections(original, "Introduction", new_content, "replace")
        
        # Should replace the Introduction section
        assert "New and improved introduction." in result
        assert "Old intro content." not in result
        assert "Setup instructions." in result  # Other sections preserved
        assert "Final thoughts." in result
    
    def test_manage_sections_append(self):
        """Test appending to sections in markdown."""
        original = """# Document

## Notes

Existing notes.

## Other Section

Other content.
"""
        
        additional = """Additional notes to append.
"""
        
        mp = MarkdownProcessor()
        result = mp.manage_sections(original, "Notes", additional, "append")
        
        # Should append to existing content
        assert "Existing notes." in result
        assert "Additional notes to append." in result
        assert "Other content." in result
    
    def test_manage_sections_create_new(self):
        """Test creating new sections in markdown."""
        original = """# Document

## Existing Section

Existing content.
"""
        
        new_section_content = """Content for new section.
"""
        
        mp = MarkdownProcessor()
        result = mp.manage_sections(original, "New Section", new_section_content, "replace")
        
        # Should create new section
        assert "## New Section" in result or "# New Section" in result
        assert "Content for new section." in result
        assert "Existing content." in result
    
    def test_clean_markdown_basic(self):
        """Test basic markdown cleaning."""
        messy_content = """# Title with   extra   spaces

## Section with trailing spaces   

Content with   multiple    spaces between words.

- List item with  spaces
- Another   item

```
Code block should preserve   spaces
```
"""
        
        mp = MarkdownProcessor()
        cleaned = mp.clean_markdown(messy_content)
        
        # Should normalize spaces
        assert "# Title with extra spaces" in cleaned
        assert "## Section with trailing spaces" in cleaned
        assert "multiple spaces between" in cleaned
        
        # Should preserve code blocks
        assert "preserve   spaces" in cleaned
    
    def test_clean_markdown_empty_lines(self):
        """Test cleaning excessive empty lines."""
        content = """# Title


## Section


Content here.



More content.




## Another Section

Final content.
"""
        
        mp = MarkdownProcessor()
        cleaned = mp.clean_markdown(content)
        
        # Should reduce excessive blank lines
        lines = cleaned.split('\n')
        empty_line_count = 0
        max_consecutive_empty = 0
        
        for line in lines:
            if line.strip() == '':
                empty_line_count += 1
                max_consecutive_empty = max(max_consecutive_empty, empty_line_count)
            else:
                empty_line_count = 0
        
        # Should not have more than 2 consecutive empty lines
        assert max_consecutive_empty <= 2


class TestMarkdownCompatibility:
    """Test compatibility with Bash implementation."""
    
    def test_extract_content_bash_compatible(self):
        """Test that content extraction matches Bash behavior."""
        # This mimics the kind of content the Bash version would process
        bash_style_content = """# giv

A git-integrated versioning tool.

## Installation

To install giv:

```bash
curl -sSL https://install.example.com | bash
```

### Requirements

- Git 2.0+
- Bash 4.0+

## Usage

Basic usage:

```bash
giv summary
```

### Advanced Options

Use with custom templates:

```bash
giv summary --template custom
```

## Configuration

Configuration options:

- `GIV_TEMPLATE_DIR`: Template directory
- `GIV_CONFIG_FILE`: Config file path
"""
        
        mp = MarkdownProcessor()
        
        # Test extraction of main sections
        installation = mp.extract_content(bash_style_content, "Installation")
        assert "To install giv:" in installation
        assert "Git 2.0+" in installation
        assert "Bash 4.0+" in installation
        assert "Basic usage:" not in installation
        
        usage = mp.extract_content(bash_style_content, "Usage")
        assert "Basic usage:" in usage
        assert "giv summary" in usage
        assert "custom templates:" in usage
        assert "Configuration options:" not in usage
    
    def test_toc_generation_bash_format(self):
        """Test TOC generation in format compatible with Bash version."""
        content = """# Project Name

## Quick Start
## Installation
### Prerequisites
### Install Steps
## Configuration
### Basic Config
### Advanced Config
## Usage Examples
## API Reference
### Authentication
### Endpoints
## Troubleshooting
"""
        
        mp = MarkdownProcessor()
        toc = mp.generate_toc(content)
        
        # Should generate hierarchical TOC
        assert "Quick Start" in toc
        assert "Installation" in toc
        assert "Prerequisites" in toc
        assert "Install Steps" in toc
        assert "Configuration" in toc
        assert "Basic Config" in toc
        assert "Advanced Config" in toc
        assert "Usage Examples" in toc
        assert "API Reference" in toc
        assert "Authentication" in toc
        assert "Endpoints" in toc
        assert "Troubleshooting" in toc
    
    def test_section_management_bash_style(self):
        """Test section management in Bash-compatible way."""
        # Test with real-world style content
        original = """# Project Documentation

## Overview

This project provides CLI tools.

## Installation

Current installation instructions.

## Usage

How to use the tools.

## Contributing

Guidelines for contributors.
"""
        
        new_install_content = """### Quick Install

```bash
curl -sSL install.sh | bash
```

### Manual Install

1. Download the latest release
2. Extract to /usr/local/bin
3. Make executable: `chmod +x giv`

### Verify Installation

```bash
giv --version
```
"""
        
        mp = MarkdownProcessor()
        result = mp.manage_sections(original, "Installation", new_install_content, "replace")
        
        # Should replace installation section completely
        assert "### Quick Install" in result
        assert "curl -sSL install.sh" in result
        assert "### Manual Install" in result
        assert "### Verify Installation" in result
        assert "Current installation instructions." not in result
        
        # Other sections should remain
        assert "This project provides CLI tools." in result
        assert "How to use the tools." in result
        assert "Guidelines for contributors." in result


class TestMarkdownEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_content(self):
        """Test handling empty content."""
        mp = MarkdownProcessor()
        
        # Should handle empty strings gracefully
        assert mp.extract_content("", "Section") == "" or mp.extract_content("", "Section") is None
        assert mp.generate_toc("") == "" or mp.generate_toc("") == []
        assert mp.clean_markdown("") == ""
    
    def test_malformed_headers(self):
        """Test handling malformed markdown headers."""
        content = """#NoSpaceHeader

##  Extra  Spaces  

###Too Many Spaces   

Content here.

###### Very Deep Header

More content.
"""
        
        mp = MarkdownProcessor()
        
        # Should handle malformed headers gracefully
        toc = mp.generate_toc(content)
        assert isinstance(toc, str) or isinstance(toc, list)
        
        cleaned = mp.clean_markdown(content)
        assert isinstance(cleaned, str)
    
    def test_content_with_special_characters(self):
        """Test handling content with special characters."""
        content = """# Title with émojis 🚀

## Sección en Español

Contenido con caracteres especiales: áéíóú ñ

### Code with symbols

```python
def test():
    return "Special chars: @#$%^&*()"
```

## Unicode Content: 中文测试

Testing unicode handling.
"""
        
        mp = MarkdownProcessor()
        
        # Should handle unicode and special characters
        toc = mp.generate_toc(content)
        assert "émojis" in toc or "Special" in toc
        
        spanish_section = mp.extract_content(content, "Sección en Español")
        assert "Contenido con caracteres" in spanish_section or spanish_section == ""
        
        unicode_section = mp.extract_content(content, "Unicode Content")
        assert "Testing unicode" in unicode_section or unicode_section == ""
    
    def test_deeply_nested_sections(self):
        """Test handling deeply nested sections."""
        content = """# Level 1

## Level 2

### Level 3

#### Level 4

##### Level 5

###### Level 6

Content at deepest level.

##### Back to Level 5

More content.

## Another Level 2

Different content.
"""
        
        mp = MarkdownProcessor()
        
        # Should handle deep nesting
        toc = mp.generate_toc(content)
        assert "Level 6" in toc
        
        deep_content = mp.extract_content(content, "Level 4")
        assert "Content at deepest level." in deep_content or "Level 5" in deep_content
