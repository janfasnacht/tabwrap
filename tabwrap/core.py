# tex_compiler/core.py
import subprocess
import time
from enum import Enum
from pathlib import Path

from .config import setup_logging
from .exceptions import (
    DependencyError,
    InvalidLatexError,
    LatexCompilationError,
)
from .io import clean_up, create_temp_dir
from .latex import (
    BatchCompilationResult,
    CompilationResult,
    FileValidationError,
    LaTeXErrorParser,
    TexTemplates,
    check_latex_dependencies,
    clean_filename_for_display,
    create_include_command,
    detect_packages,
    format_dependency_report,
    is_valid_tabular_content,
    validate_output_dir,
    validate_tex_content_syntax,
    validate_tex_file,
)
from .output import (
    bundle_artifacts,
    convert_pdf_to_cropped_png,
    convert_pdf_to_svg,
    get_pdf_page_count,
)
from .result import CompileResult, Format, resolve_formats

logger = setup_logging(module_name=__name__)


class CompilerMode(Enum):
    CLI = "cli"
    WEB = "web"


class TabWrap:
    """Core table compilation and processing functionality."""

    def __init__(self, mode: CompilerMode = CompilerMode.CLI):
        self.mode = mode
        self.generated_pdfs: list[Path] = []
        self.temp_dir: Path | None = None

    def check_dependencies(self, require_convert: bool = False) -> None:
        """Check LaTeX dependencies and raise error if missing critical ones."""
        deps = check_latex_dependencies()

        missing = []
        if not deps["pdflatex"]:
            missing.append("pdflatex is required but not found. Install a LaTeX distribution.")

        if require_convert and not deps["convert"]:
            missing.append("ImageMagick 'convert' is required for PNG output but not found.")

        if missing:
            error_msg = "\n".join(missing)
            error_msg += f"\n\n{format_dependency_report(deps)}"
            raise DependencyError(error_msg)

    def compile_tex(
        self,
        input_path: Path | str,
        output_dir: Path | str,
        *,
        suffix: str = "_compiled",
        packages: str = "",
        # `landscape` and `no_rescale` are deprecated no-ops kept for backwards
        # compatibility with shell scripts, API form payloads, and the web UI
        # in the tabwrap-web repo. Remove in 2.0.
        landscape: bool = False,
        no_rescale: bool = False,
        show_filename: bool = False,
        keep_tex: bool = False,
        formats: set[Format] | str | None = None,
        png: bool = False,
        svg: bool = False,
        combine_pdf: bool = False,
        recursive: bool = False,
        parallel: bool = False,
        max_workers: int = None,
    ) -> CompileResult:
        """Compile TeX table(s) and return a structured CompileResult.

        `formats` accepts a set of Format values or a comma-separated string.
        The legacy `png` / `svg` booleans remain supported as aliases when
        `formats` is not supplied.
        """
        if (png or svg) and formats:
            logger.warning("png/svg flags ignored because explicit formats were provided")
        if landscape or no_rescale:
            ignored = ", ".join(name for name, on in (("landscape", landscape), ("no_rescale", no_rescale)) if on)
            logger.warning(f"{ignored} option(s) ignored: the standalone document class auto-fits content")
        resolved_formats = resolve_formats(formats, png=png, svg=svg)
        needs_image_convert = bool(resolved_formats & {Format.PNG})
        self.check_dependencies(require_convert=needs_image_convert)

        try:
            input_path = Path(input_path)
            if input_path.is_dir():
                pattern = "**/*.tex" if recursive else "*.tex"
                all_tex_files = list(input_path.glob(pattern))
                if suffix:
                    tex_files = [f for f in all_tex_files if not f.stem.endswith(suffix)]
                else:
                    tex_files = all_tex_files
                if not tex_files:
                    search_type = "recursively" if recursive else ""
                    raise FileValidationError(f"No .tex files found {search_type} in {input_path}")
                for tex_file in tex_files:
                    validate_tex_file(tex_file)
            else:
                validate_tex_file(input_path)
                tex_files = [input_path]

            output_dir = validate_output_dir(output_dir)

            batch_result = self._compile_batch(
                tex_files,
                output_dir,
                suffix=suffix,
                packages=packages,
                landscape=landscape,
                no_rescale=no_rescale,
                show_filename=show_filename,
                keep_tex=self.mode == CompilerMode.CLI and keep_tex,
                formats=resolved_formats,
                combine_pdf=combine_pdf,
                parallel=parallel,
                max_workers=max_workers,
            )

            if batch_result.all_failed:
                error_report = LaTeXErrorParser.format_batch_result(batch_result)
                # Surface the first structured error if we have one; otherwise generic.
                first_error = batch_result.failures[0].error if batch_result.failures else None
                if isinstance(first_error, InvalidLatexError | LatexCompilationError):
                    raise first_error
                raise LatexCompilationError(message=error_report)

            successes = [r for r in batch_result.successes if r.result is not None]

            # Combined PDF mode (PDF only, multiple files)
            if combine_pdf and Format.PDF in resolved_formats and len(resolved_formats) == 1 and len(successes) > 1:
                pdf_paths = [s.result.artifacts[Format.PDF] for s in successes if Format.PDF in s.result.artifacts]
                combined_path = self._combine_pdfs(pdf_paths, output_dir)
                if batch_result.has_failures:
                    logger.warning(LaTeXErrorParser.format_batch_result(batch_result))
                if combined_path is None:
                    raise LatexCompilationError(message="Combined PDF generation produced no output")
                return CompileResult(
                    artifacts={Format.PDF: combined_path},
                    page_counts={Format.PDF: get_pdf_page_count(combined_path)},
                )

            if successes:
                if batch_result.has_failures:
                    logger.warning(LaTeXErrorParser.format_batch_result(batch_result))
                return successes[0].result

            # Should be unreachable given all_failed handled above.
            raise LatexCompilationError(message="No output produced")

        except Exception:
            self._cleanup()
            raise

    def _compile_batch(self, tex_files: list[Path], output_dir: Path, **options) -> BatchCompilationResult:
        """Compile multiple files with error recovery."""
        parallel = options.pop("parallel", False)
        max_workers = options.pop("max_workers", None)

        if parallel and len(tex_files) > 1:
            return self._compile_batch_parallel(tex_files, output_dir, max_workers, **options)
        else:
            return self._compile_batch_sequential(tex_files, output_dir, **options)

    def _compile_batch_sequential(self, tex_files: list[Path], output_dir: Path, **options) -> BatchCompilationResult:
        """Compile multiple files sequentially with error recovery."""
        successes = []
        failures = []

        for tex_file in tex_files:
            try:
                result = self._process_single_file(tex_file, output_dir, **options)
                successes.append(CompilationResult(file=tex_file, success=True, result=result))
                logger.info(f"✅ Compiled: {tex_file.name}")

            except Exception as e:
                failures.append(CompilationResult(file=tex_file, success=False, error=e))
                logger.error(f"❌ Failed: {tex_file.name} - {e}")
                continue

        return BatchCompilationResult(successes=successes, failures=failures)

    def _compile_batch_parallel(
        self, tex_files: list[Path], output_dir: Path, max_workers: int = None, **options
    ) -> BatchCompilationResult:
        """Compile multiple files in parallel with error recovery."""
        import concurrent.futures
        import os

        if max_workers is None:
            max_workers = min(len(tex_files), os.cpu_count() or 1)

        successes = []
        failures = []

        def compile_single_file(tex_file: Path) -> CompilationResult:
            try:
                result = self._process_single_file(tex_file, output_dir, **options)
                logger.info(f"✅ Compiled: {tex_file.name}")
                return CompilationResult(file=tex_file, success=True, result=result)
            except Exception as e:
                logger.error(f"❌ Failed: {tex_file.name} - {e}")
                return CompilationResult(file=tex_file, success=False, error=e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(compile_single_file, tex_file): tex_file for tex_file in tex_files}

            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                if result.success:
                    successes.append(result)
                else:
                    failures.append(result)

        return BatchCompilationResult(successes=successes, failures=failures)

    def _get_tex_files(self, input_path: Path, recursive: bool = False) -> list[Path]:
        """Get list of .tex files to process."""
        if input_path.is_dir():
            pattern = "**/*.tex" if recursive else "*.tex"
            return list(input_path.glob(pattern))
        return [input_path]

    def _process_single_file(self, tex_file: Path, output_dir: Path, **options) -> CompileResult:
        """Process a single TeX file."""
        with open(tex_file) as f:
            content = f.read()

        is_valid, error = is_valid_tabular_content(content)
        if not is_valid:
            raise InvalidLatexError(f"Invalid tabular content in {tex_file}: {error}")

        syntax_issues = validate_tex_content_syntax(content)
        if syntax_issues:
            issues_str = "\n  ".join(syntax_issues)
            raise InvalidLatexError(f"Syntax issues in {tex_file}:\n  {issues_str}")

        full_tex, detected_packages = self._prepare_latex_content(content, tex_file, **options)

        return self._compile_tex_file(
            tex_file,
            full_tex,
            output_dir,
            detected_packages=detected_packages,
            **options,
        )

    def _prepare_latex_content(self, content: str, tex_file: Path, **options) -> tuple[str, list[str]]:
        """
        Prepare LaTeX content with appropriate packages and formatting.

        Returns the formatted document and the list of auto-detected packages
        (so callers can surface them in CompileResult without re-running detection).
        """
        detected_packages = sorted(detect_packages(content))
        user_packages = [f"\\usepackage{{{pkg}}}" for pkg in options.get("packages", "").split(",") if pkg]
        all_packages = "\n".join(user_packages) + "\n" + "\n".join(detected_packages)

        underscore_package = ""
        if options.get("show_filename") and "_" in tex_file.name:
            underscore_package = "\\usepackage{underscore}  % Handle underscores in filenames"

        header = ""
        if options.get("show_filename"):
            header = r"\texttt{" + clean_filename_for_display(tex_file.name) + r"}\par\medskip"

        prepared = TexTemplates.SINGLE_TABLE.format(
            packages=all_packages,
            underscore=underscore_package,
            header=header,
            content=content,
        )
        return prepared, detected_packages

    def _cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and self.mode == CompilerMode.WEB:
            clean_up([self.temp_dir])
            self.temp_dir = None

    def _compile_tex_file(
        self,
        tex_file: Path,
        full_tex: str,
        output_dir: Path,
        *,
        formats: set[Format],
        suffix: str = "_compiled",
        keep_tex: bool = False,
        detected_packages: list[str] | None = None,
        **_options,
    ) -> CompileResult:
        """Compile TeX file and produce a structured CompileResult."""
        compiled_tex_name = tex_file.stem + suffix + ".tex"
        compiled_tex_path = output_dir / compiled_tex_name

        artifacts: dict[Format, Path] = {}
        page_counts: dict[Format, int] = {}
        warnings_list: list[str] = []
        timings: dict[str, float] = {}

        total_start = time.perf_counter()

        try:
            with open(compiled_tex_path, "w") as f:
                f.write(full_tex)

            pdf_path = output_dir / (tex_file.stem + suffix + ".pdf")
            if pdf_path.exists():
                pdf_path.unlink()

            pdflatex_start = time.perf_counter()
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(compiled_tex_path)],
                capture_output=True,
                text=True,
            )
            timings["pdflatex"] = time.perf_counter() - pdflatex_start

            log_path = output_dir / (tex_file.stem + suffix + ".log")
            log_content = log_path.read_text() if log_path.exists() else ""
            errors = LaTeXErrorParser.parse_latex_log(log_content, tex_file) if log_content else []
            warnings_list = LaTeXErrorParser.parse_latex_warnings(log_content) if log_content else []

            if errors:
                raise LatexCompilationError(errors=errors)

            if not pdf_path.exists():
                stderr_msg = result.stderr.strip() if result.stderr.strip() else "Unknown compilation error"
                raise LatexCompilationError(message=stderr_msg)

            pdf_page_count = get_pdf_page_count(pdf_path)

            if Format.PDF in formats:
                artifacts[Format.PDF] = pdf_path
                page_counts[Format.PDF] = pdf_page_count

            if Format.PNG in formats:
                png_start = time.perf_counter()
                png_path = convert_pdf_to_cropped_png(pdf_path, output_dir, suffix)
                timings["png_conversion"] = time.perf_counter() - png_start
                artifacts[Format.PNG] = png_path
                page_counts[Format.PNG] = 1

            if Format.SVG in formats:
                svg_start = time.perf_counter()
                svg_path = convert_pdf_to_svg(pdf_path, output_dir, suffix)
                timings["svg_conversion"] = time.perf_counter() - svg_start
                artifacts[Format.SVG] = svg_path
                page_counts[Format.SVG] = 1

            # Drop the intermediate PDF if it wasn't requested as an artifact.
            if Format.PDF not in formats and pdf_path.exists():
                clean_up([pdf_path])

            timings["total"] = time.perf_counter() - total_start

            return CompileResult(
                artifacts=artifacts,
                page_counts=page_counts,
                detected_packages=list(detected_packages or []),
                warnings=warnings_list,
                timings=timings,
            )

        finally:
            if not keep_tex or self.mode == CompilerMode.WEB:
                clean_up(
                    [
                        compiled_tex_path,
                        output_dir / (tex_file.stem + suffix + ".aux"),
                        output_dir / (tex_file.stem + suffix + ".log"),
                    ]
                )

    def _create_combined_pdf(self, pdf_files: list[Path], output_dir: Path) -> Path | None:
        """Create a combined PDF with table of contents."""
        if not pdf_files:
            return None

        try:
            include_commands = []
            for i, pdf_file in enumerate(pdf_files, start=1):
                display_name = clean_filename_for_display(pdf_file.stem)
                include_commands.extend(create_include_command(pdf_file, display_name, i + 1))

            combined_tex = TexTemplates.COMBINED_DOCUMENT.format(include_commands="\n".join(include_commands))

            combined_tex_path = output_dir / "tex_tables_combined.tex"
            with open(combined_tex_path, "w") as f:
                f.write(combined_tex)

            combined_pdf_path = output_dir / "tex_tables_combined.pdf"
            if combined_pdf_path.exists():
                combined_pdf_path.unlink()

            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(combined_tex_path)],
                    capture_output=True,
                    text=True,
                )

            log_path = output_dir / "tex_tables_combined.log"
            log_content = log_path.read_text() if log_path.exists() else ""
            errors = LaTeXErrorParser.parse_latex_log(log_content, combined_tex_path) if log_content else []

            if errors:
                raise LatexCompilationError(errors=errors)

            if not combined_pdf_path.exists():
                stderr_msg = result.stderr.strip() if result.stderr.strip() else "Unknown compilation error"
                raise LatexCompilationError(message=stderr_msg)

            return combined_pdf_path

        finally:
            if self.mode != CompilerMode.CLI:
                clean_up(
                    [
                        combined_tex_path,
                        output_dir / "tex_tables_combined.aux",
                        output_dir / "tex_tables_combined.log",
                        output_dir / "tex_tables_combined.toc",
                        output_dir / "tex_tables_combined.out",
                    ]
                )

    def _combine_pdfs(self, pdf_files: list[Path], output_dir: Path) -> Path | None:
        """Combine multiple PDFs into a single file with table of contents."""
        if not pdf_files:
            return None

        pdf_files = sorted(pdf_files, key=lambda x: x.stem)

        combined_pdf = self._create_combined_pdf(pdf_files, output_dir)

        if combined_pdf and self.mode == CompilerMode.WEB:
            for pdf in pdf_files:
                clean_up([pdf])

        return combined_pdf

    def __enter__(self):
        """Context manager entry."""
        if self.mode == CompilerMode.WEB:
            self.temp_dir = create_temp_dir()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()


__all__ = ["TabWrap", "CompilerMode", "bundle_artifacts"]
