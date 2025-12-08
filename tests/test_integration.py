# tests/test_integration.py
from tabwrap.core import TabWrap


def test_complex_table(tmp_path):
    content = r"""
    \begin{tabular}{@{}l*{3}{c}@{}}
    \toprule
    & \multicolumn{3}{c}{Treatment Effect} \\
    \cmidrule(lr){2-4}
    Outcome & (1) & (2) & (3) \\
    \midrule
    Variable 1 & 0.123*** & 0.456** & 0.789* \\
               & (0.023) & (0.045) & (0.067) \\
    Variable 2 & -0.321* & -0.654** & -0.987*** \\
               & (0.034) & (0.056) & (0.078) \\
    \midrule
    Controls & Yes & Yes & No \\
    Observations & 1000 & 1000 & 1000 \\
    R$^2$ & 0.23 & 0.34 & 0.45 \\
    \bottomrule
    \end{tabular}
    """
    tex_file = tmp_path / "complex_table.tex"
    tex_file.write_text(content)

    compiler = TabWrap()
    output = compiler.compile_tex(input_path=tex_file, output_dir=tmp_path)
    assert output.exists()
    assert (tmp_path / "complex_table_compiled.pdf").exists()
