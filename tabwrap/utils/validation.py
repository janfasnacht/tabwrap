# tex_compiler/utils/validation.py
import os
from pathlib import Path
from typing import Union, Tuple

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass

def validate_tex_file(file_path: Union[str, Path]) -> Path:
    """Validate a TeX file exists and has correct format."""
    path = Path(file_path)

    if not path.exists():
        raise FileValidationError(f"File not found: {path}")
    if not path.is_file():
        raise FileValidationError(f"Not a file: {path}")
    if path.suffix.lower() != '.tex':
        raise FileValidationError(f"Not a TeX file: {path}")
    if path.stat().st_size == 0:
        raise FileValidationError(f"Empty file: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                raise FileValidationError(f"File contains no content: {path}")
    except UnicodeDecodeError:
        raise FileValidationError(f"File is not valid UTF-8: {path}")

    return path

def validate_output_dir(dir_path: Union[str, Path]) -> Path:
    """Validate output directory exists or can be created."""
    path = Path(dir_path)

    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise FileValidationError(f"Permission denied creating directory: {path}")
    except OSError as e:
        raise FileValidationError(f"Error creating directory: {path} - {e}")

    if not os.access(path, os.W_OK):
        raise FileValidationError(f"Output directory not writable: {path}")

    return path

def is_valid_tabular_content(content: str) -> Tuple[bool, str]:
    """Check if content appears to be a valid LaTeX tabular environment."""
    if not content.strip():
        return False, "Empty content"

    if not any(env in content for env in ['\\begin{tabular}', '\\begin{tabularx}']):
        return False, "No tabular environment found"

    environments = {
        'tabular': content.count('\\begin{tabular}') == content.count('\\end{tabular}'),
        'tabularx': content.count('\\begin{tabularx}') == content.count('\\end{tabularx}')
    }

    if not any(environments.values()):
        return False, "Mismatched tabular environment tags"

    if '{@' not in content and '{|' not in content and '{l' not in content and '{c' not in content and '{r' not in content:
        return False, "Missing or invalid column specification"

    return True, ""
