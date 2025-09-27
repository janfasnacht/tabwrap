# tex_compiler/utils/file_handling.py
import logging
import os
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def create_temp_dir(prefix: str = "tex_compiler_") -> Path:
    """Create a temporary directory with proper permissions."""
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    os.chmod(temp_dir, 0o755)
    return temp_dir


def clean_up(files: list[str | Path], ignore_errors: bool = True):
    """Safely remove files and directories."""
    for file in files:
        path = Path(file)
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except (FileNotFoundError, PermissionError) as e:
            if not ignore_errors:
                raise
            logger.warning(f"Failed to remove {path}: {e}")


def ensure_dir_exists(path: str | Path) -> Path:
    """Ensure directory exists, create if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
