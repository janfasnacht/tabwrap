# tex_compiler/utils/validation.py
import os
from pathlib import Path


class FileValidationError(Exception):
    """Custom exception for file validation errors."""

    pass


def validate_tex_file(file_path: str | Path) -> Path:
    """Validate a TeX file exists and has correct format."""
    path = Path(file_path)

    if not path.exists():
        raise FileValidationError(f"File not found: {path}")
    if not path.is_file():
        raise FileValidationError(f"Not a file: {path}")
    if path.suffix.lower() != ".tex":
        raise FileValidationError(f"Not a TeX file: {path}")
    if path.stat().st_size == 0:
        raise FileValidationError(f"Empty file: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                raise FileValidationError(f"File contains no content: {path}")
    except UnicodeDecodeError:
        raise FileValidationError(f"File is not valid UTF-8: {path}")

    return path


def validate_output_dir(dir_path: str | Path) -> Path:
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


def is_valid_tabular_content(content: str) -> tuple[bool, str]:
    """
    Check if content appears to be a valid LaTeX table environment.

    Supports: tabular, tabularx, longtable, threeparttable, table

    Args:
        content: LaTeX content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content.strip():
        return False, "Empty content"

    # Check which table environments are present
    has_tabular = "\\begin{tabular}" in content
    has_tabularx = "\\begin{tabularx}" in content
    has_longtable = "\\begin{longtable}" in content
    has_threeparttable = "\\begin{threeparttable}" in content
    has_table = "\\begin{table}" in content

    # Must have at least one supported table environment
    # For table environment, it must contain an inner environment
    if has_table:
        if not (has_tabular or has_tabularx or has_longtable or has_threeparttable):
            return (
                False,
                "table environment must contain a table environment (tabular, tabularx, longtable, or threeparttable)",
            )
    elif not (has_tabular or has_tabularx or has_longtable or has_threeparttable):
        return False, "No supported table environment found (tabular, tabularx, longtable, threeparttable, or table)"

    # CRITICAL: longtable cannot be inside table float
    if has_table and has_longtable:
        return False, "longtable cannot be used inside table environment (longtable is its own float)"

    # Validate environment matching for table
    if has_table:
        if content.count("\\begin{table}") != content.count("\\end{table}"):
            return False, "Mismatched table environment tags"

    # Validate environment matching for each type that's present
    if has_tabular:
        if content.count("\\begin{tabular}") != content.count("\\end{tabular}"):
            return False, "Mismatched tabular environment tags"

    if has_tabularx:
        if content.count("\\begin{tabularx}") != content.count("\\end{tabularx}"):
            return False, "Mismatched tabularx environment tags"

    if has_longtable:
        if content.count("\\begin{longtable}") != content.count("\\end{longtable}"):
            return False, "Mismatched longtable environment tags"

    if has_threeparttable:
        if content.count("\\begin{threeparttable}") != content.count("\\end{threeparttable}"):
            return False, "Mismatched threeparttable environment tags"
        # threeparttable must contain a table environment inside
        if not (has_tabular or has_tabularx or has_longtable):
            return False, "threeparttable must contain a table environment (tabular, tabularx, or longtable)"

    # Check for column specification (required for actual table environments)
    # Skip this check if we only have table/threeparttable wrapper
    if has_tabular or has_tabularx or has_longtable:
        if "{@" not in content and "{|" not in content and "{l" not in content and "{c" not in content and "{r" not in content:
            return False, "Missing or invalid column specification"

    return True, ""
