# tests/test_cli.py

import pytest
from click.testing import CliRunner

from tabwrap.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_tex(tmp_path):
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
    tex_file = tmp_path / "test_table.tex"
    tex_file.write_text(tex_content)
    return tex_file


def test_basic_compilation(runner, sample_tex, tmp_path):
    result = runner.invoke(main, [str(sample_tex), "-o", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "test_table_compiled.pdf").exists()


def test_png_output(runner, sample_tex, tmp_path):
    result = runner.invoke(main, [str(sample_tex), "-o", str(tmp_path), "-p"])
    assert result.exit_code == 0
    assert (tmp_path / "test_table_compiled.png").exists()


def test_landscape_mode(runner, sample_tex, tmp_path, test_logger):
    result = runner.invoke(main, [str(sample_tex), "-o", str(tmp_path), "--landscape"])
    if result.exit_code != 0:
        test_logger.error(f"Command failed with output: {result.output}")
        test_logger.error(f"Exception: {result.exception}")
    assert result.exit_code == 0
    assert (tmp_path / "test_table_compiled.pdf").exists()


def test_directory_input(runner, tmp_path, test_logger):
    # Create multiple tex files
    for i in range(3):
        tex_content = f"""
\\begin{{tabular}}{{lcr}}
\\toprule
Table {i} & Column 2 & Column 3 \\\\
\\midrule
1 & 2 & 3 \\\\
\\bottomrule
\\end{{tabular}}
"""
        file_path = tmp_path / f"table_{i}.tex"
        file_path.write_text(tex_content)
        test_logger.info(f"Created test file: {file_path}")

    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path), "-c"])
    if result.exit_code != 0:
        test_logger.error(f"Command failed with output: {result.output}")
        test_logger.error(f"Exception: {result.exception}")
    assert result.exit_code == 0
    assert (tmp_path / "tex_tables_combined.pdf").exists()


def test_recursive_directory_input(runner, tmp_path, test_logger):
    # Create directory structure with tex files in subdirectories
    subdir1 = tmp_path / "subdir1"
    subdir2 = tmp_path / "subdir2"
    subdir1.mkdir()
    subdir2.mkdir()

    # Create tex files in root
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Root Table & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    (tmp_path / "root_table.tex").write_text(tex_content)

    # Create tex files in subdirectories
    for i, subdir in enumerate([subdir1, subdir2], 1):
        tex_content = f"""
\\begin{{tabular}}{{lcr}}
\\toprule
Subdir {i} & Column 2 & Column 3 \\\\
\\midrule
{i} & {i + 1} & {i + 2} \\\\
\\bottomrule
\\end{{tabular}}
"""
        (subdir / f"subdir{i}_table.tex").write_text(tex_content)
        test_logger.info(f"Created test file: {subdir / f'subdir{i}_table.tex'}")

    # Test recursive compilation
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path), "-r", "-c"])
    if result.exit_code != 0:
        test_logger.error(f"Command failed with output: {result.output}")
        test_logger.error(f"Exception: {result.exception}")
    assert result.exit_code == 0
    assert (tmp_path / "tex_tables_combined.pdf").exists()


def test_recursive_vs_non_recursive(runner, tmp_path, test_logger):
    # Create directory structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    # Create tex file only in subdirectory
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Nested Table & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""
    (subdir / "nested_table.tex").write_text(tex_content)

    # Test non-recursive - should find no files
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path)])
    assert result.exit_code != 0  # Should fail - no .tex files found

    # Test recursive - should find the nested file
    result = runner.invoke(main, [str(tmp_path), "-o", str(tmp_path), "-r"])
    if result.exit_code != 0:
        test_logger.error(f"Recursive command failed with output: {result.output}")
        test_logger.error(f"Exception: {result.exception}")
    assert result.exit_code == 0
