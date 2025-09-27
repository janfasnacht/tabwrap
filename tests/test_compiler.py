
# tests/test_compiler.py

import pytest
from pathlib import Path
from tabwrap.core import TexCompiler
from tabwrap.latex import FileValidationError


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


def test_recursive_compilation(temp_dir):
    # Create directory structure with tex files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    # Create tex file in subdirectory
    content = r"""
    \begin{tabular}{lcr}
    \toprule
    Nested Table & Column 2 & Column 3 \\
    \midrule
    1 & 2 & 3 \\
    \bottomrule
    \end{tabular}
    """
    tex_file = subdir / "nested_table.tex"
    tex_file.write_text(content)
    
    # Test recursive compilation
    compiler = TexCompiler()
    output = compiler.compile_tex(
        input_path=temp_dir,
        output_dir=temp_dir,
        recursive=True
    )
    assert output.exists()


def test_non_recursive_vs_recursive(temp_dir):
    # Create directory structure
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    # Create tex file only in subdirectory
    content = r"""
    \begin{tabular}{lcr}
    \toprule
    Nested Table & Column 2 & Column 3 \\
    \midrule
    1 & 2 & 3 \\
    \bottomrule
    \end{tabular}
    """
    tex_file = subdir / "nested_table.tex"
    tex_file.write_text(content)
    
    compiler = TexCompiler()
    
    # Non-recursive should fail (no .tex files in root)
    with pytest.raises(FileValidationError, match="No .tex files found"):
        compiler.compile_tex(
            input_path=temp_dir,
            output_dir=temp_dir,
            recursive=False
        )
    
    # Recursive should succeed
    output = compiler.compile_tex(
        input_path=temp_dir,
        output_dir=temp_dir,
        recursive=True
    )
    assert output.exists()
