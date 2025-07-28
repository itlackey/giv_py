"""
Binary builder using PyInstaller.

Handles the compilation of Python source code into standalone executables
for different platforms and architectures.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import build modules using sys.path approach since we're not a proper package
build_dir = Path(__file__).parent.parent
sys.path.insert(0, str(build_dir))

from core.config import BuildConfig
from core.platform_detector import PlatformDetector
from core.version_manager import VersionManager


class BinaryBuilder:
    """Builds standalone binaries using PyInstaller."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize binary builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
        self.platform_detector = PlatformDetector()
        
        # PyInstaller spec file
        self.spec_file = Path(__file__).parent / "giv.spec"
        
    def check_dependencies(self) -> None:
        """Check that required tools are available."""
        missing = []
        
        # Check PyInstaller
        try:
            import PyInstaller
        except ImportError:
            missing.append("PyInstaller")
        
        # Check UPX (optional but recommended)
        try:
            subprocess.run(["upx", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: UPX not found. Binary compression will be skipped.")
        
        if missing:
            raise RuntimeError(f"Missing required dependencies: {', '.join(missing)}")
    
    def build_current_platform(self, version: Optional[str] = None) -> Path:
        """
        Build binary for the current platform.
        
        Args:
            version: Version string (auto-detected if not provided)
            
        Returns:
            Path to built binary
        """
        if version is None:
            version = self.version_manager.get_version()
        
        platform_name = self.platform_detector.get_current_platform()
        arch = self.platform_detector.get_current_architecture()
        
        return self._build_binary(version, platform_name, arch)
    
    def _create_build_spec(self, spec_file: Path, output_dir: Path, platform_name: str, arch: str) -> None:
        """Create a custom PyInstaller spec file for the build."""
        # Create a simplified spec file that works with PyInstaller
        binary_name = "giv.exe" if platform_name == "windows" else "giv"
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
Generated PyInstaller spec file for giv CLI binary.
"""

import os
from pathlib import Path

# Define the project root relative to this spec file location
spec_dir = Path(os.path.dirname(os.path.abspath(SPECPATH)))
project_root = spec_dir.parent.parent

block_cipher = None

# Define the main entry point
main_script = project_root / "giv" / "__main__.py"

# Data files to include
datas = [
    # Include template files
    (str(project_root / "giv" / "templates"), "giv/templates"),
]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    'giv',
    'giv.cli',
    'giv.config',
    'giv.git_utils',
    'giv.llm_utils',
    'giv.template_utils',
    'giv.output_utils',
    'giv.project_metadata',
    'giv.markdown_utils',
    'requests',
    'click',
    'packaging',
    'importlib.metadata',
]

# Analysis phase
a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'unittest',
        'test',
        'tests',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{binary_name.replace(".exe", "")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application
    disable_windowed_traceback=False,
    target_arch={'None' if platform_name != 'darwin' else f"'{arch}'"},
    codesign_identity=None,
    entitlements_file=None,
)
'''
        
        # Write the custom spec file
        with open(spec_file, 'w') as f:
            f.write(spec_content)
    
    def _build_binary(self, version: str, platform_name: str, arch: str) -> Path:
        """
        Build binary for specific platform and architecture.
        
        Args:
            version: Version string
            platform_name: Target platform (linux, darwin, windows)
            arch: Target architecture (x86_64, arm64)
            
        Returns:
            Path to built binary
        """
        print(f"Building binary for {platform_name}-{arch} version {version}")
        
        # Check dependencies
        self.check_dependencies()
        
        # Prepare build directory
        build_dir = self.config.temp_root / "pyinstaller" / f"{platform_name}-{arch}"
        build_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare output directory
        output_dir = self.config.get_platform_dist_dir(version, platform_name, arch)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine binary name (simple name for PyInstaller)
        binary_name = self.config.get_binary_name(platform_name, arch)
        # Platform-specific name for final distribution
        platform_binary_name = self.config.get_platform_binary_name(platform_name, arch)
        
        # Create a temporary spec file with custom settings
        temp_spec_file = build_dir / "giv_build.spec"
        self._create_build_spec(temp_spec_file, output_dir, platform_name, arch)
        
        # Prepare PyInstaller command (when using .spec file, don't pass conflicting options)
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",  # Clean cache
            "--distpath", str(output_dir),
            "--workpath", str(build_dir / "work"),
            str(temp_spec_file),
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.config.project_root)
        
        # Run PyInstaller
        print(f"Running PyInstaller...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.config.project_root,
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
            print("PyInstaller completed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller failed with exit code {e.returncode}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise RuntimeError(f"PyInstaller build failed for {platform_name}-{arch}")
        
        # Find the built binary
        if platform_name == "windows":
            binary_path = output_dir / "giv.exe"
        else:
            binary_path = output_dir / "giv"
        
        if not binary_path.exists():
            raise RuntimeError(f"Built binary not found at {binary_path}")
        
        # Rename to platform-specific name for distribution
        final_binary_path = output_dir / platform_binary_name
        if binary_path != final_binary_path:
            shutil.move(str(binary_path), str(final_binary_path))
        
        # Make executable on Unix systems
        if platform_name in ["linux", "darwin"]:
            final_binary_path.chmod(0o755)
        
        # Get binary size
        size_mb = final_binary_path.stat().st_size / (1024 * 1024)
        print(f"✓ Built binary: {final_binary_path}")
        print(f"  Size: {size_mb:.1f} MB")
        
        return final_binary_path
    
    def test_binary(self, binary_path: Path) -> bool:
        """
        Test that the built binary works correctly.
        
        Args:
            binary_path: Path to binary to test
            
        Returns:
            True if binary works, False otherwise
        """
        if not binary_path.exists():
            print(f"Error: Binary not found at {binary_path}")
            return False
        
        print(f"Testing binary: {binary_path}")
        
        # Test basic functionality
        tests = [
            ["--version"],
            ["--help"],
        ]
        
        for test_args in tests:
            try:
                result = subprocess.run(
                    [str(binary_path)] + test_args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True
                )
                print(f"✓ Test passed: giv {' '.join(test_args)}")
                
            except subprocess.CalledProcessError as e:
                print(f"✗ Test failed: giv {' '.join(test_args)}")
                print(f"  Exit code: {e.returncode}")
                print(f"  STDERR: {e.stderr}")
                return False
                
            except subprocess.TimeoutExpired:
                print(f"✗ Test timed out: giv {' '.join(test_args)}")
                return False
        
        print("✓ All binary tests passed")
        return True
    
    def build_all_platforms(self, version: Optional[str] = None) -> Dict[str, Path]:
        """
        Build binaries for all buildable platforms.
        
        Args:
            version: Version string (auto-detected if not provided)
            
        Returns:
            Dictionary mapping platform-arch to binary path
        """
        if version is None:
            version = self.version_manager.get_version()
        
        buildable_platforms = self.platform_detector.get_buildable_platforms()
        results = {}
        
        for platform_name, arch in buildable_platforms:
            try:
                binary_path = self._build_binary(version, platform_name, arch)
                
                # Test the binary
                if self.test_binary(binary_path):
                    results[f"{platform_name}-{arch}"] = binary_path
                else:
                    print(f"Warning: Binary for {platform_name}-{arch} failed tests")
                    
            except Exception as e:
                print(f"Error building binary for {platform_name}-{arch}: {e}")
                continue
        
        return results
    
    def optimize_binary(self, binary_path: Path) -> None:
        """
        Optimize binary size and performance.
        
        Args:
            binary_path: Path to binary to optimize
        """
        if not binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
        
        original_size = binary_path.stat().st_size
        
        # Try UPX compression if available
        try:
            subprocess.run(
                ["upx", "--best", str(binary_path)],
                check=True,
                capture_output=True
            )
            
            new_size = binary_path.stat().st_size
            compression_ratio = (1 - new_size / original_size) * 100
            
            print(f"✓ UPX compression applied")
            print(f"  Original size: {original_size / 1024 / 1024:.1f} MB")
            print(f"  Compressed size: {new_size / 1024 / 1024:.1f} MB")
            print(f"  Compression ratio: {compression_ratio:.1f}%")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("UPX compression not available or failed")


def main():
    """CLI interface for binary builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build giv CLI binaries")
    parser.add_argument("--version", help="Version to build (auto-detected if not provided)")
    parser.add_argument("--platform", help="Target platform (current platform if not provided)")
    parser.add_argument("--arch", help="Target architecture (current arch if not provided)")
    parser.add_argument("--all", action="store_true", help="Build for all buildable platforms")
    parser.add_argument("--test", action="store_true", help="Test built binaries")
    parser.add_argument("--optimize", action="store_true", help="Optimize binaries with UPX")
    
    args = parser.parse_args()
    
    builder = BinaryBuilder()
    
    if args.all:
        print("Building binaries for all buildable platforms...")
        results = builder.build_all_platforms(args.version)
        
        print(f"\nBuild Summary:")
        print("=" * 40)
        for platform_arch, binary_path in results.items():
            print(f"✓ {platform_arch}: {binary_path}")
        
        if args.optimize:
            print("\nOptimizing binaries...")
            for binary_path in results.values():
                builder.optimize_binary(binary_path)
    
    else:
        print("Building binary for current platform...")
        binary_path = builder.build_current_platform(args.version)
        
        if args.test:
            builder.test_binary(binary_path)
        
        if args.optimize:
            builder.optimize_binary(binary_path)


if __name__ == "__main__":
    main()