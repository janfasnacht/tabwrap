# tex_compiler/utils/latex.py

from pathlib import Path


def clean_filename_for_display(filename: str) -> str:
    """
    Clean filename for LaTeX display.

    Args:
        filename: Original filename

    Returns:
        LaTeX-safe filename string
    """
    # Remove _compiled suffix if present
    clean_name = filename.replace("_compiled", "")
    # Escape underscores for LaTeX
    return clean_name.replace("_", r"\_")


def create_include_command(pdf_file: Path, display_name: str, page_number: int) -> list[str]:
    """
    Create LaTeX commands to include a PDF page with proper formatting.

    Args:
        pdf_file: Path to PDF file
        display_name: Name to display in header
        page_number: Page number for combined document

    Returns:
        List of LaTeX commands
    """
    return [
        r"\phantomsection",
        rf"\setCurrentSection{{\texttt{{{display_name}}}}}",
        rf"\addcontentsline{{toc}}{{section}}{{\texttt{{{display_name}}}}}",
        r"\includepdf[pages=-,pagecommand={\thispagestyle{fancy}\setcounter{page}{"
        + str(page_number)
        + r"}},offset=0 -1cm]{"
        + str(pdf_file)
        + "}",
    ]
