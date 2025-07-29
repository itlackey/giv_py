"""
Utility functions for build system.
"""
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def replace_template_vars(template_content: str, variables: Dict[str, str]) -> str:
    """Replace template variables in content."""
    result = template_content
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, value)
    return result


def run_command(cmd: list, cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(
        cmd, 
        cwd=cwd, 
        check=check, 
        capture_output=True, 
        text=True
    )


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_files(src_files: list, dest_dir: Path, preserve_structure: bool = False) -> None:
    """Copy files to destination directory."""
    ensure_dir(dest_dir)
    
    for src_file in src_files:
        src_path = Path(src_file)
        if not src_path.exists():
            continue
            
        if preserve_structure:
            # Preserve directory structure
            rel_path = src_path.relative_to(src_path.parents[-1])
            dest_path = dest_dir / rel_path
            ensure_dir(dest_path.parent)
        else:
            dest_path = dest_dir / src_path.name
            
        shutil.copy2(src_path, dest_path)


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
