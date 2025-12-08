# tests/conftest.py

import pytest
from click.testing import CliRunner

from tabwrap.config import setup_logging


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def test_logger():
    return setup_logging(level="DEBUG", module_name="tabwrap.test")


@pytest.fixture
def sample_tex(tmp_path):
    """Fixture providing a sample LaTeX table file."""
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


@pytest.fixture
def output_dir(tmp_path):
    """Fixture providing a clean output directory."""
    output = tmp_path / "output"
    output.mkdir()
    return output
