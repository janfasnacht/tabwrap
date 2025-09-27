# tex_compiler/core.py
import subprocess
from enum import Enum
from pathlib import Path

from .config import setup_logging
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
from .output import convert_pdf_to_cropped_png, convert_pdf_to_svg

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
            raise RuntimeError(error_msg)

    def compile_tex(
        self,
        input_path: Path | str,
        output_dir: Path | str,
        *,
        suffix: str = "_compiled",
        packages: str = "",
        landscape: bool = False,
        no_rescale: bool = False,
        show_filename: bool = False,
        keep_tex: bool = False,
        png: bool = False,
        svg: bool = False,
        combine_pdf: bool = False,
        recursive: bool = False,
        parallel: bool = False,
        max_workers: int = None,
    ) -> Path:
        """Compile TeX table(s) to PDF, PNG, or SVG."""
        # Check dependencies first
        self.check_dependencies(require_convert=(png or svg))

        try:
            # Validate input
            input_path = Path(input_path)
            if input_path.is_dir():
                pattern = "**/*.tex" if recursive else "*.tex"
                all_tex_files = list(input_path.glob(pattern))
                # Filter out already compiled files (those with _compiled suffix)
                tex_files = [f for f in all_tex_files if not f.stem.endswith(suffix)]
                if not tex_files:
                    search_type = "recursively" if recursive else ""
                    raise FileValidationError(f"No .tex files found {search_type} in {input_path}")
                for tex_file in tex_files:
                    validate_tex_file(tex_file)
            else:
                validate_tex_file(input_path)
                tex_files = [input_path]

            # Setup output directory
            output_dir = validate_output_dir(output_dir)

            # Compile files with error handling
            batch_result = self._compile_batch(
                tex_files,
                output_dir,
                suffix=suffix,
                packages=packages,
                landscape=landscape,
                no_rescale=no_rescale,
                show_filename=show_filename,
                keep_tex=self.mode == CompilerMode.CLI and keep_tex,
                png=png,
                svg=svg,
                combine_pdf=combine_pdf,
                parallel=parallel,
                max_workers=max_workers,
            )

            # Handle results
            if batch_result.all_failed:
                error_report = LaTeXErrorParser.format_batch_result(batch_result)
                raise RuntimeError(error_report)

            # Get successful output paths
            output_paths = [r.output_path for r in batch_result.successes if r.output_path]

            # Handle combination if needed
            if combine_pdf and not png and not svg and len(output_paths) > 1:
                combined_path = self._combine_pdfs(output_paths, output_dir)
                if batch_result.has_failures:
                    # Show warning about partial success
                    logger.warning(LaTeXErrorParser.format_batch_result(batch_result))
                return combined_path

            # Return first successful output or handle partial failures
            if output_paths:
                if batch_result.has_failures:
                    # Log warning about failures but continue
                    logger.warning(LaTeXErrorParser.format_batch_result(batch_result))
                return output_paths[0]

            # Fallback - should not happen if we have validated files
            output_dir.mkdir(parents=True, exist_ok=True)
            extension = ".png" if png else ".pdf"
            return output_dir / f"{input_path.stem}{suffix}{extension}"

        except Exception:
            # Clean up any temporary files on error
            self._cleanup()
            raise

    def _compile_batch(self, tex_files: list[Path], output_dir: Path, **options) -> BatchCompilationResult:
        """Compile multiple files with error recovery."""
        # Extract parallel options
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
                output_path = self._process_single_file(tex_file, output_dir, **options)
                successes.append(CompilationResult(file=tex_file, success=True, output_path=output_path))
                logger.info(f"✅ Compiled: {tex_file.name}")

            except Exception as e:
                failures.append(CompilationResult(file=tex_file, success=False, error=e))
                logger.error(f"❌ Failed: {tex_file.name} - {e}")
                # Continue with next file instead of stopping
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
            """Compile a single file (used by parallel executor)."""
            try:
                output_path = self._process_single_file(tex_file, output_dir, **options)
                logger.info(f"✅ Compiled: {tex_file.name}")
                return CompilationResult(file=tex_file, success=True, output_path=output_path)
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

    def _process_single_file(self, tex_file: Path, output_dir: Path, **options) -> Path:
        """Process a single TeX file."""
        # Read and validate content
        with open(tex_file) as f:
            content = f.read()

        is_valid, error = is_valid_tabular_content(content)
        if not is_valid:
            raise ValueError(f"Invalid tabular content in {tex_file}: {error}")

        # Additional syntax validation
        syntax_issues = validate_tex_content_syntax(content)
        if syntax_issues:
            issues_str = "\n  ".join(syntax_issues)
            raise ValueError(f"Syntax issues in {tex_file}:\n  {issues_str}")

        # Prepare LaTeX content
        full_tex = self._prepare_latex_content(content, tex_file, **options)

        # Compile
        return self._compile_tex_file(tex_file, full_tex, output_dir, **options)

    def _prepare_latex_content(self, content: str, tex_file: Path, **options) -> str:
        """
        Prepare LaTeX content with appropriate packages and formatting.

        Args:
            content: Raw LaTeX content
            tex_file: Path to the input file
            **options: Compilation options

        Returns:
            Formatted LaTeX document ready for compilation
        """
        # Detect and collect packages
        detected_packages = detect_packages(content)
        user_packages = [f"\\usepackage{{{pkg}}}" for pkg in options.get("packages", "").split(",") if pkg]
        all_packages = "\n".join(user_packages) + "\n" + "\n".join(detected_packages)

        # Add option-specific packages
        if not options.get("no_rescale"):
            all_packages += "\n\\usepackage{graphicx}"
            content = r"\resizebox{\linewidth}{!}{" + content + "}"

        # Add underscore package if filename contains underscores and show_filename is enabled
        underscore_package = ""
        if options.get("show_filename") and "_" in tex_file.name:
            underscore_package = "\\usepackage{underscore}  % Handle underscores in filenames"

        # Prepare header and pagestyle
        header = ""
        if options.get("show_filename"):
            header = r"\texttt{" + clean_filename_for_display(tex_file.name) + r"}"
        pagestyle = "plain" if options.get("combine_pdf") else "empty"

        # Handle geometry package options
        geometry_options = ["margin=1cm"]
        if options.get("landscape"):
            geometry_options.append("landscape")
        geometry_package = f"\\usepackage[{','.join(geometry_options)}]{{geometry}}"

        # Format final document
        return TexTemplates.SINGLE_TABLE.format(
            packages=all_packages,
            underscore=underscore_package,
            geometry=geometry_package,
            header=header,
            content=content,
            pagestyle=pagestyle,
        )

    def _cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and self.mode == CompilerMode.WEB:
            clean_up([self.temp_dir])
            self.temp_dir = None

    def _compile_tex_file(self, tex_file: Path, full_tex: str, output_dir: Path, **options) -> Path:
        """
        Compile TeX file and handle output.

        Args:
            tex_file: Original TeX file path
            full_tex: Prepared LaTeX content
            output_dir: Output directory
            **options: Compilation options

        Returns:
            Path to compiled output file
        """
        suffix = options.get("suffix", "_compiled")
        compiled_tex_name = tex_file.stem + suffix + ".tex"
        compiled_tex_path = output_dir / compiled_tex_name

        try:
            # Write TeX file
            with open(compiled_tex_path, "w") as f:
                f.write(full_tex)

            # Run pdflatex
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(compiled_tex_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                # Parse LaTeX log for better error messages
                log_path = output_dir / (tex_file.stem + suffix + ".log")
                if log_path.exists():
                    log_content = log_path.read_text()
                    errors = LaTeXErrorParser.parse_latex_log(log_content, tex_file)
                    if errors:
                        error_report = LaTeXErrorParser.format_error_report(errors)
                        raise RuntimeError(f"LaTeX compilation failed:\n{error_report}")

                # Fallback to basic error message
                stderr_msg = result.stderr.strip() if result.stderr.strip() else "Unknown compilation error"
                raise RuntimeError(f"LaTeX compilation failed: {stderr_msg}")

            pdf_path = output_dir / (tex_file.stem + suffix + ".pdf")
            if not pdf_path.exists():
                raise RuntimeError("PDF file not generated despite successful compilation")

            # Convert to PNG if requested
            if options.get("png"):
                png_path = convert_pdf_to_cropped_png(pdf_path, output_dir, suffix)
                if not png_path:
                    raise RuntimeError("PNG conversion failed")
                clean_up([pdf_path])
                return png_path

            # Convert to SVG if requested
            if options.get("svg"):
                svg_path = convert_pdf_to_svg(pdf_path, output_dir, suffix)
                if not svg_path:
                    raise RuntimeError("SVG conversion failed")
                clean_up([pdf_path])
                return svg_path

            return pdf_path

        finally:
            # Clean up intermediate files
            if not options.get("keep_tex") or self.mode == CompilerMode.WEB:
                clean_up(
                    [
                        compiled_tex_path,
                        output_dir / (tex_file.stem + suffix + ".aux"),
                        output_dir / (tex_file.stem + suffix + ".log"),
                    ]
                )

    def _create_combined_pdf(self, pdf_files: list[Path], output_dir: Path) -> Path | None:
        """
        Create a combined PDF with table of contents.

        Args:
            pdf_files: List of PDF files to combine
            output_dir: Output directory

        Returns:
            Path to combined PDF if successful
        """
        if not pdf_files:
            return None

        try:
            # Create include commands for each PDF
            include_commands = []
            for i, pdf_file in enumerate(pdf_files, start=1):
                display_name = clean_filename_for_display(pdf_file.stem)
                include_commands.extend(create_include_command(pdf_file, display_name, i + 1))

            # Create combined document
            combined_tex = TexTemplates.COMBINED_DOCUMENT.format(include_commands="\n".join(include_commands))

            # Write and compile
            combined_tex_path = output_dir / "tex_tables_combined.tex"
            with open(combined_tex_path, "w") as f:
                f.write(combined_tex)

            # Compile twice for table of contents
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(combined_tex_path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    # Parse LaTeX log for better error messages
                    log_path = output_dir / "tex_tables_combined.log"
                    if log_path.exists():
                        log_content = log_path.read_text()
                        errors = LaTeXErrorParser.parse_latex_log(log_content, combined_tex_path)
                        if errors:
                            error_report = LaTeXErrorParser.format_error_report(errors)
                            raise RuntimeError(f"Combined PDF compilation failed:\n{error_report}")

                    # Fallback to basic error message
                    stderr_msg = result.stderr.strip() if result.stderr.strip() else "Unknown compilation error"
                    raise RuntimeError(f"Combined PDF compilation failed: {stderr_msg}")

            combined_pdf_path = output_dir / "tex_tables_combined.pdf"
            if not combined_pdf_path.exists():
                raise RuntimeError("Combined PDF not generated")

            return combined_pdf_path

        finally:
            # Clean up temporary files (but only if not in CLI mode with keep_tex)
            if self.mode != CompilerMode.CLI:  # Only clean up in web mode
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
        """
        Combine multiple PDFs into a single file with table of contents.

        Args:
            pdf_files: List of PDFs to combine
            output_dir: Output directory

        Returns:
            Path to combined PDF
        """
        if not pdf_files:
            return None

        # Sort PDFs alphabetically
        pdf_files = sorted(pdf_files, key=lambda x: x.stem)

        # Create combined PDF
        combined_pdf = self._create_combined_pdf(pdf_files, output_dir)

        # Clean up individual PDFs if in web mode
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
