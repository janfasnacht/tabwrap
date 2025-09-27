# tabwrap/utils/error_handling.py
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompilationError:
    """Structured compilation error information."""

    file: Path
    line_number: int | None
    error_type: str
    suggestion: str
    original_error: str


@dataclass
class CompilationResult:
    """Result of compiling a single file."""

    file: Path
    success: bool
    output_path: Path | None = None
    error: Exception | None = None


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

    @classmethod
    def parse_latex_log(cls, log_content: str, tex_file: Path) -> list[CompilationError]:
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
                    CompilationError(
                        file=tex_file,
                        line_number=line_number,
                        error_type=error_type,
                        suggestion=suggestion,
                        original_error=match.group(0),
                    )
                )

        return errors

    @classmethod
    def format_error_report(cls, errors: list[CompilationError]) -> str:
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

    # Check for tabular environment issues
    if "begin{tabular}" in content:
        if "end{tabular}" not in content:
            issues.append("Missing \\end{tabular}")

        # Check for lines ending without \\
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and "&" in line and not line.endswith("\\\\") and not line.endswith("\\"):
                if "toprule" not in line and "midrule" not in line and "bottomrule" not in line:
                    issues.append(f"Line {i} contains & but doesn't end with \\\\")

    return issues
