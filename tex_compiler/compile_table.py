import click
import subprocess
from pathlib import Path
import os
import numpy as np
from PIL import Image
import fitz  # PyMuPDF


# LaTeX wrapper template with minimal preamble and postamble
LATEX_WRAPPER = r"""
\documentclass{{article}}
\usepackage[margin=1cm]{{geometry}}
\usepackage{{underscore}}  % Handle underscores in filenames
{packages}  % Inserted packages
\pagestyle{{{pagestyle}}}  % Page numbering controlled by combine_pdf option
\begin{{document}}
{header}
\begin{{center}}
{content}
\end{{center}}
\end{{document}}
"""

# Template for the combined PDF
COMBINED_TEX_TEMPLATE = r"""
\documentclass{{article}}
\usepackage[margin=2.5cm]{{geometry}}
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


def detect_packages(tex_content):
    packages = set()
    if "\\toprule" in tex_content or "\\midrule" in tex_content or "\\bottomrule" in tex_content:
        packages.add(r"\usepackage{booktabs}")
    if "\\tabularx" in tex_content:
        packages.add(r"\usepackage{tabularx}")
    if "\\longtable" in tex_content:
        packages.add(r"\usepackage{longtable}")
    if "\\SI" in tex_content or "\\num" in tex_content:
        packages.add(r"\usepackage{siunitx}")
    if "\\checkmark" in tex_content:
        packages.add(r"\usepackage{amssymb}")
    return "\n".join(packages)


def clean_up(files):
    for file in files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass


def convert_pdf_to_cropped_png(pdf_path, output_dir, suffix=""):
    # Generate output path
    png_path = output_dir / (pdf_path.stem + suffix + ".png")

    # Open the PDF and get the first page
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(0)

    # Render the page to a pixmap with higher DPI for better quality
    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))

    # Convert the pixmap to a numpy array
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    # Create a mask of non-white areas
    mask = np.all(img < 250, axis=-1)

    # Find the bounding box of non-white content
    coords = np.argwhere(mask)
    if len(coords) == 0:
        y0, x0, y1, x1 = 0, 0, pix.height, pix.width
    else:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1

    # Add padding
    padding = 10
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(pix.width, x1 + padding)
    y1 = min(pix.height, y1 + padding)

    # Crop the image
    cropped_img = img[y0:y1, x0:x1]

    # Convert numpy array to PIL Image and save
    pil_img = Image.fromarray(cropped_img)
    pil_img.save(str(png_path))

    # Clean up
    doc.close()


def clean_filename_for_display(filename):
    """
    Clean filename for display by removing the _compiled suffix and replacing underscores.
    """
    # Remove _compiled suffix
    clean_name = filename.replace('_compiled', '')
    # Replace remaining underscores with spaces and escape underscores for LaTeX
    return clean_name.replace('_', r'\_')


def combine_pdfs(pdf_files, output_dir, suffix="_tables_combined"):
    """
    Combines multiple PDFs into a single PDF with a table of contents.
    """
    if not pdf_files:
        return None

    # Sort PDF files alphabetically
    pdf_files = sorted(pdf_files, key=lambda x: x.stem)

    # Create include commands for each PDF file
    include_commands = []
    for i, pdf_file in enumerate(pdf_files, start=1):
        # Clean filename for display
        display_name = clean_filename_for_display(pdf_file.stem)

        include_commands.extend([
            r"\phantomsection",
            r"\setCurrentSection{{\texttt{{{0}}}}}".format(display_name),
            r"\addcontentsline{{toc}}{{section}}{{\texttt{{{0}}}}}".format(display_name),
            # Add offset and force page number
            r"\includepdf[pages=-,pagecommand={\thispagestyle{fancy}\setcounter{page}{" + str(i+1) + r"}},offset=0 -1cm]{" + str(pdf_file) + "}"
        ])

    # Create the combined PDF LaTeX file
    combined_tex = COMBINED_TEX_TEMPLATE.format(
        include_commands="\n".join(include_commands)
    )

    # Write the combined TeX file
    combined_tex_path = output_dir / "tex_tables_combined.tex"
    with open(combined_tex_path, "w") as f:
        f.write(combined_tex)

    # Compile the combined PDF twice (for ToC)
    for _ in range(2):
        subprocess.run(["pdflatex", "-output-directory", str(output_dir), str(combined_tex_path)])

    # Clean up temporary files
    clean_up([
        output_dir / "tex_tables_combined.aux",
        output_dir / "tex_tables_combined.log",
        output_dir / "tex_tables_combined.toc",
        output_dir / "tex_tables_combined.out",
        combined_tex_path
    ])

    return output_dir / "tex_tables_combined.pdf"


@click.command()
@click.option('--input', type=click.Path(exists=True, file_okay=True, dir_okay=True), default=".", help="Input .tex file or folder containing .tex files (default is current folder).")
@click.option('--output', type=click.Path(), default=str(Path.home() / "Downloads"), help="Directory to save compiled PDFs (default is Downloads folder).")
@click.option('--suffix', default="_compiled", help="Suffix to add to output filenames (default is '_compiled').")
@click.option('--packages', default="", help="Comma-separated list of LaTeX packages to include (auto-detects necessary packages if left empty).")
@click.option('--landscape', is_flag=True, help="Set the document to landscape orientation.")
@click.option('--no-rescale', is_flag=True, help="Disable table rescaling (default is to rescale to fit page).")
@click.option('--show-filename', is_flag=True, help="Show original .tex filename as header (off by default).")
@click.option('--keep-tex', is_flag=True, help="Keep the generated _compiled.tex file (default is to delete it).")
@click.option('--png', is_flag=True, help="Output a PNG instead of a PDF (default is PDF).")
@click.option('--combine-pdf', is_flag=True, help="Combine all PDFs into a single PDF with ToC (default is separate PDFs).")
def compile_tex(input, output, suffix, packages, landscape, no_rescale, show_filename, keep_tex, png, combine_pdf):
    """
    Compiles LaTeX .tex files to PDF, adding necessary preambles and postambles.
    """
    input_path = Path(input)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        tex_files = list(input_path.glob("*.tex"))
    else:
        tex_files = [input_path]

    if not tex_files:
        click.echo(f"No .tex files found in {input_path}")
        return

    # Keep track of generated PDFs for potential combination
    generated_pdfs = []

    # Compile each .tex file
    for tex_file in tex_files:
        click.echo(f"Processing {tex_file}...")
        with open(tex_file, "r") as f:
            content = f.read()

        detected_packages = detect_packages(content)
        user_packages = [f"\\usepackage{{{pkg}}}" for pkg in packages.split(",") if pkg]
        all_packages = "\n".join(user_packages) + "\n" + detected_packages

        if landscape:
            all_packages += "\n\\usepackage[landscape]{geometry}"

        if not no_rescale:
            all_packages += "\n\\usepackage{graphicx}"
            content = r"\resizebox{\linewidth}{!}{" + content + "}"

        if show_filename:
            header = r"\texttt{" + clean_filename_for_display(tex_file.name) + r"}"
        else:
            header = ""

        # Set pagestyle based on whether we're combining PDFs
        pagestyle = "plain" if combine_pdf else "empty"

        full_tex = LATEX_WRAPPER.format(
            packages=all_packages,
            header=header,
            content=content,
            pagestyle=pagestyle
        )

        compiled_tex_name = tex_file.stem + suffix + ".tex"
        compiled_tex_path = output_dir / compiled_tex_name

        with open(compiled_tex_path, "w") as f:
            f.write(full_tex)

        subprocess.run(["pdflatex", "-output-directory", str(output_dir), str(compiled_tex_path)])

        pdf_path = output_dir / (tex_file.stem + suffix + ".pdf")

        if png:
            convert_pdf_to_cropped_png(pdf_path, output_dir, suffix)
            clean_up([pdf_path])
        elif combine_pdf:
            generated_pdfs.append(pdf_path)

        # Clean up intermediate files
        aux_file = output_dir / (tex_file.stem + suffix + ".aux")
        log_file = output_dir / (tex_file.stem + suffix + ".log")
        clean_up([aux_file, log_file])

        if not keep_tex:
            clean_up([compiled_tex_path])

    # Combine PDFs if requested and not converting to PNG
    if combine_pdf and not png and generated_pdfs:
        combined_pdf = combine_pdfs(generated_pdfs, output_dir)
        if combined_pdf:
            click.echo(f"Combined PDF saved as {combined_pdf}")
            # Clean up individual PDFs
            for pdf in generated_pdfs:
                clean_up([pdf])

    click.echo(f"Output saved to {output_dir}")


if __name__ == '__main__':
    compile_tex()
