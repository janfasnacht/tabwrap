# tests/test_parallel.py

import tempfile
from pathlib import Path

import pytest

from tabwrap.core import CompilerMode, TabWrap


@pytest.fixture
def sample_tex_content():
    """Sample TeX content for testing."""
    return r"""
\begin{tabular}{lcr}
\toprule
Header 1 & Header 2 & Header 3 \\
\midrule
1 & 2 & 3 \\
4 & 5 & 6 \\
\bottomrule
\end{tabular}
"""


@pytest.fixture
def test_dataset(sample_tex_content):
    """Create a test dataset with multiple files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create multiple test files
        files = []
        for i in range(5):
            file_path = temp_path / f"test_table_{i:03d}.tex"
            file_path.write_text(sample_tex_content)
            files.append(file_path)

        yield temp_path, files


def test_parallel_vs_sequential(test_dataset):
    """Test that parallel and sequential processing produce the same results."""
    temp_dir, test_files = test_dataset
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Test sequential processing
    with TabWrap(mode=CompilerMode.CLI) as compiler:
        sequential_result = compiler.compile_tex(input_path=temp_dir, output_dir=output_dir, parallel=False)

    # Count sequential outputs
    sequential_outputs = list(output_dir.glob("*.pdf"))

    # Clean output directory
    for f in output_dir.glob("*"):
        f.unlink()

    # Test parallel processing
    with TabWrap(mode=CompilerMode.CLI) as compiler:
        parallel_result = compiler.compile_tex(input_path=temp_dir, output_dir=output_dir, parallel=True)

    # Count parallel outputs
    parallel_outputs = list(output_dir.glob("*.pdf"))

    # Both should produce the same number of files
    assert len(sequential_outputs) == len(parallel_outputs)
    assert len(sequential_outputs) == 5  # Should compile all 5 files
    assert sequential_result.exists()
    assert parallel_result.exists()


def test_parallel_with_single_file(sample_tex_content):
    """Test that parallel processing works correctly with a single file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_dir = temp_path / "output"
        output_dir.mkdir()

        # Create single test file
        test_file = temp_path / "single_test.tex"
        test_file.write_text(sample_tex_content)

        # Test parallel processing with single file
        with TabWrap(mode=CompilerMode.CLI) as compiler:
            result = compiler.compile_tex(input_path=test_file, output_dir=output_dir, parallel=True)

        assert result.exists()
        assert result.name == "single_test_compiled.pdf"


def test_parallel_with_max_workers(test_dataset):
    """Test parallel processing with custom max_workers setting."""
    temp_dir, test_files = test_dataset
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    with TabWrap(mode=CompilerMode.CLI) as compiler:
        result = compiler.compile_tex(
            input_path=temp_dir,
            output_dir=output_dir,
            parallel=True,
            max_workers=2,  # Limit to 2 workers
        )

    outputs = list(output_dir.glob("*.pdf"))
    assert len(outputs) == 5  # Should still compile all files
    assert result.exists()


def test_parallel_error_recovery(sample_tex_content):
    """Test that parallel processing handles errors gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_dir = temp_path / "output"
        output_dir.mkdir()

        # Create mix of valid and invalid files
        good_file = temp_path / "good_table.tex"
        good_file.write_text(sample_tex_content)

        bad_file = temp_path / "bad_table.tex"
        bad_file.write_text("This is not valid LaTeX \\invalid{}")

        # Test parallel processing with mixed files
        with TabWrap(mode=CompilerMode.CLI) as compiler:
            try:
                result = compiler.compile_tex(input_path=temp_dir, output_dir=output_dir, parallel=True)
                # Should succeed and return path to good file
                assert result.exists()
            except RuntimeError as e:
                # Should provide information about failures
                assert "failed" in str(e).lower()

        # At least one file should have been compiled successfully
        outputs = list(output_dir.glob("*.pdf"))
        assert len(outputs) >= 1


def test_parallel_png_output(test_dataset):
    """Test parallel processing with PNG output."""
    temp_dir, test_files = test_dataset
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    with TabWrap(mode=CompilerMode.CLI) as compiler:
        result = compiler.compile_tex(input_path=temp_dir, output_dir=output_dir, parallel=True, png=True)

    # Should produce PNG files
    png_outputs = list(output_dir.glob("*.png"))
    assert len(png_outputs) == 5
    assert result.exists()
    assert result.suffix == ".png"


def test_parallel_disabled_by_default():
    """Test that parallel processing is disabled by default."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_dir = temp_path / "output"
        output_dir.mkdir()

        # Create test file
        test_file = temp_path / "test.tex"
        test_file.write_text(r"""
\begin{tabular}{cc}
A & B \\
\end{tabular}
""")

        with TabWrap(mode=CompilerMode.CLI) as compiler:
            result = compiler.compile_tex(
                input_path=test_file,
                output_dir=output_dir,
                # parallel=False is the default
            )

        assert result.exists()
