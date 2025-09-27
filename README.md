# tabwrap

**Wrap LaTeX table fragments into complete documents for research workflows**

A Python tool that transforms statistical programming output (LaTeX table fragments) into publication-ready PDFs and PNGs. Perfect for researchers who need to quickly inspect, share, and explore tables from Stata, R, Python, and other statistical tools.

## What it does

`tabwrap` takes incomplete LaTeX table fragments like this:
```latex
\begin{tabular}{lcr}
\toprule
Variable & Coefficient & P-value \\
\midrule
Intercept & 1.23 & 0.045 \\
\bottomrule
\end{tabular}
```

And automatically wraps them into complete, compilable LaTeX documents with:
- Auto-detected packages (booktabs, array, etc.)
- Proper document structure and preambles  
- Smart table resizing to fit pages
- Optional landscape orientation, PNG output, filename headers
- Batch processing and PDF combination

## Installation & Usage

```bash
pip install tabwrap
tabwrap [file_or_folder]
```

### Basic Examples

```bash
# Compile a single table
tabwrap regression_table.tex

# Process all tables in a folder
tabwrap ./results_tables/

# Output PNG with landscape orientation  
tabwrap table.tex -p --landscape

# Use short flags for common options
tabwrap ./tables/ -r -c    # recursive + combine PDFs
```

### All Options:

**Positional:**
- `INPUT_PATH`: .tex file or directory to process (default: current directory)

**Output Options:**
- `-o, --output PATH`: Output directory (default: current directory)  
- `-p, --png`: Output PNG instead of PDF
- `--suffix TEXT`: Filename suffix (default: '_compiled')

**Processing Options:**
- `-r, --recursive`: Process subdirectories recursively
- `-c, --combine-pdf`: Combine multiple PDFs with table of contents
- `--landscape`: Use landscape orientation
- `--no-resize`: Disable automatic table resizing

**Display Options:**
- `--header`: Show filename as header in output
- `--packages TEXT`: Comma-separated LaTeX packages (auto-detected if empty)
- `--keep-tex`: Keep intermediate .tex files

## Advanced Examples

```bash
# Recursive folder processing with combination
tabwrap ./tables/ -r -c

# Custom output location with filename headers  
tabwrap table.tex -o ./output/ --header

# PNG output with no file suffix
tabwrap table.tex -p --suffix ""

# Keep intermediate files and add custom packages
tabwrap table.tex --keep-tex --packages "array,multirow"

# Disable auto-resizing for exact table dimensions
tabwrap table.tex --no-resize
```

## Requirements

- Python 3.12+
- `pdflatex` (part of any LaTeX distribution like TeX Live, MiKTeX)

## Research Workflow Integration

**Stata**: Use `esttab` or `outreg2` to generate LaTeX fragments, then `tabwrap` for compilation

**R**: Use `stargazer`, `xtable`, or `gt` table packages with LaTeX output

**Python**: Use `pandas.to_latex()` or `statsmodels` summary tables

**Example workflow**:
```bash
# Generate tables from your analysis
stata -b do analysis.do  # Creates table1.tex, table2.tex

# Quick inspection
tabwrap ./results/ -p

# Final publication version
tabwrap ./results/ -c --header
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
