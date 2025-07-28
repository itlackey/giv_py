"""
Scoop manifest builder for giv CLI.

Generates Scoop manifests that reference Windows binary releases.
"""
import hashlib
import json
from pathlib import Path
from typing import Optional

from ..core.config import BuildConfig
from ..core.version_manager import VersionManager


class ScoopBuilder:
    """Builds Scoop manifest for Windows binary distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Scoop builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "giv.json"
    
    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def generate_manifest(self, version: str, binary_path: Optional[Path] = None) -> dict:
        """
        Generate Scoop manifest.
        
        Args:
            version: Version string
            binary_path: Path to Windows binary (auto-detected if not provided)
            
        Returns:
            Generated manifest as dictionary
        """
        # Read template
        with open(self.template_file, 'r') as f:
            template_content = f.read()
        
        # Auto-detect binary path if not provided
        if binary_path is None:
            windows_dir = self.config.get_platform_dist_dir(version, "windows", "x86_64")
            binary_name = self.config.get_binary_name("windows", "x86_64")
            binary_path = windows_dir / binary_name
        
        # Calculate hash if binary exists
        hash_value = ""
        if binary_path and binary_path.exists():
            hash_value = self.calculate_sha256(binary_path)
        
        # Replace template variables
        manifest_content = template_content.replace("{{VERSION}}", version)
        manifest_content = manifest_content.replace("{{HASH}}", hash_value)
        
        # Parse as JSON
        manifest = json.loads(manifest_content)
        
        return manifest
    
    def build_manifest(self, version: Optional[str] = None, binary_path: Optional[Path] = None) -> Path:
        """
        Build Scoop manifest.
        
        Args:
            version: Version string (auto-detected if not provided)
            binary_path: Path to Windows binary (auto-detected if not provided)
            
        Returns:
            Path to generated manifest
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Building Scoop manifest for version {version}")
        
        # Generate manifest
        manifest = self.generate_manifest(version, binary_path)
        
        # Output directory
        output_dir = self.config.get_dist_dir(version) / "scoop"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write manifest
        manifest_path = output_dir / "giv.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)
        
        print(f"✓ Scoop manifest generated: {manifest_path}")
        return manifest_path
    
    def validate_manifest(self, manifest_path: Path) -> bool:
        """
        Validate Scoop manifest.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if manifest is valid
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check required fields
            required_fields = ["version", "description", "url", "bin"]
            missing_fields = [field for field in required_fields if field not in manifest]
            
            if missing_fields:
                print(f"✗ Scoop manifest missing required fields: {missing_fields}")
                return False
            
            # Validate URL format
            url = manifest.get("url", "")
            if not url.startswith("https://"):
                print(f"✗ Scoop manifest URL must be HTTPS: {url}")
                return False
            
            print("✓ Scoop manifest is valid")
            return True
            
        except json.JSONDecodeError as e:
            print(f"✗ Scoop manifest JSON syntax error: {e}")
            return False
        except Exception as e:
            print(f"✗ Scoop manifest validation error: {e}")
            return False
    
    def create_bucket_structure(self, version: str, manifest_path: Path) -> Path:
        """
        Create Scoop bucket directory structure.
        
        Args:
            version: Version string
            manifest_path: Path to manifest file
            
        Returns:
            Path to bucket directory
        """
        bucket_dir = self.config.get_dist_dir(version) / "scoop-bucket"
        bucket_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy manifest to bucket directory
        bucket_manifest_path = bucket_dir / "giv.json"
        import shutil
        shutil.copy2(manifest_path, bucket_manifest_path)
        
        # Create bucket README
        readme_content = f"""# Scoop Bucket for giv CLI

This is the official Scoop bucket for the giv CLI tool.

## Installation

```powershell
scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket
scoop install giv
```

## About

giv is a Git history AI assistant CLI tool that generates commit messages,
changelogs, release notes, and announcements using AI.

- Homepage: https://github.com/giv-cli/giv-py
- Version: {version}
"""
        
        with open(bucket_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Scoop bucket structure created: {bucket_dir}")
        return bucket_dir
    
    def generate_chocolatey_nuspec(self, version: str) -> Path:
        """
        Generate Chocolatey package specification.
        
        Args:
            version: Version string
            
        Returns:
            Path to generated nuspec file
        """
        nuspec_content = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>giv</id>
    <version>{version}</version>
    <packageSourceUrl>https://github.com/giv-cli/giv-py</packageSourceUrl>
    <owners>giv-cli</owners>
    <title>giv CLI</title>
    <authors>giv Development Team</authors>
    <projectUrl>https://github.com/giv-cli/giv-py</projectUrl>
    <iconUrl>https://raw.githubusercontent.com/giv-cli/giv-py/main/docs/logo.png</iconUrl>
    <copyright>2024 giv Development Team</copyright>
    <licenseUrl>https://github.com/giv-cli/giv-py/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectSourceUrl>https://github.com/giv-cli/giv-py</projectSourceUrl>
    <docsUrl>https://github.com/giv-cli/giv-py/blob/main/README.md</docsUrl>
    <bugTrackerUrl>https://github.com/giv-cli/giv-py/issues</bugTrackerUrl>
    <tags>git cli ai changelog commit-message</tags>
    <summary>Git history AI assistant CLI tool</summary>
    <description>giv is a CLI tool that uses AI to generate commit messages, changelogs, release notes, and announcements from Git history. It integrates with local and remote AI models to provide intelligent Git workflow automation.</description>
    <releaseNotes>https://github.com/giv-cli/giv-py/releases/tag/v{version}</releaseNotes>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>'''
        
        # Output directory
        output_dir = self.config.get_dist_dir(version) / "chocolatey"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write nuspec file
        nuspec_path = output_dir / "giv.nuspec"
        with open(nuspec_path, 'w') as f:
            f.write(nuspec_content)
        
        # Create tools directory with install script
        tools_dir = output_dir / "tools"
        tools_dir.mkdir(exist_ok=True)
        
        install_script = f'''$ErrorActionPreference = 'Stop'

$packageName = 'giv'
$url = 'https://github.com/giv-cli/giv-py/releases/download/v{version}/giv-windows-x86_64.exe'
$checksum = ''  # Will be filled in during build

$packageArgs = @{{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'EXE'
  url           = $url
  checksum      = $checksum
  checksumType  = 'sha256'
}}

Get-ChocolateyWebFile @packageArgs
'''
        
        with open(tools_dir / "chocolateyinstall.ps1", 'w') as f:
            f.write(install_script)
        
        print(f"✓ Chocolatey nuspec generated: {nuspec_path}")
        return nuspec_path


def main():
    """CLI interface for Scoop builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Scoop manifest for giv CLI")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--validate", action="store_true", help="Validate manifest")
    parser.add_argument("--create-bucket", action="store_true", help="Create bucket directory structure")
    parser.add_argument("--chocolatey", action="store_true", help="Generate Chocolatey nuspec")
    
    args = parser.parse_args()
    
    builder = ScoopBuilder()
    
    # Build manifest
    manifest_path = builder.build_manifest(args.version)
    
    # Validate manifest
    if args.validate:
        builder.validate_manifest(manifest_path)
    
    # Create bucket structure
    if args.create_bucket:
        version = args.version or builder.version_manager.get_version()
        builder.create_bucket_structure(version, manifest_path)
    
    # Generate Chocolatey nuspec
    if args.chocolatey:
        version = args.version or builder.version_manager.get_version()
        builder.generate_chocolatey_nuspec(version)


if __name__ == "__main__":
    main()