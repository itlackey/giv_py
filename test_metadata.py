#!/usr/bin/env python3
"""
Simple test script to verify enhanced project metadata functionality.
"""
import sys
from pathlib import Path

# Add the giv_cli package to Python path
sys.path.insert(0, str(Path(__file__).parent / "giv_cli"))

from project_metadata import ProjectMetadata

def test_project_metadata():
    """Test enhanced project metadata functionality."""
    print("Testing Enhanced Project Metadata...")
    
    # Test project type detection
    try:
        project_type = ProjectMetadata.detect_project_type()
        print(f"Detected Project Type: {project_type}")
    except Exception as e:
        print(f"Error detecting project type: {e}")
        return False
    
    # Test metadata extraction
    try:
        title = ProjectMetadata.get_title()
        version = ProjectMetadata.get_version()
        description = ProjectMetadata.get_description()
        url = ProjectMetadata.get_url()
        author = ProjectMetadata.get_author()
        
        print(f"Project Title: {title}")
        print(f"Project Version: {version}")
        print(f"Project Description: {description}")
        print(f"Project URL: {url}")
        print(f"Project Author: {author}")
        
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return False
    
    # Test all metadata
    try:
        all_metadata = ProjectMetadata.get_all_metadata()
        print(f"\nAll Metadata ({len(all_metadata)} fields):")
        for key, value in all_metadata.items():
            if value:  # Only show non-empty values
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error getting all metadata: {e}")
        return False
    
    # Test metadata value extraction
    try:
        name_value = ProjectMetadata.get_metadata_value("name")
        version_value = ProjectMetadata.get_metadata_value("version")
        print(f"\nDirect Metadata Access:")
        print(f"  name: {name_value}")
        print(f"  version: {version_value}")
        
    except Exception as e:
        print(f"Error getting metadata values: {e}")
        return False
    
    print("\n✅ Enhanced Project Metadata test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_project_metadata()
    sys.exit(0 if success else 1)
