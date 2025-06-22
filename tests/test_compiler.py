
# tests/test_compiler.py

import pytest
from pathlib import Path
from tex_compiler.core import TexCompiler


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def sample_tex_file(temp_dir):
    content = r"""
    \begin{tabular}{lcr}
    \toprule
    Header 1 & Header 2 & Header 3 \\
    \midrule
    1 & 2 & 3 \\
    4 & 5 & 6 \\
    \bottomrule
    \end{tabular}
    """
    tex_file = temp_dir / "test_table.tex"
    tex_file.write_text(content)
    return tex_file


def test_basic_compilation(temp_dir, sample_tex_file):
    compiler = TexCompiler()
    output = compiler.compile_tex(
        input_path=sample_tex_file,
        output_dir=temp_dir
    )
    assert output.exists()
    assert (temp_dir / "test_table_compiled.pdf").exists()


def test_png_output(temp_dir, sample_tex_file):
    compiler = TexCompiler()
    output = compiler.compile_tex(
        input_path=sample_tex_file,
        output_dir=temp_dir,
        png=True
    )
    assert output.exists()
    assert (temp_dir / "test_table_compiled.png").exists()


def test_invalid_file():
    compiler = TexCompiler()
    with pytest.raises(FileValidationError):
        compiler.compile_tex(
            input_path="nonexistent.tex",
            output_dir="."
        )
