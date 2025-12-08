# tests/test_longtable_threeparttable.py
"""
Tests for longtable and threeparttable environment support.
"""

from tabwrap.latex import detect_packages, is_valid_tabular_content


class TestLongtableValidation:
    """Test validation of longtable environments."""

    def test_valid_longtable_simple(self):
        """Test simple longtable with basic structure."""
        content = r"""
        \begin{longtable}{lcc}
        \toprule
        Header 1 & Header 2 & Header 3 \\
        \midrule
        Row 1 & Data & 100 \\
        \bottomrule
        \end{longtable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error == ""

    def test_valid_longtable_with_headers(self):
        """Test longtable with repeated headers/footers."""
        content = r"""
        \begin{longtable}{lrc}
        \caption{Long Table Example} \\
        \toprule
        Col1 & Col2 & Col3 \\
        \midrule
        \endfirsthead

        \toprule
        Col1 & Col2 & Col3 \\
        \midrule
        \endhead

        \bottomrule
        \endfoot

        Data & 123 & Active \\
        More & 456 & Inactive \\
        \end{longtable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error == ""

    def test_invalid_longtable_mismatched(self):
        """Test longtable with mismatched tags."""
        content = r"""
        \begin{longtable}{lcc}
        Data & 123 & 456 \\
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "Mismatched longtable environment tags" in error

    def test_longtable_package_detection(self):
        """Test that longtable package is automatically detected."""
        content = r"\begin{longtable}{lcc} Data \end{longtable}"
        packages = detect_packages(content)
        assert r"\usepackage{longtable}" in packages


class TestThreeparttableValidation:
    """Test validation of threeparttable environments."""

    def test_valid_threeparttable_with_tabular(self):
        """Test threeparttable with tabular inside."""
        content = r"""
        \begin{threeparttable}
        \caption{Table with Notes}
        \begin{tabular}{lcc}
        \toprule
        Var\tnote{a} & Coef & SE \\
        \midrule
        X1 & 1.23 & 0.45 \\
        \bottomrule
        \end{tabular}
        \begin{tablenotes}
        \item[a] Note here
        \end{tablenotes}
        \end{threeparttable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error == ""

    def test_valid_threeparttable_with_longtable(self):
        """Test threeparttable with longtable inside."""
        content = r"""
        \begin{threeparttable}
        \begin{longtable}{lcr}
        Header 1 & Header 2 & Header 3 \\
        Data\tnote{1} & 123 & 456 \\
        \end{longtable}
        \begin{tablenotes}
        \item[1] Footnote
        \end{tablenotes}
        \end{threeparttable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"
        assert error == ""

    def test_invalid_threeparttable_no_inner_table(self):
        """Test threeparttable without inner table environment."""
        content = r"""
        \begin{threeparttable}
        \caption{Invalid Table}
        Just some text, no table
        \begin{tablenotes}
        \item Note
        \end{tablenotes}
        \end{threeparttable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "must contain a table environment" in error

    def test_invalid_threeparttable_mismatched(self):
        """Test threeparttable with mismatched tags."""
        content = r"""
        \begin{threeparttable}
        \begin{tabular}{lcc}
        Data & 123 & 456 \\
        \end{tabular}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "Mismatched threeparttable environment tags" in error

    def test_threeparttable_package_detection(self):
        """Test that threeparttable package is automatically detected."""
        content = r"\begin{threeparttable}\begin{tabular}{lcc}Data\end{tabular}\end{threeparttable}"
        packages = detect_packages(content)
        assert r"\usepackage{threeparttable}" in packages

    def test_tablenotes_package_detection(self):
        """Test that tablenotes triggers threeparttable package."""
        content = r"\begin{tablenotes}\item Note\end{tablenotes}"
        packages = detect_packages(content)
        assert r"\usepackage{threeparttable}" in packages


class TestCombinedEnvironments:
    """Test combinations of different table environments."""

    def test_multiple_environments_in_content(self):
        """Test content with both tabular and longtable."""
        content = r"""
        \begin{tabular}{lcc}
        Table 1 & Data & More \\
        \end{tabular}

        \begin{longtable}{rcl}
        Table 2 & Other & Info \\
        \end{longtable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"

    def test_threeparttable_with_nested_tabularx(self):
        """Test threeparttable with tabularx inside."""
        content = r"""
        \begin{threeparttable}
        \begin{tabularx}{\linewidth}{lXr}
        Col1 & Long text column & Col3 \\
        Data & More text here & 123 \\
        \end{tabularx}
        \end{threeparttable}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid, f"Expected valid, got error: {error}"


class TestBackwardCompatibility:
    """Ensure existing tabular/tabularx functionality still works."""

    def test_regular_tabular_still_works(self):
        """Test that regular tabular tables still validate."""
        content = r"""
        \begin{tabular}{lcr}
        \toprule
        Header 1 & Header 2 & Header 3 \\
        \midrule
        1 & 2 & 3 \\
        \bottomrule
        \end{tabular}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid
        assert error == ""

    def test_tabularx_still_works(self):
        """Test that tabularx tables still validate."""
        content = r"""
        \begin{tabularx}{\linewidth}{lXr}
        Column 1 & Long Column 2 & Column 3 \\
        Data 1 & Some longer text & Data 3 \\
        \end{tabularx}
        """
        is_valid, error = is_valid_tabular_content(content)
        assert is_valid
        assert error == ""


class TestErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_no_environment_error_message(self):
        """Test error message when no table environment found."""
        content = "Just some random text"
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "No supported table environment found" in error
        assert "tabular" in error.lower()
        assert "longtable" in error.lower()
        assert "threeparttable" in error.lower()

    def test_mismatched_longtable_error(self):
        """Test specific error for mismatched longtable."""
        content = r"\begin{longtable}{lcc} Data"
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "longtable" in error.lower()
        assert "mismatched" in error.lower()

    def test_threeparttable_missing_inner_error(self):
        """Test specific error for threeparttable without inner table."""
        content = r"\begin{threeparttable}No table here\end{threeparttable}"
        is_valid, error = is_valid_tabular_content(content)
        assert not is_valid
        assert "must contain" in error.lower()
