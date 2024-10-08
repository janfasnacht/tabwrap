# LaTeX Table Compiler

This Python tool simplifies compiling `.tex` files (especially tabular content) into PDFs, helping researchers quickly inspect, share, and explore tables from research projects. The tool automatically adds LaTeX structure, resizes tables to fit the page, and offers features like filename headers to streamline table processing and visualization.

## Motivation

In research, generating `.tex` files from statistical outputs (e.g., regression results) is common. However, these files often lack the preambles required for direct PDF compilation. This tool automates adding the necessary LaTeX structure, providing a fast way to compile, inspect, and share tables for exploratory analysis, without needing a full LaTeX setup.


## Features and Usage

To use the tool, navigate to the project folder and run:

```bash
python compile_table.py --input <input file/folder>
```

### Options:

- `--input`: Path to a `.tex` file or a folder containing `.tex` files. (Default is the current folder)
- `--output`: Directory to save compiled PDFs. (Default is `~/Downloads`)
- `--suffix`: Suffix for the output filenames. (Default is `_compiled`)
- `--packages`: Comma-separated list of LaTeX packages to include. If left empty, the tool will auto-detect necessary packages based on the `.tex` content.
- `--landscape`: Set the document to landscape orientation.
- `--no-rescale`: Disable table rescaling (by default, tables are resized to fit the page width while maintaining aspect ratio).
- `--show-filename`: Show the original `.tex` filename as a header in the PDF, centered at the top of the page and formatted using `\texttt`. (Off by default)
- `--keep-tex`: Keep the generated `_compiled.tex` files (by default, they are deleted after compilation).
- `--png`: Output a (cropped to content) PNG image of the table instead of a PDF. (Off by default)

## Example Commands

1. **Compile a `.tex` file with automatic table rescaling (default)**:
    ```bash
    python compile_table.py --input /path/to/your/file.tex
    ```

2. **Compile and display the filename as a header in the PDF**:
    ```bash
    python compile_table.py --input /path/to/your/file.tex --show-filename
    ```

3. **Compile without rescaling the table**:
    ```bash
    python compile_table.py --input /path/to/your/file.tex --no-rescale
    ```

4. **Specify a custom directory to save the compiled PDF**:
    ```bash
    python compile_table.py --input /path/to/your/file.tex --output /path/to/save/location
    ```

5. **Compile and convert the table to a PNG image with no suffix**:
    ```bash
    python compile_table.py --input /path/to/your/file.tex --png --suffix ""
    ```

## Requirements

- Python 3.x
- Poetry (for dependency management)
- `pdflatex` installed on your system


## Installation

To install the required dependencies, navigate to the project directory and run:

```bash
poetry install
```

This will ensure that all necessary Python packages are installed, and the tool is ready to use.

## License

This project is currently private.
