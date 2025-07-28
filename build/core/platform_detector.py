"""
Platform and architecture detection utilities.

Provides functions to detect the current platform, available architectures,
and cross-compilation capabilities.
"""
import platform
import subprocess
import sys
from typing import Dict, List, Tuple, Optional


class PlatformDetector:
    """Detects platform information for build targeting."""
    
    @staticmethod
    def get_current_platform() -> str:
        """Get the current platform name."""
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "windows"
        else:
            return "linux"
    
    @staticmethod
    def get_current_architecture() -> str:
        """Get the current architecture."""
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            return "x86_64"
        elif machine in ["arm64", "aarch64"]:
            return "arm64"
        elif machine in ["i386", "i686"]:
            return "x86"
        else:
            return machine
    
    @staticmethod
    def get_python_info() -> Dict[str, str]:
        """Get Python version and implementation info."""
        return {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "architecture": platform.architecture()[0],
        }
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get comprehensive system information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
        }
    
    @staticmethod
    def can_cross_compile() -> Dict[str, List[str]]:
        """Determine which platforms/architectures can be targeted from current system."""
        current_platform = PlatformDetector.get_current_platform()
        current_arch = PlatformDetector.get_current_architecture()
        
        capabilities = {
            "native": [f"{current_platform}-{current_arch}"],
            "cross": [],
        }
        
        # Linux can cross-compile to different architectures with proper setup
        if current_platform == "linux":
            if current_arch == "x86_64":
                # Can potentially build ARM64 with cross-compilation tools
                capabilities["cross"].extend([
                    "linux-arm64",
                ])
        
        # macOS can build for both Intel and Apple Silicon
        elif current_platform == "darwin":
            if current_arch == "x86_64":
                capabilities["cross"].append("darwin-arm64")
            elif current_arch == "arm64":
                capabilities["cross"].append("darwin-x86_64")
        
        # Windows typically builds only for current architecture
        # Cross-compilation would require additional tooling
        
        return capabilities
    
    @staticmethod
    def check_docker_available() -> bool:
        """Check if Docker is available for cross-platform builds."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def check_pyinstaller_available() -> bool:
        """Check if PyInstaller is available."""
        try:
            import PyInstaller
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_target_platforms() -> List[Tuple[str, str]]:
        """Get list of target platforms and architectures."""
        return [
            ("linux", "x86_64"),
            ("linux", "arm64"),
            ("darwin", "x86_64"),
            ("darwin", "arm64"),
            ("windows", "x86_64"),
        ]
    
    @staticmethod
    def get_buildable_platforms() -> List[Tuple[str, str]]:
        """Get platforms that can be built from the current system."""
        current_platform = PlatformDetector.get_current_platform()
        current_arch = PlatformDetector.get_current_architecture()
        
        # Start with native platform
        buildable = [(current_platform, current_arch)]
        
        # Add cross-compilation targets based on platform
        if current_platform == "linux" and current_arch == "x86_64":
            # Linux x86_64 can potentially build ARM64 with proper tooling
            buildable.append(("linux", "arm64"))
        
        elif current_platform == "darwin":
            # macOS can build universal binaries or cross-compile
            if current_arch == "x86_64":
                buildable.append(("darwin", "arm64"))
            else:
                buildable.append(("darwin", "x86_64"))
        
        return buildable
    
    @classmethod
    def print_platform_info(cls) -> None:
        """Print comprehensive platform information."""
        print("Platform Information:")
        print("=" * 40)
        print(f"Current Platform: {cls.get_current_platform()}")
        print(f"Current Architecture: {cls.get_current_architecture()}")
        print()
        
        print("Python Information:")
        python_info = cls.get_python_info()
        for key, value in python_info.items():
            print(f"  {key.title()}: {value}")
        print()
        
        print("System Information:")
        system_info = cls.get_system_info()
        for key, value in system_info.items():
            print(f"  {key.title()}: {value}")
        print()
        
        print("Build Capabilities:")
        capabilities = cls.can_cross_compile()
        print(f"  Native: {', '.join(capabilities['native'])}")
        if capabilities['cross']:
            print(f"  Cross-compile: {', '.join(capabilities['cross'])}")
        else:
            print("  Cross-compile: None available")
        print()
        
        print("Tool Availability:")
        print(f"  Docker: {'✓' if cls.check_docker_available() else '✗'}")
        print(f"  PyInstaller: {'✓' if cls.check_pyinstaller_available() else '✗'}")
        print()
        
        print("Target Platforms:")
        for platform_name, arch in cls.get_target_platforms():
            buildable = "✓" if (platform_name, arch) in cls.get_buildable_platforms() else "✗"
            print(f"  {platform_name}-{arch}: {buildable}")


if __name__ == "__main__":
    PlatformDetector.print_platform_info()