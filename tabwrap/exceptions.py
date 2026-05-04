"""Exception hierarchy for tabwrap.

Errors raised in the compile pipeline are typed so the API and CLI can route
them by class instead of string-matching the message.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .latex.error_handling import ParsedLatexError


class TabwrapError(Exception):
    """Base class for all tabwrap-raised errors."""


class InvalidLatexError(TabwrapError):
    """User-supplied LaTeX content is invalid (validation / syntax)."""


class LatexCompilationError(TabwrapError):
    """pdflatex reported one or more errors while compiling."""

    def __init__(self, errors: list[ParsedLatexError] | None = None, message: str | None = None) -> None:
        self.errors: list[ParsedLatexError] = list(errors) if errors else []
        self.raw_message = message
        super().__init__(self._format())

    def _format(self) -> str:
        if self.errors:
            from .latex.error_handling import LaTeXErrorParser

            return f"LaTeX compilation failed:\n{LaTeXErrorParser.format_error_report(self.errors)}"
        return self.raw_message or "LaTeX compilation failed"


class ConversionError(TabwrapError):
    """A PDF→PNG/SVG conversion failed."""


class DependencyError(TabwrapError):
    """A required external tool (pdflatex, pdf2svg, ...) is missing."""
