# tests/test_enhanced_error_handling.py
"""Tests for enhanced error handling with multi-file support."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from tabwrap.cli import main
from tabwrap.core import TabWrap
from tabwrap.latex import (
    BatchCompilationResult,
    CompilationResult,
    LaTeXErrorParser,
    check_latex_dependencies,
    format_dependency_report,
)


@pytest.fixture
def runner():
    return CliRunner()


def test_dependency_checking():
    """Test LaTeX dependency checking."""
    deps = check_latex_dependencies()

    # Should return a dict with at least pdflatex and convert
    assert isinstance(deps, dict)
    assert "pdflatex" in deps
    assert "convert" in deps

    # Values should be booleans
    assert isinstance(deps["pdflatex"], bool)
    assert isinstance(deps["convert"], bool)


def test_dependency_report_formatting():
    """Test dependency report formatting."""
    # Test with all available
    deps_good = {"pdflatex": True, "convert": True}
    report = format_dependency_report(deps_good)
    assert "✅ All dependencies satisfied!" in report
    assert "✅ pdflatex" in report
    assert "✅ convert" in report

    # Test with missing dependencies
    deps_bad = {"pdflatex": False, "convert": False}
    report = format_dependency_report(deps_bad)
    assert "⚠️  2 dependencies missing" in report
    assert "❌ pdflatex" in report
    assert "❌ convert" in report
    assert "Install a LaTeX distribution" in report


def test_compiler_dependency_check():
    """Test compiler dependency checking."""
    compiler = TabWrap()

    # Mock missing pdflatex
    with patch("tabwrap.core.check_latex_dependencies") as mock_check:
        mock_check.return_value = {"pdflatex": False, "convert": True}

        with pytest.raises(RuntimeError) as excinfo:
            compiler.check_dependencies()

        assert "pdflatex is required but not found" in str(excinfo.value)
        assert "LaTeX Dependencies:" in str(excinfo.value)


def test_compiler_dependency_check_png():
    """Test compiler dependency checking for PNG output."""
    compiler = TabWrap()

    # Mock missing convert for PNG
    with patch("tabwrap.core.check_latex_dependencies") as mock_check:
        mock_check.return_value = {"pdflatex": True, "convert": False}

        # Should pass without PNG requirement
        compiler.check_dependencies(require_convert=False)

        # Should fail with PNG requirement
        with pytest.raises(RuntimeError) as excinfo:
            compiler.check_dependencies(require_convert=True)

        assert "ImageMagick 'convert' is required for PNG output" in str(excinfo.value)


def test_compilation_result():
    """Test CompilationResult dataclass."""
    success_result = CompilationResult(file=Path("test.tex"), success=True, output_path=Path("test.pdf"))

    assert success_result.success
    assert success_result.output_path == Path("test.pdf")
    assert success_result.error is None

    failure_result = CompilationResult(file=Path("bad.tex"), success=False, error=RuntimeError("Test error"))

    assert not failure_result.success
    assert failure_result.output_path is None
    assert isinstance(failure_result.error, RuntimeError)


def test_batch_compilation_result():
    """Test BatchCompilationResult aggregation."""
    successes = [
        CompilationResult(Path("good1.tex"), True, Path("good1.pdf")),
        CompilationResult(Path("good2.tex"), True, Path("good2.pdf")),
    ]

    failures = [
        CompilationResult(Path("bad1.tex"), False, error=RuntimeError("Error 1")),
        CompilationResult(Path("bad2.tex"), False, error=RuntimeError("Error 2")),
    ]

    batch_result = BatchCompilationResult(successes=successes, failures=failures)

    assert batch_result.success_count == 2
    assert batch_result.failure_count == 2
    assert batch_result.total_count == 4
    assert batch_result.has_failures
    assert not batch_result.all_failed

    # Test all successful
    all_success = BatchCompilationResult(successes=successes, failures=[])
    assert not all_success.has_failures
    assert not all_success.all_failed

    # Test all failed
    all_failed = BatchCompilationResult(successes=[], failures=failures)
    assert all_failed.has_failures
    assert all_failed.all_failed


def test_batch_result_formatting():
    """Test batch result formatting."""
    # All successful
    successes = [CompilationResult(Path("good.tex"), True, Path("good.pdf"))]
    all_success = BatchCompilationResult(successes=successes, failures=[])
    report = LaTeXErrorParser.format_batch_result(all_success)
    assert "✅ All 1 files compiled successfully!" in report

    # Partial failures
    failures = [CompilationResult(Path("bad.tex"), False, error=RuntimeError("Test error"))]
    partial = BatchCompilationResult(successes=successes, failures=failures)
    report = LaTeXErrorParser.format_batch_result(partial)
    assert "⚠️  1 of 2 files failed to compile:" in report
    assert "📋 Failed files:" in report
    assert "bad.tex" in report
    assert "✅ Successfully compiled: good.tex" in report

    # All failed
    all_failed = BatchCompilationResult(successes=[], failures=failures)
    report = LaTeXErrorParser.format_batch_result(all_failed)
    assert "❌ All 1 files failed to compile:" in report


def test_multi_file_compilation_with_errors(runner, tmp_path):
    """Test multi-file compilation where some files fail."""
    # Create good file
    good_tex = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    (tmp_path / "good.tex").write_text(good_tex)

    # Create bad file (missing \end{tabular})
    bad_tex = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
"""
    (tmp_path / "bad.tex").write_text(bad_tex)

    # Run compilation - should succeed partially
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path)])

    # Should succeed (partial success) and show warnings
    # The good file should compile, bad file should fail
    assert result.exit_code == 0  # Partial success
    assert (tmp_path / "good_compiled.pdf").exists()
    assert not (tmp_path / "bad_compiled.pdf").exists()


def test_all_files_fail_compilation(runner, tmp_path):
    """Test compilation where all files fail."""
    # Create multiple bad files that will definitely fail validation
    for i in range(3):
        bad_tex = f"This is not valid LaTeX content for Bad File {i}"
        (tmp_path / f"bad_{i}.tex").write_text(bad_tex)

    # Run compilation - should fail completely
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path)])

    # Should fail completely (all files invalid)
    assert result.exit_code != 0
    assert "No supported table environment found" in result.output

    # No PDFs should be created
    assert not list(tmp_path.glob("*.pdf"))


def test_dependency_failure_on_missing_pdflatex(runner, tmp_path):
    """Test that missing pdflatex is caught early."""
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex_content)

    # Mock pdflatex as missing in the core module where it's imported
    with patch("tabwrap.core.check_latex_dependencies") as mock_check:
        mock_check.return_value = {"pdflatex": False, "convert": True}

        result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])

        assert result.exit_code != 0
        assert "pdflatex is required but not found" in result.output
        assert "LaTeX Dependencies:" in result.output


def test_png_dependency_check(runner, tmp_path):
    """Test PNG dependency checking."""
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(tex_content)

    # Mock convert as missing for PNG output
    with patch("tabwrap.core.check_latex_dependencies") as mock_check:
        mock_check.return_value = {"pdflatex": True, "convert": False}

        # PDF should work
        result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])
        assert result.exit_code == 0

        # PNG should fail
        result = runner.invoke(
            main,
            [
                str(tex_file),
                "-o",
                str(tmp_path),
                "-p",  # PNG output
            ],
        )
        assert result.exit_code != 0
        assert "ImageMagick 'convert' is required for PNG output" in result.output
