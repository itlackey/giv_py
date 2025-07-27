#!/usr/bin/env python3
"""
Simple test script to verify template system functionality.
"""
import sys
from pathlib import Path

# Add the giv_cli package to Python path
sys.path.insert(0, str(Path(__file__).parent / "giv_cli"))

from template_utils import TemplateManager

def test_template_system():
    """Test basic template system functionality."""
    print("Testing Template System...")
    
    # Create template manager
    template_mgr = TemplateManager()
    
    # Test template discovery
    try:
        templates = template_mgr.list_available_templates()
        print(f"Found {len(templates)} templates:")
        for name, path in templates.items():
            print(f"  - {name}: {path}")
    except Exception as e:
        print(f"Error listing templates: {e}")
        return False
    
    # Test template loading
    try:
        if "message_prompt.md" in templates:
            content = template_mgr.load_template("message_prompt.md")
            print(f"\nLoaded message_prompt.md ({len(content)} characters)")
            print("First 200 characters:")
            print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print("message_prompt.md not found in templates")
            return False
    except Exception as e:
        print(f"Error loading template: {e}")
        return False
    
    # Test template render
    try:
        context = {
            "SUMMARY": "Test git diff content",
            "PROJECT_TITLE": "Test Project", 
            "VERSION": "1.0.0",
            "REVISION": "HEAD"
        }
        
        rendered = template_mgr.render_template_file("message_prompt.md", context)
        print(f"\nRendered template ({len(rendered)} characters)")
        print("Checking token replacement...")
        
        if "Test git diff content" in rendered:
            print("✓ SUMMARY token replaced correctly")
        else:
            print("✗ SUMMARY token not replaced")
            
        if "Test Project" in rendered:
            print("✓ PROJECT_TITLE token replaced correctly")
        else:
            print("✗ PROJECT_TITLE token not replaced")
            
    except Exception as e:
        print(f"Error rendering template: {e}")
        return False
    
    print("\n✅ Template system test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_template_system()
    sys.exit(0 if success else 1)
