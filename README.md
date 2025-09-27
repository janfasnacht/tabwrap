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
tabwrap --input <file_or_folder>
```

### Basic Examples

```bash
# Compile a single table
tabwrap --input regression_table.tex

# Process all tables in a folder
tabwrap --input ./results_tables/

# Output PNG with landscape orientation
tabwrap --input table.tex --png --landscape
```

### All Options:

- `--input`: Path to a `.tex` file or a folder containing `.tex` files. (Default is the current folder)
- `--output`: Directory to save compiled PDFs. (Default is `~/Downloads`)
- `--suffix`: Suffix for the output filenames. (Default is `_compiled`)
- `--packages`: Comma-separated list of LaTeX packages to include. If left empty, the tool will auto-detect necessary packages based on the `.tex` content.
- `--landscape`: Set the document to landscape orientation.
- `--no-rescale`: Disable table rescaling (by default, tables are resized to fit the page width while maintaining aspect ratio).
- `--show-filename`: Show the original `.tex` filename as a header in the PDF, centered at the top of the page and formatted using `\texttt`. (Off by default)
- `--keep-tex`: Keep the generated `_compiled.tex` files (by default, they are deleted after compilation).
- `--png`: Output a (cropped to content) PNG image of the table instead of a PDF. (Off by default)
- `--combine-pdf`: Combine all PDFs into a single file with a table of contents, bookmarks, and filenames as headers. (Off by default)

## Advanced Examples

```bash
# Recursive folder processing with combination
tabwrap --input ./tables/ --recursive --combine-pdf

# Custom output location with filename headers
tabwrap --input table.tex --output ./output/ --show-filename

# PNG output with no file suffix
tabwrap --input table.tex --png --suffix ""

# Keep intermediate files and add custom packages
tabwrap --input table.tex --keep-tex --packages "array,multirow"

# Disable auto-rescaling for exact table dimensions
tabwrap --input table.tex --no-rescale
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
tabwrap --input ./results/ --png

# Final publication version
tabwrap --input ./results/ --combine-pdf --show-filename
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
