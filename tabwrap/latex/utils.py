# tex_compiler/utils/latex.py

from pathlib import Path


def detect_packages(tex_content: str) -> set[str]:
    """
    Detect required LaTeX packages based on content analysis.

    Uses pattern matching to identify commands that require specific packages.
    This provides automatic package inclusion for common LaTeX table patterns.

    Args:
        tex_content: The LaTeX content to analyze

    Returns:
        Set of LaTeX package commands
    """
    packages = set()

    # Define package detection rules: (commands, package)
    package_rules = [
        # Table-related packages
        (["\\toprule", "\\midrule", "\\bottomrule"], "booktabs"),
        (["\\tabularx", "\\begin{tabularx}"], "tabularx"),
        (["\\longtable", "\\begin{longtable}"], "longtable"),
        (["\\multirow"], "multirow"),
        (["\\multicolumn"], "multicol"),
        # Math and symbols
        (["\\SI", "\\num"], "siunitx"),
        (["\\checkmark"], "amssymb"),
        (["\\mathbb"], "amsfonts"),
        (["\\boldsymbol"], "amsmath"),
        # Graphics and color
        (["\\includegraphics"], "graphicx"),
        (["\\textcolor", "\\color"], "xcolor"),
        # Special characters and fonts
        (["\\texttt"], ""),  # Built-in, no package needed
        (["\\url"], "url"),
    ]

    # Apply detection rules
    for commands, package in package_rules:
        if package and any(cmd in tex_content for cmd in commands):
            packages.add(f"\\usepackage{{{package}}}")

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
