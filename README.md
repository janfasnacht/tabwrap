# tabwrap

[![PyPI version](https://badge.fury.io/py/tabwrap.svg)](https://pypi.org/project/tabwrap/)
[![Python](https://img.shields.io/pypi/pyversions/tabwrap.svg)](https://pypi.org/project/tabwrap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
- ✅ Auto-detected packages (booktabs, tabularx, siunitx, etc.)
- ✅ Proper document structure and preambles  
- ✅ Smart table resizing to fit pages
- ✅ Multi-file batch processing with error recovery
- ✅ Combined PDFs with table of contents
- ✅ PNG output with automatic cropping
- ✅ Landscape orientation and custom formatting
- ✅ Enhanced error reporting with suggestions

## Quick Start

### Prerequisites
**LaTeX Distribution Required:** tabwrap needs a LaTeX installation to compile documents.

- **Windows**: [MiKTeX](https://miktex.org/download) or [TeX Live](https://tug.org/texlive/)
- **macOS**: [MacTeX](https://tug.org/mactex/) or `brew install --cask mactex`
- **Linux**: `sudo apt-get install texlive-full` or equivalent

**Optional for PNG output**: [ImageMagick](https://imagemagick.org/script/download.php)

### Installation

#### Recommended (CLI tools):
```bash
pipx install tabwrap
```

#### Standard Python installation:
```bash
pip install tabwrap
```

#### With API support:
```bash
pip install tabwrap[api]
```

### Basic Usage

```bash
# Compile a single table
tabwrap regression_table.tex

# Process all tables in a folder
tabwrap ./results_tables/

# Output PNG with landscape orientation  
tabwrap table.tex -p --landscape

# Batch process with combined PDF
tabwrap ./tables/ -r -c    # recursive + combine PDFs

# Show filename headers and keep intermediate files
tabwrap data/ --header --keep-tex
```

## Features

### Enhanced Error Handling
```
⚠️  1 of 3 files failed to compile:

📋 Failed files:
   • bad_table.tex
     Invalid tabular content: No tabular environment found

✅ Successfully compiled: table1.tex, table2.tex
```

### Smart Package Detection
Automatically detects and includes required packages:
- `booktabs` for \\toprule, \\midrule, \\bottomrule
- `tabularx` for \\begin{tabularx}
- `siunitx` for \\SI{}{}, \\num{}
- `multirow` for \\multirow
- And many more...

### Flexible Output Options
```bash
tabwrap table.tex -o output/          # Custom output directory
tabwrap table.tex -p                  # PNG output  
tabwrap table.tex --landscape         # Landscape orientation
tabwrap table.tex --no-resize         # Disable auto-resizing
tabwrap folder/ -c                     # Combine into single PDF
tabwrap folder/ -r                     # Process recursively
```

## CLI Reference

```
Usage: tabwrap [INPUT] [OPTIONS]

Arguments:
  INPUT                    File or directory to process [default: current directory]

Options:
  -o, --output PATH        Output directory [default: current directory]
  -p, --png                Output PNG instead of PDF
  -c, --combine            Combine multiple PDFs with table of contents
  -r, --recursive          Process subdirectories recursively
  --landscape              Use landscape orientation
  --no-resize              Disable automatic table resizing
  --header                 Show filename as header in output
  --keep-tex               Keep intermediate LaTeX files
  --suffix TEXT            Custom output filename suffix [default: _compiled]
  --packages TEXT          Additional LaTeX packages (comma-separated)
  --help                   Show this message and exit
```

## API Usage

For programmatic access:

```python
from tabwrap import TabWrap

compiler = TabWrap()
result = compiler.compile_tex(
    input_path="table.tex",
    output_dir="output/",
    png=True,
    landscape=True
)
print(f"Compiled to: {result}")
```

## Research Workflow Integration

### Stata
```stata
esttab using "regression_results.tex", replace booktabs
! tabwrap regression_results.tex -p
```

### R
```r
library(xtable)
xtable(model) %>% 
  print(file = "model_table.tex", include.rownames = FALSE)
system("tabwrap model_table.tex --landscape")
```

### Python
```python
df.to_latex("data_summary.tex", index=False)
os.system("tabwrap data_summary.tex -p")
```

## Development

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `poetry run pytest`
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/janfasnacht/tabwrap.git
cd tabwrap
poetry install
poetry run pytest  # Run tests
```

### Building and Testing
```bash
poetry build                    # Build distribution packages
poetry run tabwrap --help      # Test CLI
make test                       # Run full test suite
make test-coverage              # Generate coverage report
```

## License

MIT License - see [LICENSE](LICENSE) file for details.