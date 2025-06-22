# tex_compiler/utils/latex_templates.py
"""LaTeX templates for document generation."""

from pathlib import Path
from typing import Set


class TexTemplates:
    """Collection of LaTeX templates and document structures."""

    # Template for single table compilation
    SINGLE_TABLE = r"""
    \documentclass{{article}}
    \usepackage[margin=1cm]{{geometry}}
    \usepackage{{underscore}}  % Handle underscores in filenames # TODO: should only be here if needed
    {packages}  % Inserted packages
    \pagestyle{{{pagestyle}}}  % Page numbering controlled by combine_pdf option # TODO: should only be here if needed
    \begin{{document}}
    {header}
    \begin{{center}}
    {content}
    \end{{center}}
    \end{{document}}
    """

    # Template for combined PDF with table of contents
    COMBINED_DOCUMENT = r"""
    \documentclass{{article}}
    \usepackage[margin=2.5cm]{{geometry}}  # TODO: why the margin larger here? for the header?
    \usepackage{{underscore}}
    \usepackage{{pdfpages}}
    \usepackage{{hyperref}}
    \usepackage{{bookmark}}
    \usepackage{{fancyhdr}}

    % Setup fancy headers
    \pagestyle{{fancy}}
    \fancyhf{{}}  % Clear all header/footer fields
    \renewcommand{{\headrulewidth}}{{0pt}}  % Remove header rule
    \fancyhead[C]{{\currentSection}}
    \fancyfoot[C]{{\thepage}}  % Add page number at bottom center

    % Command to store current section name
    \newcommand{{\currentSection}}{{}}
    \newcommand{{\setCurrentSection}}[1]{{\renewcommand{{\currentSection}}{{#1}}}}

    % Adjust header height and top margin for content
    \setlength{{\headheight}}{{14pt}}
    \setlength{{\topmargin}}{{-0.5in}}
    \setlength{{\headsep}}{{25pt}}

    \begin{{document}}
    \tableofcontents
    \newpage

    {include_commands}
    \end{{document}}
    """
