"""Comprehensive tests for package detection, especially edge cases."""

import pytest
from tabwrap.latex.package_detection import detect_packages


class TestSiunitxDetection:
    """Test siunitx package detection with various S column patterns."""

    def test_simple_s_column(self):
        """Test detection of simple {S} column."""
        content = r"""
\begin{tabular}{lS}
Age & 45.123 \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_s_column_between_others(self):
        """Test detection of S between other columns like {lScr}."""
        content = r"""
\begin{tabular}{lScr}
Variable & 45.123 & 12.456 & Text \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_multiple_s_columns(self):
        """Test detection of multiple S columns like {SSS}."""
        content = r"""
\begin{tabular}{lSSS}
Variable & 1.23 & 4.56 & 7.89 \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_s_column_with_options(self):
        """Test detection of S column with options like S[table-format=1.3]."""
        content = r"""
\begin{tabular}{lS[table-format=1.3]}
Variable & 45.123 \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_s_column_with_options_between_others(self):
        """Test detection of S with options between other columns."""
        content = r"""
\begin{tabular}{lS[table-format=1.3]cr}
Variable & 45.123 & Text & Right \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_complex_s_column_with_full_options(self):
        """Test detection with complex S column options (real-world example)."""
        content = r"""
\begin{tabular}{@{}l@{\hspace{0.3em}}*{3}{S[table-format=1.3,table-alignment-mode=marker]@{\hspace{0.3em}}}@{}}
Variable & 45.123 & 12.456 & 7.89 \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_num_command(self):
        """Test detection via \\num command."""
        content = r"""
\begin{tabular}{lc}
Observations & \num{1234} \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_si_command(self):
        """Test detection via \\SI command."""
        content = r"""
\begin{tabular}{lc}
Distance & \SI{3.14}{\meter} \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_sisetup_command(self):
        """Test detection via \\sisetup command."""
        content = r"""
\sisetup{
    input-symbols = () [],
    table-space-text-post = ***,
}
\begin{tabular}{lc}
Variable & Value \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" in packages

    def test_no_false_positive_random_s(self):
        """Test that random S in text doesn't trigger detection."""
        content = r"""
\begin{tabular}{lcr}
SOMETHING & SPECIAL & SUCCESS \\
\end{tabular}
"""
        packages = detect_packages(content)
        # Should only detect booktabs, not siunitx
        assert r"\usepackage{siunitx}" not in packages

    def test_no_false_positive_in_text(self):
        """Test that S in regular text doesn't trigger detection."""
        content = r"""
This is SOME text with {SPECIAL} formatting.
\begin{tabular}{lcr}
Text & More & Text \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{siunitx}" not in packages


class TestBooktabsDetection:
    """Test booktabs package detection."""

    def test_toprule(self):
        content = r"\begin{tabular}{lc} \toprule A & B \\ \end{tabular}"
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages

    def test_midrule(self):
        content = r"\begin{tabular}{lc} A & B \\ \midrule C & D \\ \end{tabular}"
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages

    def test_cmidrule(self):
        content = r"\begin{tabular}{lc} A & B \\ \cmidrule{1-2} C & D \\ \end{tabular}"
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages

    def test_bottomrule(self):
        content = r"\begin{tabular}{lc} A & B \\ \bottomrule \end{tabular}"
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages


class TestMultiplePackages:
    """Test detection of multiple packages in one document."""

    def test_booktabs_and_siunitx(self):
        """Test detection of both booktabs and siunitx."""
        content = r"""
\begin{tabular}{lS}
\toprule
Variable & {Value} \\
\midrule
Age & 45.123 \\
\bottomrule
\end{tabular}
"""
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages
        assert r"\usepackage{siunitx}" in packages

    def test_complex_table_multiple_packages(self):
        """Test complex table requiring multiple packages."""
        content = r"""
\sisetup{input-symbols = () []}
\begin{tabularx}{\textwidth}{lS[table-format=1.3]Xc}
\toprule
\multirow{2}{*}{Variable} & {Mean} & {Description} & {N} \\
\cmidrule{2-4}
 & 45.123 & Some text & \num{100} \\
\bottomrule
\end{tabularx}
"""
        packages = detect_packages(content)
        assert r"\usepackage{booktabs}" in packages
        assert r"\usepackage{siunitx}" in packages
        assert r"\usepackage{tabularx}" in packages
        assert r"\usepackage{multirow}" in packages


class TestLongtableAndThreeparttable:
    """Test longtable and threeparttable detection."""

    def test_longtable(self):
        content = r"\begin{longtable}{lc} A & B \\ \end{longtable}"
        packages = detect_packages(content)
        assert r"\usepackage{longtable}" in packages

    def test_threeparttable(self):
        content = r"""
\begin{threeparttable}
\begin{tabular}{lc}
A & B \\
\end{tabular}
\end{threeparttable}
"""
        packages = detect_packages(content)
        assert r"\usepackage{threeparttable}" in packages

    def test_tablenotes(self):
        content = r"""
\begin{threeparttable}
\begin{tabular}{lc}
A & B \\
\end{tabular}
\begin{tablenotes}
Note here
\end{tablenotes}
\end{threeparttable}
"""
        packages = detect_packages(content)
        assert r"\usepackage{threeparttable}" in packages


class TestEdgeCases:
    """Test edge cases and potential false positives."""

    def test_empty_content(self):
        """Test with empty content."""
        packages = detect_packages("")
        assert len(packages) == 0

    def test_no_packages_needed(self):
        """Test basic table needing no special packages."""
        content = r"""
\begin{tabular}{lc}
A & B \\
C & D \\
\end{tabular}
"""
        packages = detect_packages(content)
        assert len(packages) == 0

    def test_case_sensitivity(self):
        """Test that detection is case-sensitive (lowercase s shouldn't match)."""
        content = r"""
\begin{tabular}{ls}
Variable & value \\
\end{tabular}
"""
        packages = detect_packages(content)
        # lowercase 's' shouldn't trigger siunitx
        assert r"\usepackage{siunitx}" not in packages
