# tests/test_validation.py

from tabwrap.latex import is_valid_tabular_content


def test_valid_tabular():
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
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid
    assert error == ""


def test_invalid_tabular_no_environment():
    content = "Just some text with no tabular"
    is_valid, error = is_valid_tabular_content(content)
    assert not is_valid
    assert "No supported table environment found" in error


def test_invalid_tabular_mismatched():
    content = r"""
    \begin{tabular}{lcr}
    1 & 2 & 3 \\
    4 & 5 & 6
    """
    is_valid, error = is_valid_tabular_content(content)
    assert not is_valid
    assert "Mismatched tabular environment" in error


def test_valid_table_environment():
    """Test validation accepts table environment."""
    content = r"""
    \begin{table}[h]
    \centering
    \caption{Test}
    \begin{tabular}{lcr}
    \toprule
    Header 1 & Header 2 & Header 3 \\
    \midrule
    1 & 2 & 3 \\
    \bottomrule
    \end{tabular}
    \end{table}
    """
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid
    assert error == ""


def test_invalid_table_with_longtable():
    """Test validation rejects longtable inside table."""
    content = r"""
    \begin{table}[h]
    \begin{longtable}{lcr}
    1 & 2 & 3 \\
    \end{longtable}
    \end{table}
    """
    is_valid, error = is_valid_tabular_content(content)
    assert not is_valid
    assert "longtable cannot be used inside table" in error


def test_invalid_empty_table():
    """Test validation rejects empty table environment."""
    content = r"""
    \begin{table}[h]
    \caption{Empty}
    \end{table}
    """
    is_valid, error = is_valid_tabular_content(content)
    assert not is_valid
    assert "must contain a table environment" in error


def test_p_column_spec():
    """Test validation accepts p{width} paragraph columns."""
    content = r"\begin{tabular}{p{3cm}}Content\\\end{tabular}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept p{{}} column: {error}"


def test_multiple_p_columns():
    """Test validation accepts multiple p{width} columns."""
    content = r"\begin{tabular}{p{3.5cm}p{5.5cm}p{6cm}}A & B & C\\\end{tabular}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept multiple p{{}} columns: {error}"


def test_mixed_p_and_standard_columns():
    """Test validation accepts mixed p{} and standard columns."""
    content = r"\begin{tabular}{lp{4cm}cr}A & B & C & D\\\end{tabular}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept mixed columns: {error}"


def test_m_column_spec():
    """Test validation accepts m{width} middle-aligned paragraph columns."""
    content = r"\begin{tabular}{m{3cm}}Content\\\end{tabular}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept m{{}} column: {error}"


def test_b_column_spec():
    """Test validation accepts b{width} bottom-aligned paragraph columns."""
    content = r"\begin{tabular}{b{3cm}}Content\\\end{tabular}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept b{{}} column: {error}"


def test_tabularx_X_column():
    """Test validation accepts X columns in tabularx."""
    content = r"\begin{tabularx}{\textwidth}{lXr}A & B & C\\\end{tabularx}"
    is_valid, error = is_valid_tabular_content(content)
    assert is_valid, f"Should accept X column: {error}"
