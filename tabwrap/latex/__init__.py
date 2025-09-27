# tabwrap/latex/__init__.py
"""LaTeX processing functionality."""

from .error_handling import (
    BatchCompilationResult,
    CompilationError,
    CompilationResult,
    LaTeXErrorParser,
    check_latex_dependencies,
    format_dependency_report,
    validate_tex_content_syntax,
)
from .templates import TexTemplates
from .utils import clean_filename_for_display, create_include_command, detect_packages
from .validation import FileValidationError, is_valid_tabular_content, validate_output_dir, validate_tex_file

__all__ = [
    # Templates
    "TexTemplates",
    # Utilities
    "detect_packages",
    "clean_filename_for_display",
    "create_include_command",
    # Validation
    "validate_tex_file",
    "validate_output_dir",
    "is_valid_tabular_content",
    "FileValidationError",
    # Error handling
    "LaTeXErrorParser",
    "check_latex_dependencies",
    "validate_tex_content_syntax",
    "format_dependency_report",
    "CompilationError",
    "CompilationResult",
    "BatchCompilationResult",
]
