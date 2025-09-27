# tabwrap

[![PyPI version](https://badge.fury.io/py/tabwrap.svg)](https://pypi.org/project/tabwrap/)
[![Python](https://img.shields.io/pypi/pyversions/tabwrap.svg)](https://pypi.org/project/tabwrap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Wrap LaTeX table fragments into complete documents for research workflows**

A simple Python tool that transforms statistical programming output (LaTeX table fragments) into compiled PDFs, PNGs, or SVGs. Perfect for researchers who need to quickly inspect, share, and explore tables from Stata, R, Python, and other statistical tools.

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
- Auto-detected packages (booktabs, tabularx, siunitx, etc.)
- Proper document structure and preambles
- Smart table resizing to fit pages
- Multi-file batch processing with error recovery
- Combined PDFs with table of contents
- PNG output with automatic cropping, SVG support
- Landscape orientation and custom formatting
- Enhanced error reporting with suggestions

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

### Error Handling

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
# Output formats
tabwrap table.tex                     # PDF output (default)
tabwrap table.tex -p                  # PNG output with auto-cropping
tabwrap table.tex --svg               # SVG output (vector graphics)

# Batch processing
tabwrap folder/ -r                    # Process subdirectories recursively
tabwrap folder/ -j                    # Parallel processing (4-6x faster)
tabwrap folder/ -c                    # Combine into single PDF with TOC

# Layout and formatting
tabwrap table.tex --landscape         # Landscape orientation
tabwrap table.tex --no-resize         # Disable auto-resizing
tabwrap table.tex --header            # Show filename as header
```

### Shell Completion

tabwrap supports shell completion for bash, zsh, and fish:

```bash
# Bash - add to ~/.bashrc
tabwrap --completion bash >> ~/.bashrc

# Zsh - add to ~/.zshrc
tabwrap --completion zsh >> ~/.zshrc

# Fish - save to completions directory
tabwrap --completion fish > ~/.config/fish/completions/tabwrap.fish
```

## CLI Reference

```
Usage: tabwrap [OPTIONS] [INPUT_PATH]

Arguments:
  INPUT_PATH               .tex file or directory to process [default: current directory]

Output Options:
  -o, --output PATH        Output directory [default: current directory]
  --suffix TEXT            Output filename suffix [default: _compiled]
  -p, --png                Output PNG instead of PDF
  --svg                    Output SVG instead of PDF

Processing Options:
  -r, --recursive          Process subdirectories recursively
  -j, --parallel           Process files in parallel for faster batch compilation
  --max-workers INTEGER    Maximum number of parallel workers [default: CPU cores]
  -c, --combine            Combine multiple PDFs with table of contents

Formatting Options:
  --landscape              Use landscape orientation
  --no-resize              Disable automatic table resizing
  --header                 Show filename as header in output
  --packages TEXT          Comma-separated LaTeX packages (auto-detected if empty)

Advanced Options:
  --keep-tex               Keep generated LaTeX files and compilation logs for debugging
  --completion [bash|zsh|fish]  Generate shell completion script
  --help                   Show this message and exit
```

### Common Usage Patterns

```bash
# Basic compilation
tabwrap table.tex                     # PDF output
tabwrap table.tex -p                  # PNG output
tabwrap table.tex --svg               # SVG output

# Batch processing
tabwrap folder/                       # All .tex files in folder
tabwrap folder/ -r                    # Include subdirectories
tabwrap folder/ -j                    # Parallel processing (faster)
tabwrap folder/ -c                    # Combined PDF with TOC

# Formatting options
tabwrap table.tex --landscape         # Landscape orientation
tabwrap table.tex --no-resize         # No auto-resizing
tabwrap table.tex --header            # Show filename header

# Output control
tabwrap table.tex -o output/          # Custom output directory
tabwrap table.tex --suffix _final     # Custom filename suffix
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
