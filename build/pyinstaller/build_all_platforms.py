"""
Cross-platform build orchestrator.

Coordinates building binaries for all target platforms using various methods
including native builds, cross-compilation, and GitHub Actions.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Import build modules using sys.path approach since we're not a proper package
build_dir = Path(__file__).parent.parent
sys.path.insert(0, str(build_dir))

from core.config import BuildConfig
from core.platform_detector import PlatformDetector
from core.version_manager import VersionManager
from pyinstaller.binary_builder import BinaryBuilder


class CrossPlatformBuilder:
    """Orchestrates building binaries for all target platforms."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize cross-platform builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        self.platform_detector = PlatformDetector()
        self.binary_builder = BinaryBuilder(self.config)
    
    def get_build_matrix(self) -> List[Dict[str, str]]:
        """
        Get build matrix for GitHub Actions.
        
        Returns:
            List of build configurations
        """
        matrix = []
        
        for platform_name, arch in self.platform_detector.get_target_platforms():
            # Determine runner OS
            if platform_name == "linux":
                runner_os = "ubuntu-latest"
            elif platform_name == "darwin":
                if arch == "x86_64":
                    runner_os = "macos-13"  # Intel runner
                else:
                    runner_os = "macos-latest"  # Apple Silicon runner
            elif platform_name == "windows":
                runner_os = "windows-latest"
            
            matrix.append({
                "platform": platform_name,
                "arch": arch,
                "runner": runner_os,
                "target": f"{platform_name}-{arch}",
            })
        
        return matrix
    
    def generate_github_actions_workflow(self) -> str:
        """Generate GitHub Actions workflow for building binaries."""
        matrix = self.get_build_matrix()
        
        workflow = f"""name: Build Binaries

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to build'
        required: false
        type: string

jobs:
  build:
    strategy:
      matrix:
        include:
{self._format_matrix_for_yaml(matrix)}
    
    runs-on: ${{{{ matrix.runner }}}}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: 'latest'
        virtualenvs-create: true
        virtualenvs-in-project: true
    
    - name: Install dependencies
      run: poetry install --no-dev
    
    - name: Build binary
      run: |
        poetry run python -m build.pyinstaller.binary_builder \\
          --platform ${{{{ matrix.platform }}}} \\
          --arch ${{{{ matrix.arch }}}} \\
          --optimize
    
    - name: Test binary
      run: |
        poetry run python -m build.pyinstaller.binary_builder \\
          --platform ${{{{ matrix.platform }}}} \\
          --arch ${{{{ matrix.arch }}}} \\
          --test
    
    - name: Upload binary
      uses: actions/upload-artifact@v4
      with:
        name: giv-${{{{ matrix.target }}}}
        path: dist/*/giv-${{{{ matrix.target }}}}*
        retention-days: 30
    
    - name: Create release (on tag)
      if: startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*/giv-${{{{ matrix.target }}}}*
        draft: false
        prerelease: ${{{{ contains(github.ref, '-') }}}}
      env:
        GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
"""
        
        return workflow
    
    def _format_matrix_for_yaml(self, matrix: List[Dict[str, str]]) -> str:
        """Format build matrix for YAML."""
        lines = []
        for item in matrix:
            lines.append(f"          - platform: {item['platform']}")
            lines.append(f"            arch: {item['arch']}")
            lines.append(f"            runner: {item['runner']}")
            lines.append(f"            target: {item['target']}")
        return "\\n".join(lines)
    
    def build_locally_available(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build binaries for platforms available on current system.
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Dictionary mapping platform-arch to binary path
        """
        print("Building binaries for locally available platforms...")
        
        if version is None:
            version = self.version_manager.get_version()
        
        return self.binary_builder.build_all_platforms(version)
    
    def build_with_docker(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build binaries using Docker for cross-platform compilation.
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Dictionary mapping platform-arch to binary path
        """
        if not self.platform_detector.check_docker_available():
            raise RuntimeError("Docker is not available for cross-platform builds")
        
        print("Building binaries using Docker...")
        
        if version is None:
            version = self.version_manager.get_version()
        
        results = {}
        target_platforms = self.platform_detector.get_target_platforms()
        
        for platform_name, arch in target_platforms:
            try:
                binary_path = self._build_with_docker_platform(version, platform_name, arch)
                if binary_path:
                    results[f"{platform_name}-{arch}"] = binary_path
            except Exception as e:
                print(f"Error building {platform_name}-{arch} with Docker: {e}")
                continue
        
        return results
    
    def _build_with_docker_platform(self, version: str, platform_name: str, arch: str) -> Optional[Path]:
        """Build binary for specific platform using Docker."""
        print(f"Building {platform_name}-{arch} using Docker...")
        
        # Determine Docker image
        if platform_name == "linux":
            if arch == "x86_64":
                docker_image = "python:3.8-slim"
                docker_platform = "linux/amd64"
            elif arch == "arm64":
                docker_image = "python:3.8-slim"
                docker_platform = "linux/arm64"
            else:
                print(f"Unsupported architecture for Docker build: {arch}")
                return None
        else:
            print(f"Docker cross-compilation not supported for {platform_name}")
            return None
        
        # Prepare build command
        build_script = f"""
set -e
cd /workspace
pip install poetry
poetry install --no-dev
poetry run python -m build.pyinstaller.binary_builder --platform {platform_name} --arch {arch} --optimize
"""
        
        cmd = [
            "docker", "run", "--rm",
            "--platform", docker_platform,
            "-v", f"{self.config.project_root}:/workspace",
            "-w", "/workspace",
            docker_image,
            "bash", "-c", build_script
        ]
        
        try:
            subprocess.run(cmd, check=True)
            
            # Find the built binary
            binary_name = self.config.get_binary_name(platform_name, arch)
            binary_path = self.config.get_platform_dist_dir(version, platform_name, arch) / binary_name
            
            if binary_path.exists():
                return binary_path
            else:
                print(f"Docker build completed but binary not found: {binary_path}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"Docker build failed for {platform_name}-{arch}: {e}")
            return None
    
    def build_all_methods(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build binaries using all available methods.
        
        Args:
            version: Version to build (auto-detected if not provided)
            
        Returns:
            Dictionary mapping platform-arch to binary path
        """
        if version is None:
            version = self.version_manager.get_version()
        
        print(f"Building all binaries for version {version}")
        print("=" * 50)
        
        all_results = {}
        
        # Try local builds first
        print("\\n1. Building locally available platforms...")
        try:
            local_results = self.build_locally_available(version)
            all_results.update(local_results)
            print(f"✓ Local builds completed: {len(local_results)} binaries")
        except Exception as e:
            print(f"✗ Local builds failed: {e}")
        
        # Try Docker builds for missing platforms
        missing_platforms = set(f"{p}-{a}" for p, a in self.platform_detector.get_target_platforms()) - set(all_results.keys())
        
        if missing_platforms and self.platform_detector.check_docker_available():
            print(f"\\n2. Building missing platforms with Docker: {', '.join(missing_platforms)}")
            try:
                docker_results = self.build_with_docker(version)
                all_results.update(docker_results)
                print(f"✓ Docker builds completed: {len(docker_results)} binaries")
            except Exception as e:
                print(f"✗ Docker builds failed: {e}")
        
        # Report final results
        print(f"\\nBuild Summary:")
        print("=" * 30)
        for platform_arch, binary_path in all_results.items():
            size_mb = binary_path.stat().st_size / (1024 * 1024)
            print(f"✓ {platform_arch}: {binary_path} ({size_mb:.1f} MB)")
        
        still_missing = set(f"{p}-{a}" for p, a in self.platform_detector.get_target_platforms()) - set(all_results.keys())
        if still_missing:
            print(f"\\nMissing platforms (use GitHub Actions): {', '.join(still_missing)}")
        
        return all_results
    
    def create_release_assets(self, version: str, binaries: Dict[str, Path]) -> Path:
        """
        Create release assets directory with all binaries and checksums.
        
        Args:
            version: Version string
            binaries: Dictionary mapping platform-arch to binary path
            
        Returns:
            Path to release assets directory
        """
        assets_dir = self.config.get_dist_dir(version) / "release-assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy binaries to assets directory
        for platform_arch, binary_path in binaries.items():
            dest_path = assets_dir / binary_path.name
            if binary_path != dest_path:
                shutil.copy2(binary_path, dest_path)
        
        # Generate checksums
        checksums_file = assets_dir / "checksums.txt"
        with open(checksums_file, 'w') as f:
            for binary_file in sorted(assets_dir.glob("giv-*")):
                if binary_file.name != "checksums.txt":
                    # Calculate SHA256
                    import hashlib
                    sha256_hash = hashlib.sha256()
                    with open(binary_file, 'rb') as bf:
                        for chunk in iter(lambda: bf.read(4096), b""):
                            sha256_hash.update(chunk)
                    
                    f.write(f"{sha256_hash.hexdigest()}  {binary_file.name}\\n")
        
        print(f"✓ Release assets prepared in: {assets_dir}")
        return assets_dir


def main():
    """CLI interface for cross-platform builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build giv CLI binaries for all platforms")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--local-only", action="store_true", help="Build only locally available platforms")
    parser.add_argument("--docker-only", action="store_true", help="Build only with Docker")
    parser.add_argument("--generate-workflow", action="store_true", help="Generate GitHub Actions workflow")
    parser.add_argument("--create-assets", action="store_true", help="Create release assets directory")
    
    args = parser.parse_args()
    
    builder = CrossPlatformBuilder()
    
    if args.generate_workflow:
        workflow = builder.generate_github_actions_workflow()
        workflow_file = builder.config.project_root / ".github" / "workflows" / "build-binaries.yml"
        workflow_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(workflow_file, 'w') as f:
            f.write(workflow)
        
        print(f"✓ GitHub Actions workflow generated: {workflow_file}")
        return
    
    version = args.version or builder.version_manager.get_version()
    
    if args.local_only:
        results = builder.build_locally_available(version)
    elif args.docker_only:
        results = builder.build_with_docker(version)
    else:
        results = builder.build_all_methods(version)
    
    if args.create_assets and results:
        builder.create_release_assets(version, results)


if __name__ == "__main__":
    main()