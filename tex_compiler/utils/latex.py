# tex_compiler/utils/latex.py

from .latex_templates import TexTemplates
from pathlib import Path
from typing import Set


def detect_packages(tex_content: str) -> Set[str]:
    # TODO: generalize this more obviously
    """
    Detect required LaTeX packages based on content.

    Args:
        tex_content: The LaTeX content to analyze

    Returns:
        Set of LaTeX package commands
    """
    packages = set()

    # Table-related packages
    if any(cmd in tex_content for cmd in ["\\toprule", "\\midrule", "\\bottomrule"]):
        packages.add(r"\usepackage{booktabs}")
    if "\\tabularx" in tex_content:
        packages.add(r"\usepackage{tabularx}")
    if "\\longtable" in tex_content:
        packages.add(r"\usepackage{longtable}")

    # Math and symbols
    if any(cmd in tex_content for cmd in ["\\SI", "\\num"]):
        packages.add(r"\usepackage{siunitx}")
    if "\\checkmark" in tex_content:
        packages.add(r"\usepackage{amssymb}")

    return packages


def clean_filename_for_display(filename: str) -> str:
    """
    Clean filename for LaTeX display.

    Args:
        filename: Original filename

    Returns:
        LaTeX-safe filename string
    """
    # Remove _compiled suffix if present
    clean_name = filename.replace('_compiled', '')
    # Escape underscores for LaTeX
    return clean_name.replace('_', r'\_')


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
        r"\setCurrentSection{{\texttt{{{0}}}}}".format(display_name),
        r"\addcontentsline{{toc}}{{section}}{{\texttt{{{0}}}}}".format(display_name),
        r"\includepdf[pages=-,pagecommand={\thispagestyle{fancy}\setcounter{page}{" +
        str(page_number) + r"}},offset=0 -1cm]{" + str(pdf_file) + "}"
    ]
