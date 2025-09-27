# tests/test_cli_options.py
"""Tests for individual CLI options and their combinations."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from tabwrap.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_tex(tmp_path):
    """Sample table with underscore in filename for header testing."""
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
4 & 5 & 6 \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "test_under_score.tex"
    tex_file.write_text(tex_content)
    return tex_file


def test_custom_suffix(runner, sample_tex, tmp_path):
    """Test --suffix option with custom suffix."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--suffix', '_custom'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_custom.pdf").exists()
    assert not (tmp_path / "test_under_score_compiled.pdf").exists()


def test_custom_packages(runner, sample_tex, tmp_path):
    """Test --packages option with custom LaTeX packages."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--packages', 'amsmath,amssymb',
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    
    # Check that custom packages were included
    tex_file = tmp_path / "test_under_score_compiled.tex"
    assert tex_file.exists()
    tex_content = tex_file.read_text()
    assert r"\usepackage{amsmath}" in tex_content
    assert r"\usepackage{amssymb}" in tex_content


def test_no_resize_option(runner, sample_tex, tmp_path):
    """Test --no-resize option disables automatic resizing."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--no-resize',
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    
    # Check that resizebox is NOT present
    tex_file = tmp_path / "test_under_score_compiled.tex"
    assert tex_file.exists()
    tex_content = tex_file.read_text()
    assert r"\resizebox" not in tex_content
    assert r"\usepackage{graphicx}" not in tex_content


def test_header_option(runner, sample_tex, tmp_path):
    """Test --header option includes filename in output."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--header',
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    
    # Check that header and underscore package are included
    tex_file = tmp_path / "test_under_score_compiled.tex"
    assert tex_file.exists()
    tex_content = tex_file.read_text()
    assert r"\texttt{test\_under\_score.tex}" in tex_content
    assert r"\usepackage{underscore}" in tex_content


def test_header_without_underscores(runner, tmp_path):
    """Test --header option with filename containing no underscores."""
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    tex_file = tmp_path / "simple.tex"
    tex_file.write_text(tex_content)
    
    result = runner.invoke(main, [
        str(tex_file),
        '-o', str(tmp_path),
        '--header',
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "simple_compiled.pdf").exists()
    
    # Check that header is included but underscore package is NOT
    compiled_tex = tmp_path / "simple_compiled.tex"
    assert compiled_tex.exists()
    tex_content = compiled_tex.read_text()
    assert r"\texttt{simple.tex}" in tex_content
    assert r"\usepackage{underscore}" not in tex_content


def test_keep_tex_option(runner, sample_tex, tmp_path):
    """Test --keep-tex option preserves intermediate files."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    assert (tmp_path / "test_under_score_compiled.tex").exists()


def test_without_keep_tex(runner, sample_tex, tmp_path):
    """Test that intermediate files are cleaned up by default."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path)
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    assert not (tmp_path / "test_under_score_compiled.tex").exists()


def test_option_combinations(runner, sample_tex, tmp_path):
    """Test combination of multiple options."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '--suffix', '_final',
        '--packages', 'amsmath',
        '--header',
        '--no-resize',
        '--landscape',
        '--keep-tex'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_final.pdf").exists()
    
    # Verify all options took effect
    tex_file = tmp_path / "test_under_score_final.tex"
    assert tex_file.exists()
    tex_content = tex_file.read_text()
    
    # Custom package
    assert r"\usepackage{amsmath}" in tex_content
    # Header with underscore package
    assert r"\texttt{test\_under\_score.tex}" in tex_content
    assert r"\usepackage{underscore}" in tex_content
    # No resize
    assert r"\resizebox" not in tex_content
    # Landscape
    assert r"landscape" in tex_content


def test_combine_single_file(runner, sample_tex, tmp_path):
    """Test --combine flag with single file (should work but not create combined PDF)."""
    result = runner.invoke(main, [
        str(sample_tex),
        '-o', str(tmp_path),
        '-c'
    ])
    assert result.exit_code == 0
    assert (tmp_path / "test_under_score_compiled.pdf").exists()
    # Combined PDF should not be created for single file
    assert not (tmp_path / "tex_tables_combined.pdf").exists()


def test_png_with_combine_error(runner, tmp_path):
    """Test that PNG and combine options are mutually exclusive."""
    # Create multiple tex files
    for i in range(2):
        tex_content = f"""
\\begin{{tabular}}{{lcr}}
\\toprule
Table {i} & Column 2 & Column 3 \\\\
\\midrule
1 & 2 & 3 \\\\
\\bottomrule
\\end{{tabular}}
"""
        (tmp_path / f"table_{i}.tex").write_text(tex_content)
    
    result = runner.invoke(main, [
        str(tmp_path),
        '-o', str(tmp_path),
        '-p',  # PNG
        '-c'   # Combine
    ])
    # Should succeed but not create combined PDF (PNG mode)
    assert result.exit_code == 0
    # Individual PNG files should be created
    assert (tmp_path / "table_0_compiled.png").exists()
    assert (tmp_path / "table_1_compiled.png").exists()
    # No combined PDF in PNG mode
    assert not (tmp_path / "tex_tables_combined.pdf").exists()