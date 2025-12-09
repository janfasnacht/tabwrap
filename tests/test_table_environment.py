"""
Integration tests for compiling full table environments.
"""

from pathlib import Path

import pytest

from tabwrap.core import CompilerMode, TabWrap
from tabwrap.latex import check_latex_dependencies, is_valid_tabular_content

# Skip tests if LaTeX is not installed
pytestmark = pytest.mark.skipif(not check_latex_dependencies()["pdflatex"], reason="pdflatex not available")


class TestTableEnvironmentValidation:
    """Test validation of table environments."""

    def test_valid_table_with_tabular(self):
        """Test that table with tabular inside is valid."""
        content = r"""
\begin{table}[h]
\centering
\caption{Test Table}
\begin{tabular}{lcc}
\toprule
A & B & C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
\end{table}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Should be valid but got error: {error}"
        assert error == ""

    def test_valid_table_with_threeparttable(self):
        """Test that table with threeparttable inside is valid."""
        content = r"""
\begin{table}[htbp]
\centering
\caption{Test Table}
\begin{threeparttable}
\begin{tabular}{lc}
\toprule
Variable\tnote{a} & Value \\
\midrule
X & 1.23 \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\item[a] Note text
\end{tablenotes}
\end{threeparttable}
\end{table}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Should be valid but got error: {error}"

    def test_invalid_table_with_longtable(self):
        """Test that table with longtable is invalid (longtable can't be in floats)."""
        content = r"""
\begin{table}[h]
\centering
\caption{Test Table}
\begin{longtable}{lcc}
\toprule
A & B & C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{longtable}
\end{table}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid, "Should be invalid (longtable in table)"
        assert "longtable cannot be used inside table" in error

    def test_invalid_empty_table(self):
        """Test that table without inner environment is invalid."""
        content = r"""
\begin{table}[h]
\centering
\caption{Empty Table}
\end{table}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "must contain a table environment" in error

    def test_invalid_mismatched_table_tags(self):
        """Test that mismatched table tags are caught."""
        content = r"""
\begin{table}[h]
\centering
\begin{tabular}{lcc}
A & B & C \\
\end{tabular}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "Mismatched table environment" in error


class TestTableEnvironmentCompilation:
    """Test actual compilation of table environments."""

    def test_compile_simple_table(self, tmp_path):
        """Test compiling a simple table environment."""
        tex_file = tmp_path / "test_table_simple.tex"
        tex_file.write_text(
            r"""
\begin{table}[h]
\centering
\caption{Test Table}
\label{tab:test}
\begin{tabular}{lcc}
\toprule
Variable & Value 1 & Value 2 \\
\midrule
A & 1.23 & 4.56 \\
B & 7.89 & 0.12 \\
\bottomrule
\end{tabular}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"
        assert output.stat().st_size > 0

    def test_compile_table_with_threeparttable(self, tmp_path):
        """Test compiling table with threeparttable inside."""
        tex_file = tmp_path / "test_table_tpt.tex"
        tex_file.write_text(
            r"""
\begin{table}[htbp]
\centering
\caption{Regression Results}
\label{tab:reg}
\begin{threeparttable}
\begin{tabular}{lcc}
\toprule
Variable\tnote{a} & Coef & SE \\
\midrule
Treatment & 0.234 & (0.045) \\
Control & -0.123 & (0.038) \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\item[a] Standard errors in parentheses
\end{tablenotes}
\end{threeparttable}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_compile_table_no_rescale(self, tmp_path):
        """Test that no_rescale option works with table environment."""
        tex_file = tmp_path / "test_table_no_rescale.tex"
        tex_file.write_text(
            r"""
\begin{table}[h]
\centering
\caption{Test}
\begin{tabular}{lcc}
\toprule
A & B & C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out", no_rescale=True)

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_compile_table_to_png(self, tmp_path):
        """Test compiling table to PNG."""
        deps = check_latex_dependencies()
        if not deps.get("convert"):
            pytest.skip("ImageMagick not available")

        tex_file = tmp_path / "test_table_png.tex"
        tex_file.write_text(
            r"""
\begin{table}[h]
\centering
\caption{Test Table}
\begin{tabular}{lc}
\toprule
Item & Value \\
\midrule
A & 1 \\
\bottomrule
\end{tabular}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out", png=True)

        assert output.exists()
        assert output.suffix == ".png"

    def test_compile_from_fixture_files(self, tmp_path):
        """Test compiling the actual fixture files."""
        test_data_dir = Path(__file__).parent / "data"

        fixture_files = [
            "test_table_simple.tex",
            "test_table_threeparttable.tex",
        ]

        compiler = TabWrap(mode=CompilerMode.CLI)

        for fixture_file in fixture_files:
            fixture_path = test_data_dir / fixture_file
            if fixture_path.exists():
                output = compiler.compile_tex(fixture_path, tmp_path, suffix="_compiled")
                assert output.exists(), f"Failed to compile {fixture_file}"
                assert output.suffix == ".pdf"
                assert output.stat().st_size > 0


class TestBackwardCompatibility:
    """Test that existing tabular-only content still works."""

    def test_standalone_tabular_still_works(self, tmp_path):
        """Test that standalone tabular (no table wrapper) still compiles."""
        tex_file = tmp_path / "test_standalone.tex"
        tex_file.write_text(
            r"""
\begin{tabular}{lcc}
\toprule
A & B & C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_standalone_threeparttable_still_works(self, tmp_path):
        """Test that standalone threeparttable (no table wrapper) still compiles."""
        tex_file = tmp_path / "test_standalone_tpt.tex"
        tex_file.write_text(
            r"""
\begin{threeparttable}
\caption{Test}
\begin{tabular}{lc}
\toprule
Var\tnote{a} & Val \\
\midrule
X & 1 \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\item[a] Note
\end{tablenotes}
\end{threeparttable}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_standalone_longtable_still_works(self, tmp_path):
        """Test that standalone longtable still compiles."""
        tex_file = tmp_path / "test_standalone_long.tex"
        tex_file.write_text(
            r"""
\begin{longtable}{lcc}
\caption{Test Longtable} \\
\toprule
A & B & C \\
\midrule
\endfirsthead
1 & 2 & 3 \\
\bottomrule
\end{longtable}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_table_with_multiple_placement_options(self, tmp_path):
        """Test table with complex placement specifier."""
        tex_file = tmp_path / "test_placement.tex"
        tex_file.write_text(
            r"""
\begin{table}[!htbp]
\centering
\caption{Complex Placement}
\begin{tabular}{lc}
\toprule
A & B \\
\midrule
1 & 2 \\
\bottomrule
\end{tabular}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()

    def test_table_without_centering(self, tmp_path):
        """Test table without \\centering directive."""
        tex_file = tmp_path / "test_no_center.tex"
        tex_file.write_text(
            r"""
\begin{table}[h]
\caption{No Centering}
\begin{tabular}{lc}
\toprule
A & B \\
\midrule
1 & 2 \\
\bottomrule
\end{tabular}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()

    def test_table_caption_after_tabular(self, tmp_path):
        """Test table with caption after tabular (valid LaTeX pattern)."""
        tex_file = tmp_path / "test_caption_after.tex"
        tex_file.write_text(
            r"""
\begin{table}[h]
\centering
\begin{tabular}{lc}
\toprule
A & B \\
\midrule
1 & 2 \\
\bottomrule
\end{tabular}
\caption{Caption After Table}
\label{tab:after}
\end{table}
        """
        )

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
