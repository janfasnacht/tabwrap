"""Unit coverage for the tabwrap exception hierarchy."""

from pathlib import Path

from tabwrap import (
    ConversionError,
    DependencyError,
    InvalidLatexError,
    LatexCompilationError,
    TabwrapError,
)
from tabwrap.latex import FileValidationError, ParsedLatexError


def test_hierarchy_under_tabwrap_error():
    assert issubclass(InvalidLatexError, TabwrapError)
    assert issubclass(LatexCompilationError, TabwrapError)
    assert issubclass(ConversionError, TabwrapError)
    assert issubclass(DependencyError, TabwrapError)


def test_file_validation_error_is_invalid_latex_error():
    assert issubclass(FileValidationError, InvalidLatexError)


def test_latex_compilation_error_carries_parsed_errors():
    err = ParsedLatexError(
        file=Path("foo.tex"),
        line_number=12,
        error_type="missing_package",
        suggestion="install booktabs",
        original_error="! LaTeX Error: File `booktabs.sty' not found",
    )
    exc = LatexCompilationError(errors=[err])
    assert exc.errors == [err]
    assert "missing_package" in str(exc) or "booktabs" in str(exc)


def test_latex_compilation_error_with_message():
    exc = LatexCompilationError(message="pdflatex segfaulted")
    assert "pdflatex segfaulted" in str(exc)
    assert exc.errors == []
