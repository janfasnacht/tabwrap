# tabwrap/utils/error_handling.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..result import CompileResult


@dataclass
class ParsedLatexError:
    """Structured information for a single error parsed from a pdflatex log."""

    file: Path
    line_number: int | None
    error_type: str
    suggestion: str
    original_error: str


@dataclass
class CompilationResult:
    """Result of compiling a single file in a batch.

    Wraps the per-file CompileResult plus success/error metadata so the batch
    machinery can aggregate outcomes. `output_path` is preserved as a thin
    property for code paths that still expect a single Path.
    """

    file: Path
    success: bool
    result: CompileResult | None = None
    error: Exception | None = None

    @property
    def output_path(self) -> Path | None:
        if self.result is None or not self.result.artifacts:
            return None
        from ..result import Format as _Format

        return self.result.artifacts.get(_Format.PDF) or next(iter(self.result.artifacts.values()))


@dataclass
class BatchCompilationResult:
    """Result of compiling multiple files."""

    successes: list[CompilationResult]
    failures: list[CompilationResult]

    @property
    def success_count(self) -> int:
        return len(self.successes)

    @property
    def failure_count(self) -> int:
        return len(self.failures)

    @property
    def total_count(self) -> int:
        return self.success_count + self.failure_count

    @property
    def has_failures(self) -> bool:
        return self.failure_count > 0

    @property
    def all_failed(self) -> bool:
        return self.failure_count > 0 and self.success_count == 0


class LaTeXErrorParser:
    """Parse LaTeX compilation errors and provide helpful suggestions."""

    ERROR_PATTERNS = {
        "missing_package": {
            "pattern": r"! LaTeX Error: File `([^\']+)\.sty\' not found",
            "suggestion": "Install missing package: {0}. Try: tlmgr install {0}",
        },
        "misplaced_alignment": {
            "pattern": r"! Misplaced alignment tab character &",
            "suggestion": "Check & placement in tabular environment and ensure lines end with \\\\",
        },
        "undefined_control_sequence": {
            "pattern": r"! Undefined control sequence.*\n.*\\([a-zA-Z]+)",
            "suggestion": "Unknown command: \\{0}. Check spelling or add required package",
        },
        "missing_begin": {
            "pattern": r"! LaTeX Error: \\begin\{([^}]+)\} on input line (\d+) ended by \\end\{([^}]+)\}",
            "suggestion": "Environment mismatch: \\begin{{{0}}} ended by \\end{{{2}}} on line {1}",
        },
        "runaway_argument": {
            "pattern": r"! Runaway argument\?",
            "suggestion": "Missing closing brace or unexpected line break in command argument",
        },
    }

    WARNING_PATTERNS: dict[str, str] = {
        "overfull_hbox": r"Overfull \\hbox \([^)]*\)[^\n]*",
        "underfull_hbox": r"Underfull \\hbox \([^)]*\)[^\n]*",
        "overfull_vbox": r"Overfull \\vbox \([^)]*\)[^\n]*",
        "underfull_vbox": r"Underfull \\vbox \([^)]*\)[^\n]*",
        "font_warning": r"LaTeX Font Warning: [^\n]+",
        "reference_undefined": r"LaTeX Warning: Reference [^\n]+ undefined[^\n]*",
        "citation_undefined": r"LaTeX Warning: Citation [^\n]+ undefined[^\n]*",
        "package_warning": r"Package [\w]+ Warning: [^\n]+",
    }

    @classmethod
    def parse_latex_log(cls, log_content: str, tex_file: Path) -> list[ParsedLatexError]:
        """Parse LaTeX log and extract structured error information."""
        errors = []

        for error_type, config in cls.ERROR_PATTERNS.items():
            pattern = config["pattern"]
            suggestion_template = config["suggestion"]

            for match in re.finditer(pattern, log_content, re.MULTILINE):
                # Extract line number if present
                line_number = None
                line_match = re.search(r"l\.(\d+)", log_content[match.start() : match.start() + 200])
                if line_match:
                    line_number = int(line_match.group(1))

                # Format suggestion with matched groups
                try:
                    suggestion = suggestion_template.format(*match.groups())
                except (IndexError, KeyError):
                    suggestion = suggestion_template

                errors.append(
                    ParsedLatexError(
                        file=tex_file,
                        line_number=line_number,
                        error_type=error_type,
                        suggestion=suggestion,
                        original_error=match.group(0),
                    )
                )

        return errors

    @classmethod
    def parse_latex_warnings(cls, log_content: str) -> list[str]:
        """Extract human-readable warning messages from a pdflatex log.

        Returns deduplicated, trimmed strings — one entry per distinct warning.
        """
        seen: set[str] = set()
        warnings: list[str] = []
        for pattern in cls.WARNING_PATTERNS.values():
            for match in re.finditer(pattern, log_content):
                msg = match.group(0).strip()
                if msg and msg not in seen:
                    seen.add(msg)
                    warnings.append(msg)
        return warnings

    @classmethod
    def format_error_report(cls, errors: list[ParsedLatexError]) -> str:
        """Format errors into user-friendly report."""
        if not errors:
            return "Compilation failed with unknown error."

        report_lines = []
        for error in errors:
            file_info = f"{error.file.name}"
            if error.line_number:
                file_info += f" (line {error.line_number})"

            report_lines.extend(
                [
                    f"\n❌ {file_info}:",
                    f"   Error: {error.original_error.strip()}",
                    f"   → {error.suggestion}",
                ]
            )

        return "\n".join(report_lines)

    @classmethod
    def format_batch_result(cls, result: BatchCompilationResult) -> str:
        """Format batch compilation results into user-friendly report."""
        lines = []

        # Summary line
        if result.all_failed:
            lines.append(f"❌ All {result.total_count} files failed to compile:")
        elif result.has_failures:
            lines.append(f"⚠️  {result.failure_count} of {result.total_count} files failed to compile:")
        else:
            lines.append(f"✅ All {result.total_count} files compiled successfully!")
            return "\n".join(lines)

        # Show failures first
        if result.failures:
            lines.append("\n📋 Failed files:")
            for failure in result.failures:
                lines.append(f"   • {failure.file.name}")
                if hasattr(failure.error, "__str__"):
                    error_msg = str(failure.error).replace("LaTeX compilation failed:\n", "").strip()
                    if error_msg:
                        lines.append(f"     {error_msg}")

        # Show successes
        if result.successes and result.has_failures:
            lines.append(f"\n✅ Successfully compiled: {', '.join(s.file.name for s in result.successes)}")

        return "\n".join(lines)


def check_latex_dependencies() -> dict[str, bool]:
    """Check for LaTeX installation and required tools."""
    import shutil
    import subprocess

    dependencies = {
        "pdflatex": False,
        "convert": False,  # ImageMagick for PNG conversion
    }

    # Check pdflatex
    try:
        subprocess.run(["pdflatex", "--version"], capture_output=True, check=True, text=True)
        dependencies["pdflatex"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Check ImageMagick convert for PNG output
    dependencies["convert"] = shutil.which("convert") is not None

    return dependencies


def format_dependency_report(deps: dict[str, bool]) -> str:
    """Format dependency check results."""
    lines = ["LaTeX Dependencies:"]

    for tool, available in deps.items():
        status = "✅" if available else "❌"
        lines.append(f"  {status} {tool}")

        if not available:
            if tool == "pdflatex":
                lines.append("      Install a LaTeX distribution (TeX Live, MiKTeX)")
            elif tool == "convert":
                lines.append("      Install ImageMagick for PNG output support")

    missing_count = sum(1 for available in deps.values() if not available)
    if missing_count == 0:
        lines.append("\n✅ All dependencies satisfied!")
    else:
        lines.append(f"\n⚠️  {missing_count} dependencies missing")

    return "\n".join(lines)


def validate_tex_content_syntax(content: str) -> list[str]:
    """Basic syntax validation for common LaTeX errors."""
    issues = []

    # Check for unmatched braces
    brace_count = content.count("{") - content.count("}")
    if brace_count != 0:
        issues.append(f"Unmatched braces: {abs(brace_count)} {'extra {' if brace_count > 0 else 'missing }'}")

    # Check for table environment issues
    if "begin{table}" in content:
        if "end{table}" not in content:
            issues.append("Missing \\end{table}")

    # Check for tabular environment issues
    if "begin{tabular}" in content:
        if "end{tabular}" not in content:
            issues.append("Missing \\end{tabular}")

        # Check for lines ending without \\
        # Accumulate content across lines to handle multi-line rows
        lines = content.split("\n")
        accumulated = ""
        for line in lines:
            stripped = line.strip()
            accumulated += " " + stripped

            # If line ends with \\, we have a complete row - reset accumulator
            if stripped.endswith("\\\\") or stripped.endswith("\\"):
                accumulated = ""
            # Skip lines inside environments or special commands
            elif "begin{" in stripped or "end{" in stripped:
                accumulated = ""
            elif "toprule" in stripped or "midrule" in stripped or "bottomrule" in stripped:
                accumulated = ""

        # After processing all lines, check if there's unfinished row content with &
        if accumulated.strip() and "&" in accumulated:
            issues.append("Table row contains & but never ends with \\\\")

    return issues
