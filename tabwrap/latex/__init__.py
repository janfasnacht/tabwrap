# tabwrap/latex/__init__.py
"""LaTeX processing functionality."""

from .templates import TexTemplates
from .utils import (
    detect_packages,
    clean_filename_for_display,
    create_include_command
)
from .validation import (
    validate_tex_file,
    validate_output_dir,
    is_valid_tabular_content,
    FileValidationError
)
from .error_handling import (
    LaTeXErrorParser,
    check_latex_dependencies,
    validate_tex_content_syntax,
    format_dependency_report,
    CompilationError,
    CompilationResult,
    BatchCompilationResult
)

__all__ = [
    # Templates
    'TexTemplates',
    
    # Utilities
    'detect_packages',
    'clean_filename_for_display', 
    'create_include_command',
    
    # Validation
    'validate_tex_file',
    'validate_output_dir',
    'is_valid_tabular_content',
    'FileValidationError',
    
    # Error handling
    'LaTeXErrorParser',
    'check_latex_dependencies',
    'validate_tex_content_syntax',
    'format_dependency_report',
    'CompilationError',
    'CompilationResult',
    'BatchCompilationResult',
]