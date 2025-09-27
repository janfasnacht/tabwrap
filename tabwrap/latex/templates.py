# tex_compiler/utils/latex_templates.py
"""LaTeX templates for document generation."""


class TexTemplates:
    """Collection of LaTeX templates and document structures."""

    # Template for single table compilation
    SINGLE_TABLE = r"""
    \documentclass{{article}}
    {geometry}
    {underscore}
    {packages}  % Inserted packages
    \pagestyle{{{pagestyle}}}
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
    \usepackage[margin=2.5cm]{{geometry}}  % Larger margin for headers/footers and TOC readability
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
