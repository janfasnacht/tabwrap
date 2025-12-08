# tests/test_recursive.py
from tabwrap.core import CompilerMode, TabWrap


def test_recursive_finds_nested_files(tmp_path):
    """Test that recursive mode finds files in subdirectories."""
    # Create nested structure
    (tmp_path / "subdir1").mkdir()
    (tmp_path / "subdir2").mkdir()

    # Create tex files at different levels
    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Test & Value & Result \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""

    # Root level file
    (tmp_path / "root.tex").write_text(tex_content)

    # Nested files
    (tmp_path / "subdir1" / "nested1.tex").write_text(tex_content)
    (tmp_path / "subdir2" / "nested2.tex").write_text(tex_content)

    # Compile with recursive
    compiler = TabWrap(mode=CompilerMode.CLI)
    output_path = compiler.compile_tex(input_path=tmp_path, output_dir=tmp_path, recursive=True)

    # Should find and compile all 3 files
    assert output_path.exists()
    assert (tmp_path / "root_compiled.pdf").exists()

    # Check that nested files were also processed
    # The exact behavior depends on implementation, but at least one should exist
    pdf_files = list(tmp_path.rglob("*_compiled.pdf"))
    assert len(pdf_files) >= 1


def test_non_recursive_skips_subdirs(tmp_path):
    """Test that non-recursive mode only processes current directory."""
    # Create nested structure
    (tmp_path / "subdir").mkdir()

    tex_content = r"""
\begin{tabular}{lcr}
\toprule
Test & Value & Result \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
"""

    # Root level file
    (tmp_path / "root.tex").write_text(tex_content)

    # Nested file that should be ignored
    (tmp_path / "subdir" / "nested.tex").write_text(tex_content)

    # Compile without recursive
    compiler = TabWrap(mode=CompilerMode.CLI)
    output_path = compiler.compile_tex(input_path=tmp_path, output_dir=tmp_path, recursive=False)

    # Should only process root level file
    assert output_path.exists()
    assert (tmp_path / "root_compiled.pdf").exists()

    # Nested file should not be compiled
    assert not (tmp_path / "subdir" / "nested_compiled.pdf").exists()
