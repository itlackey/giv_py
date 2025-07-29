"""
PyPI package builder module.
"""

# Import the class directly without going through the module
import sys
from pathlib import Path

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import dependencies
from core.config import BuildConfig
from core.version_manager import VersionManager
from core.utils import ensure_dir

# Import the class definition directly
import subprocess
from typing import Dict, Optional

class PyPIBuilder:
    """Builds PyPI packages (source distribution and wheel)."""
    
    def __init__(self, config: Optional[BuildConfig] = None):
        """Initialize PyPI builder."""
        self.config = config or BuildConfig()
        self.version_manager = VersionManager(self.config.project_root)
    
    def build_packages(self, version: Optional[str] = None, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Build both source distribution and wheel using Poetry.
        
        Args:
            version: Version to build (auto-detected if not provided)
            output_dir: Output directory (defaults to dist/)
            
        Returns:
            Dictionary mapping package type to package path
        """
        if version is None:
            version = self.version_manager.get_build_version()
        
        if output_dir is None:
            output_dir = self.config.dist_dir
            
        print(f"🔨 Building PyPI packages for version {version}")
        
        ensure_dir(output_dir)
        
        # Use Poetry to build packages
        cmd = ["poetry", "build", "--output", str(output_dir)]
        
        try:
            subprocess.run(
                cmd, 
                cwd=self.config.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Poetry build completed")
            
            # Find built packages
            results = {}
            
            # Look for wheel
            wheel_files = list(output_dir.glob("*.whl"))
            if wheel_files:
                results["wheel"] = wheel_files[-1]  # Get most recent
                print(f"📦 Wheel: {results['wheel'].name}")
            
            # Look for source distribution
            sdist_files = list(output_dir.glob("*.tar.gz"))
            if sdist_files:
                results["sdist"] = sdist_files[-1]  # Get most recent
                print(f"📦 Source dist: {results['sdist'].name}")
            
            if not results:
                raise RuntimeError("No packages were built")
                
            return results
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Poetry build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            raise RuntimeError(f"Failed to build packages: {e}")

__all__ = ['PyPIBuilder']
