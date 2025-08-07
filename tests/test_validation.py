# tests/test_validation.py

import pytest
from pathlib import Path
from tex_compiler.utils.validation import is_valid_tabular_content


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
    assert "No tabular environment found" in error


def test_invalid_tabular_mismatched():
    content = r"""
    \begin{tabular}{lcr}
    1 & 2 & 3 \\
    4 & 5 & 6
    """
    is_valid, error = is_valid_tabular_content(content)
    assert not is_valid
    assert "Mismatched tabular environment" in error