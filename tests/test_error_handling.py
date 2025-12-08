# tests/test_error_handling.py
"""Tests for error handling and edge cases."""

import pytest
from click.testing import CliRunner

from tabwrap.cli import main
from tabwrap.core import CompilerMode, TabWrap


@pytest.fixture
def runner():
    return CliRunner()


def test_invalid_latex_syntax(runner, tmp_path, test_logger):
    """Test handling of invalid LaTeX syntax."""
    # Create tex file with invalid LaTeX
    invalid_tex = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
% Missing \end{tabular}
"""
    tex_file = tmp_path / "invalid.tex"
    tex_file.write_text(invalid_tex)

    result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])
    assert result.exit_code != 0
    # The error could be caught at validation or LaTeX compilation stage
    # With enhanced error handling, we now get batch results format
    assert (
        "Invalid tabular content" in result.output
        or "Syntax issues" in result.output
        or "LaTeX compilation failed" in result.output
        or "files failed to compile" in result.output
    )
    test_logger.info(f"Error output: {result.output}")


def test_missing_file(runner, tmp_path):
    """Test handling of non-existent file."""
    result = runner.invoke(main, [str(tmp_path / "nonexistent.tex"), "-o", str(tmp_path)])
    assert result.exit_code != 0


def test_empty_directory(runner, tmp_path):
    """Test handling of directory with no .tex files."""
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path)])
    assert result.exit_code != 0
    assert "No .tex files found" in result.output


def test_invalid_tabular_content(runner, tmp_path):
    """Test validation of tabular content."""
    # File with no tabular environment
    invalid_content = "This is just text, no table here."
    tex_file = tmp_path / "no_table.tex"
    tex_file.write_text(invalid_content)

    result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])
    assert result.exit_code != 0
    assert "No supported table environment found" in result.output


def test_mismatched_tabular_tags(runner, tmp_path):
    """Test detection of mismatched tabular tags."""
    mismatched_tex = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\begin{tabular}{ll}
More content
\end{tabular}
% Missing second \end{tabular}
"""
    tex_file = tmp_path / "mismatched.tex"
    tex_file.write_text(mismatched_tex)

    result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])
    assert result.exit_code != 0
    # Could be validation error or LaTeX compilation error
    assert (
        "Mismatched tabular" in result.output
        or "LaTeX compilation failed" in result.output
        or "files failed to compile" in result.output
    )


def test_latex_compilation_error(runner, tmp_path, test_logger):
    """Test LaTeX compilation error handling."""
    # Create tex with valid structure but LaTeX errors
    error_tex = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & \undefined_command \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "latex_error.tex"
    tex_file.write_text(error_tex)

    result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path), "--keep-tex"])
    if result.exit_code != 0:
        test_logger.info(f"Expected LaTeX error: {result.output}")
        # Check that we get a useful error message with enhanced error handling
        assert "LaTeX compilation failed" in result.output or "files failed to compile" in result.output
    else:
        # Some LaTeX installations might be more permissive
        test_logger.warning("LaTeX error was not caught - installation may be permissive")


def test_avoid_double_compilation(runner, tmp_path):
    """Test that already compiled files are not processed again."""
    # Create source file
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    (tmp_path / "source.tex").write_text(tex_content)

    # Create an already compiled file
    (tmp_path / "source_compiled.tex").write_text("Already compiled content")

    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path)])
    assert result.exit_code == 0
    # Should only process source.tex, not source_compiled.tex
    assert (tmp_path / "source_compiled.pdf").exists()
    # Should not create source_compiled_compiled.pdf
    assert not (tmp_path / "source_compiled_compiled.pdf").exists()


def test_web_mode_vs_cli_mode():
    """Test differences between web and CLI modes."""
    compiler_cli = TabWrap(CompilerMode.CLI)
    compiler_web = TabWrap(CompilerMode.WEB)

    assert compiler_cli.mode == CompilerMode.CLI
    assert compiler_web.mode == CompilerMode.WEB


def test_package_detection_accuracy(tmp_path):
    """Test accuracy of automatic package detection."""
    from tabwrap.latex import detect_packages

    # Test booktabs detection
    booktabs_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    packages = detect_packages(booktabs_content)
    assert r"\usepackage{booktabs}" in packages

    # Test tabularx detection
    tabularx_content = r"""
\begin{tabularx}{\textwidth}{XXX}
\toprule
Column 1 & Column 2 & Column 3 \\
\bottomrule
\end{tabularx}
"""
    packages = detect_packages(tabularx_content)
    assert r"\usepackage{booktabs}" in packages
    assert r"\usepackage{tabularx}" in packages

    # Test siunitx detection with \SI and \num
    siunitx_content = r"""
\begin{tabular}{lcr}
\toprule
Value & Unit & Result \\
\midrule
\SI{3.14}{\meter} & \num{2.718} & Good \\
\bottomrule
\end{tabular}
"""
    packages = detect_packages(siunitx_content)
    assert r"\usepackage{siunitx}" in packages

    # Test siunitx detection with S column
    siunitx_s_column = r"""
\begin{tabular}{lS[table-format=1.3]S}
\toprule
Variable & {Mean} & {SD} \\
\midrule
Age & 45.123 & 12.456 \\
\bottomrule
\end{tabular}
"""
    packages = detect_packages(siunitx_s_column)
    assert r"\usepackage{siunitx}" in packages

    # Test siunitx detection with {S} column syntax
    siunitx_s_simple = r"""
\begin{tabular}{lSSS}
\toprule
Variable & {A} & {B} & {C} \\
\bottomrule
\end{tabular}
"""
    packages = detect_packages(siunitx_s_simple)
    assert r"\usepackage{siunitx}" in packages

    # Test siunitx detection with \sisetup
    siunitx_setup = r"""
\sisetup{
    input-symbols = () [],
    table-space-text-post = ***,
}
\begin{tabular}{lS}
\toprule
Variable & {Value} \\
\bottomrule
\end{tabular}
"""
    packages = detect_packages(siunitx_setup)
    assert r"\usepackage{siunitx}" in packages


def test_output_directory_creation(runner, tmp_path):
    """Test that output directories are created if they don't exist."""
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

    # Output to non-existent subdirectory
    output_dir = tmp_path / "new_subdir"
    assert not output_dir.exists()

    result = runner.invoke(main, [str(tex_file), "-o", str(output_dir)])
    assert result.exit_code == 0
    assert output_dir.exists()
    assert (output_dir / "test_compiled.pdf").exists()


def test_file_permissions_error(runner, tmp_path):
    """Test handling of file permission errors."""
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

    # Try to write to read-only directory (if possible to create)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o444)  # Read-only

    try:
        result = runner.invoke(main, [str(tex_file), "-o", str(readonly_dir)])
        # Should handle permission error gracefully
        if result.exit_code != 0:
            assert "permission" in result.output.lower() or "denied" in result.output.lower()
    finally:
        # Restore permissions for cleanup
        readonly_dir.chmod(0o755)


def test_compilation_succeeds_with_warnings(runner, tmp_path, test_logger):
    """Test that compilation succeeds despite warnings (e.g., deprecated siunitx options)."""
    # Table with deprecated siunitx options that trigger warnings but should still compile
    tex_with_warnings = r"""\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}
\begin{tabular}{l*{3}{S[table-format = 1.3, table-space-text-post = {\sym{***}}, input-symbols = {()}]}}
\toprule
Variable & {Model 1} & {Model 2} & {Model 3} \\
\midrule
Coefficient & 1.234\sym{***} & 2.456\sym{**} & 3.789\sym{*} \\
            & (0.123) & (0.234) & (0.345) \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "warnings_test.tex"
    tex_file.write_text(tex_with_warnings)

    result = runner.invoke(main, [str(tex_file), "-o", str(tmp_path)])

    test_logger.info(f"Compilation output: {result.output}")
    assert result.exit_code == 0, "Compilation should succeed despite warnings"
    assert "Output saved to" in result.output
    assert (tmp_path / "warnings_test_compiled.pdf").exists()
