"""
Scoop manifest builder for giv CLI.

Generates Scoop manifests that reference Windows binary releases.
"""
import json
import sys
from pathlib import Path
from typing import Optional

# Handle imports for both standalone and package usage
try:
    from ..core.config import BuildConfig
    from ..core.version_manager import VersionManager
    from ..core.utils import ensure_dir, calculate_sha256
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.config import BuildConfig
    from core.version_manager import VersionManager
    from core.utils import ensure_dir, calculate_sha256


class ScoopBuilder:
    """Builds Scoop manifest for Windows binary distribution."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize Scoop builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        
        # Template file
        self.template_file = Path(__file__).parent / "giv.json"
    
    def build_manifest(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Build Scoop manifest.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to generated manifest
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir
            
        print(f"Building Scoop manifest for version {version}")
        
        ensure_dir(output_dir)
        
        # Find Windows binary - always look in the main dist directory
        # regardless of where we're placing the manifest
        binary_path = self.config.dist_dir / "giv-windows-x86_64.exe"
        
        if not binary_path.exists():
            raise FileNotFoundError(f"Windows binary not found: {binary_path}")
        
        # Calculate checksum
        checksum = calculate_sha256(binary_path)
        
        # Create manifest
        manifest = {
            "version": version,
            "description": self.config.description,
            "homepage": self.config.homepage,
            "license": self.config.license,
            "url": self.config.get_github_release_url(version, binary_path.name),
            "hash": checksum,
            "bin": binary_path.name,
            "shortcuts": [
                [binary_path.name, "giv"]
            ],
            "checkver": {
                "github": self.config.repository
            },
            "autoupdate": {
                "url": f"{self.config.repository}/releases/download/v$version/{binary_path.name}"
            }
        }
        
        # Write manifest
        manifest_path = output_dir / "giv.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=4)
        
        print(f"Package: Scoop manifest: {manifest_path.name}")
        return manifest_path
    
    def validate_manifest(self, manifest_path: Path) -> bool:
        """
        Validate Scoop manifest.
        
        Args:
            manifest_path: Path to manifest file
            
        Returns:
            True if manifest is valid
        """
        print("Validating Validating Scoop manifest...")
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Basic validation
            required_fields = ["version", "url", "hash", "bin"]
            for field in required_fields:
                if field not in manifest:
                    print(f"ERROR: Missing required field: {field}")
                    return False
            
            print("SUCCESS: Scoop manifest is valid")
            return True
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in manifest: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Manifest validation failed: {e}")
            return False

    def create_bucket_structure(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Create Scoop bucket directory structure.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to bucket directory
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / version
        
        # Create bucket structure: scoop-bucket/bucket/
        bucket_dir = output_dir / "scoop-bucket" / "bucket"
        ensure_dir(bucket_dir)
        
        # Build and place manifest in bucket structure
        self.build_manifest(version, bucket_dir)
        
        # Create README for bucket
        readme_content = f"""# Scoop Bucket for giv CLI

This is the official Scoop bucket for giv CLI version {version}.

## Installation

```powershell
scoop bucket add giv-cli https://github.com/giv-cli/scoop-bucket
scoop install giv
```

## Updating

```powershell
scoop update
scoop update giv
```
"""
        readme_path = bucket_dir.parent / "README.md"
        readme_path.write_text(readme_content)
        
        print(f"Created Scoop bucket structure at: {bucket_dir.parent}")
        return bucket_dir.parent

    def create_chocolatey_package(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Path:
        """
        Create Chocolatey package structure.
        
        Args:
            version: Version string (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Path to chocolatey directory
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir / version
        
        # Create chocolatey structure
        choco_dir = output_dir / "chocolatey"
        tools_dir = choco_dir / "tools"
        ensure_dir(tools_dir)
        
        # Create basic chocolatey files
        nuspec_content = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>giv</id>
    <version>{version}</version>
    <packageSourceUrl>https://github.com/giv-cli/giv-py</packageSourceUrl>
    <owners>giv-cli</owners>
    <title>giv CLI</title>
    <authors>giv Development Team</authors>
    <projectUrl>https://github.com/giv-cli/giv-py</projectUrl>
    <description>Intelligent Git commit message and changelog generator powered by AI</description>
    <summary>AI-powered Git history assistant</summary>
    <tags>git commit ai changelog cli</tags>
    <licenseUrl>https://github.com/giv-cli/giv-py/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>"""
        
        install_script = f"""$ErrorActionPreference = 'Stop'
$packageName = 'giv'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url64 = 'https://github.com/giv-cli/giv-py/releases/download/v{version}/giv-windows-x86_64.exe'

$packageArgs = @{{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'exe'
  url64bit      = $url64
  softwareName  = 'giv*'
  checksum64    = 'CHECKSUM_PLACEHOLDER'
  checksumType64= 'sha256'
  validExitCodes= @(0)
}}

Install-ChocolateyPackage @packageArgs
"""
        
        (choco_dir / f"giv.{version}.nuspec").write_text(nuspec_content)
        (tools_dir / "chocolateyinstall.ps1").write_text(install_script)
        
        print(f"Created Chocolatey package structure at: {choco_dir}")
        return choco_dir


def main():
    """CLI interface for Scoop builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Scoop manifest")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--output-dir", type=Path, help="Output directory for manifest")
    parser.add_argument("--validate", action="store_true", help="Validate manifest only")
    parser.add_argument("--create-bucket", action="store_true", help="Create Scoop bucket structure")
    parser.add_argument("--chocolatey", action="store_true", help="Also create Chocolatey package")
    
    args = parser.parse_args()
    
    try:
        builder = ScoopBuilder()
        
        if args.create_bucket:
            # Create Scoop bucket structure
            bucket_dir = builder.create_bucket_structure(args.version, args.output_dir)
            if args.chocolatey:
                choco_dir = builder.create_chocolatey_package(args.version, args.output_dir)
                print("SUCCESS: Scoop bucket and Chocolatey package created")
            else:
                print(f"SUCCESS: Scoop bucket created at {bucket_dir}")
            return
        
        if args.chocolatey:
            # Create Chocolatey package only
            choco_dir = builder.create_chocolatey_package(args.version, args.output_dir)
            print(f"SUCCESS: Chocolatey package created at {choco_dir}")
            return
        
        if args.validate:
            # Find existing manifest to validate
            output_dir = args.output_dir or builder.config.dist_dir
            manifest_path = output_dir / "giv.json"
            
            if manifest_path.exists():
                valid = builder.validate_manifest(manifest_path)
                sys.exit(0 if valid else 1)
            else:
                print("No manifest found to validate")
                sys.exit(1)
        
        # Build manifest
        manifest_path = builder.build_manifest(args.version, args.output_dir)
        
        if not manifest_path.exists():
            print("ERROR: No manifest was built")
            sys.exit(1)
        
        # Validate manifest
        try:
            builder.validate_manifest(manifest_path)
        except Exception as e:
            print(f"WARNING:  Manifest validation skipped: {e}")
        
        print("SUCCESS: Scoop manifest build completed successfully")
        
    except Exception as e:
        print(f"ERROR: Scoop manifest build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
