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
