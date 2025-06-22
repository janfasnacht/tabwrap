# examples/usage.py
"""
Example usage of the TeX Table Compiler.

To run these examples:
1. Save your LaTeX table in a .tex file
2. Use the command-line interface as shown below
"""

# Basic usage - compile a single table
"""
tex_table.tex:
\begin{tabular}{lcr}
\toprule
Column 1 & Column 2 & Column 3 \\
\midrule
1 & 2 & 3 \\
4 & 5 & 6 \\
\bottomrule
\end{tabular}

Command:
python -m tex_compiler.cli --input tex_table.tex
"""

# Convert to PNG with custom output directory
"""
Command:
python -m tex_compiler.cli --input tex_table.tex --output ./output --png
"""

# Process all tables in a directory and combine
"""
Command:
python -m tex_compiler.cli --input ./tables --output ./output --combine-pdf
"""

# Landscape mode with filename display
"""
Command:
python -m tex_compiler.cli --input tex_table.tex --landscape --show-filename
"""

# Keep intermediate files and use custom packages
"""
Command:
python -m tex_compiler.cli --input tex_table.tex --keep-tex --packages "array,multirow"
"""

# Programmatic usage
"""
from tex_compiler.core import TexCompiler, CompilerMode

# Basic usage
compiler = TexCompiler(mode=CompilerMode.CLI)
compiler.compile_tex("input.tex", "output_dir")

# With context manager
with TexCompiler(mode=CompilerMode.CLI) as compiler:
    compiler.compile_tex(
        input_path="input.tex",
        output_dir="output_dir",
        png=True,
        landscape=True
    )
"""
