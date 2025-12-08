# tests/test_longtable_integration.py
"""
Integration tests for compiling longtable and threeparttable environments.
"""

from pathlib import Path

import pytest

from tabwrap.core import CompilerMode, TabWrap
from tabwrap.latex import check_latex_dependencies

# Skip tests if LaTeX is not installed
pytestmark = pytest.mark.skipif(not check_latex_dependencies()["pdflatex"], reason="pdflatex not available")


class TestLongtableCompilation:
    """Test actual compilation of longtable documents."""

    def test_compile_simple_longtable(self, tmp_path):
        """Test compiling a simple longtable."""
        tex_file = tmp_path / "test_longtable.tex"
        tex_file.write_text(r"""
\begin{longtable}{lrc}
\toprule
Item & Value & Status \\
\midrule
First & 1.23 & Active \\
Second & 4.56 & Inactive \\
Third & 7.89 & Active \\
\bottomrule
\end{longtable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"
        assert output.stat().st_size > 0

    def test_compile_longtable_with_headers(self, tmp_path):
        """Test compiling longtable with repeated headers."""
        tex_file = tmp_path / "test_longtable_headers.tex"
        tex_file.write_text(r"""
\begin{longtable}{lcc}
\caption{Table with Headers} \\
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
\endfirsthead

\multicolumn{3}{c}{Continued from previous page} \\
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
\endhead

\bottomrule
\endlastfoot

Row 1 & Data A & 100 \\
Row 2 & Data B & 200 \\
Row 3 & Data C & 300 \\
\end{longtable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_compile_longtable_to_png(self, tmp_path):
        """Test compiling longtable to PNG."""
        # Check if ImageMagick is available
        deps = check_latex_dependencies()
        if not deps.get("convert"):
            pytest.skip("ImageMagick not available")

        tex_file = tmp_path / "test_longtable_png.tex"
        tex_file.write_text(r"""
\begin{longtable}{lcr}
\toprule
Col A & Col B & Col C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{longtable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out", png=True)

        assert output.exists()
        assert output.suffix == ".png"


class TestThreeparttableCompilation:
    """Test actual compilation of threeparttable documents."""

    def test_compile_threeparttable_with_tabular(self, tmp_path):
        """Test compiling threeparttable with tabular inside."""
        tex_file = tmp_path / "test_threeparttable.tex"
        tex_file.write_text(r"""
\begin{threeparttable}
\caption{Regression Results}
\begin{tabular}{lcc}
\toprule
Variable & Coefficient\tnote{a} & Std. Error \\
\midrule
Intercept & 1.234 & (0.045) \\
Treatment\tnote{b} & 0.567 & (0.023) \\
Control & -0.123 & (0.034) \\
\bottomrule
\end{tabular}
\begin{tablenotes}
\item[a] All coefficients significant at p < 0.01
\item[b] Treatment effect significant at p < 0.05
\end{tablenotes}
\end{threeparttable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"
        assert output.stat().st_size > 0

    def test_compile_threeparttable_with_longtable(self, tmp_path):
        """Test compiling threeparttable with longtable inside."""
        tex_file = tmp_path / "test_threeparttable_long.tex"
        tex_file.write_text(r"""
\begin{threeparttable}
\caption{Summary Statistics}
\begin{longtable}{lcr}
\toprule
Variable\tnote{1} & Mean & SD \\
\midrule
Age & 45.6 & 12.3 \\
Income\tnote{2} & 75000 & 25000 \\
Education & 16.2 & 2.5 \\
\bottomrule
\end{longtable}
\begin{tablenotes}
\item[1] All variables measured at baseline
\item[2] In USD, adjusted for inflation
\end{tablenotes}
\end{threeparttable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
        assert output.suffix == ".pdf"

    def test_compile_threeparttable_no_rescale(self, tmp_path):
        """Test threeparttable without automatic rescaling."""
        tex_file = tmp_path / "test_no_rescale.tex"
        tex_file.write_text(r"""
\begin{threeparttable}
\begin{tabular}{lcc}
\toprule
A & B & C \\
\midrule
1 & 2 & 3 \\
\bottomrule
\end{tabular}
\end{threeparttable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out", no_rescale=True)

        assert output.exists()
        assert output.suffix == ".pdf"


class TestMixedEnvironments:
    """Test files using multiple different table environments."""

    def test_compile_from_test_data_files(self, tmp_path):
        """Test compiling actual test data files."""
        test_data_dir = Path(__file__).parent / "data"

        # Test files that should exist
        test_files = [
            "test_longtable_simple.tex",
            "test_threeparttable.tex",
        ]

        compiler = TabWrap(mode=CompilerMode.CLI)

        for test_file_name in test_files:
            test_file = test_data_dir / test_file_name
            if test_file.exists():
                output = compiler.compile_tex(test_file, tmp_path, suffix="_compiled")
                assert output.exists(), f"Failed to compile {test_file_name}"
                assert output.suffix == ".pdf"
                assert output.stat().st_size > 0

    def test_package_detection_in_compilation(self, tmp_path):
        """Test that packages are automatically detected during compilation."""
        tex_file = tmp_path / "test_auto_packages.tex"
        # This uses longtable and booktabs but doesn't specify packages
        tex_file.write_text(r"""
\begin{longtable}{lcc}
\toprule
Header 1 & Header 2 & Header 3 \\
\midrule
Data 1 & Data 2 & Data 3 \\
\bottomrule
\end{longtable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        # Should compile successfully with auto-detected packages
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out", keep_tex=True)

        assert output.exists()

        # Check that the compiled .tex file includes the packages
        compiled_tex = tmp_path / "test_auto_packages_out.tex"
        if compiled_tex.exists():
            content = compiled_tex.read_text()
            assert "\\usepackage{longtable}" in content
            assert "\\usepackage{booktabs}" in content


class TestEdgeCases:
    """Test edge cases and potential issues."""

    def test_longtable_with_caption(self, tmp_path):
        """Test longtable with caption (common pattern)."""
        tex_file = tmp_path / "test_caption.tex"
        tex_file.write_text(r"""
\begin{longtable}{lcc}
\caption{My Long Table Caption} \label{tab:mylong} \\
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
\endfirsthead
Data & More & Info \\
\bottomrule
\end{longtable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()

    def test_threeparttable_with_multirow(self, tmp_path):
        """Test threeparttable with multirow package."""
        tex_file = tmp_path / "test_multirow.tex"
        tex_file.write_text(r"""
\begin{threeparttable}
\begin{tabular}{lcc}
\toprule
\multirow{2}{*}{Category} & Value 1 & Value 2 \\
 & 100 & 200 \\
\midrule
Other & 300 & 400 \\
\bottomrule
\end{tabular}
\end{threeparttable}
        """)

        compiler = TabWrap(mode=CompilerMode.CLI)
        output = compiler.compile_tex(tex_file, tmp_path, suffix="_out")

        assert output.exists()
