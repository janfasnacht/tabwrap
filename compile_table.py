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
\usepackage[margin=1cm]{{geometry}}  % Reintroduce small margins
\usepackage{{underscore}}  % Handle underscores in filenames
{packages}  % Inserted packages
\pagestyle{{empty}}  % Remove page numbering
\begin{{document}}
{header}
\begin{{center}}
{content}
\end{{center}}
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
        packages.add(r"\usepackage{amssymb}")  # Adds package for \checkmark command
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

    # Create a mask of non-white areas (assuming white = [255, 255, 255])
    mask = np.all(img < 250, axis=-1)  # Adjust threshold as needed

    # Find the bounding box of non-white content
    coords = np.argwhere(mask)
    if len(coords) == 0:  # Handle empty/all-white pages
        y0, x0, y1, x1 = 0, 0, pix.height, pix.width
    else:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1  # Add 1 to include the last pixel

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


@click.command()
@click.option('--input', type=click.Path(exists=True, file_okay=True, dir_okay=True), default=".", help="Input .tex file or folder containing .tex files (default is current folder).")
@click.option('--output', type=click.Path(), default=str(Path.home() / "Downloads"), help="Directory to save compiled PDFs (default is Downloads folder).")
@click.option('--suffix', default="_compiled", help="Suffix to add to output filenames (default is '_compiled').")
@click.option('--packages', default="", help="Comma-separated list of LaTeX packages to include (auto-detects necessary packages if left empty).")
@click.option('--landscape', is_flag=True, help="Set the document to landscape orientation.")
@click.option('--no-rescale', is_flag=True, help="Disable table rescaling (default is to rescale to fit page).")
@click.option('--show-filename', is_flag=True, help="Show original .tex filename as header (off by default).")
@click.option('--keep-tex', is_flag=True, help="Keep the generated _compiled.tex file (default is to delete it).")
@click.option('--png', is_flag=True, help="Output a PNG instead of a PDF.")
def compile_tex(input, output, suffix, packages, landscape, no_rescale, show_filename, keep_tex, png):
    """
    Compiles LaTeX .tex files to PDF, adding necessary preambles and postambles.
    """
    input_path = Path(input)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists

    # Process a directory or a single .tex file
    if input_path.is_dir():
        tex_files = list(input_path.glob("*.tex"))
    else:
        tex_files = [input_path]

    if not tex_files:
        click.echo(f"No .tex files found in {input_path}")
        return

    # Compile each .tex file
    for tex_file in tex_files:
        click.echo(f"Processing {tex_file}...")
        with open(tex_file, "r") as f:
            content = f.read()

        # Detect packages from LaTeX content
        detected_packages = detect_packages(content)

        # Combine user-specified and detected packages
        user_packages = [f"\\usepackage{{{pkg}}}" for pkg in packages.split(",") if pkg]
        all_packages = "\n".join(user_packages) + "\n" + detected_packages

        # Handle landscape option
        if landscape:
            all_packages += "\n\\usepackage[landscape]{geometry}"

        # Add graphicx package if rescaling is enabled
        if not no_rescale:
            all_packages += "\n\\usepackage{graphicx}"
            content = r"\resizebox{\linewidth}{!}{" + content + "}"

        # Add the filename as a header if show_filename is enabled
        if show_filename:
            header = r"\texttt{" + tex_file.name.replace("_", r"\_") + r"}"
        else:
            header = ""

        # Add LaTeX wrapper using f-strings and escape braces
        full_tex = LATEX_WRAPPER.format(packages=all_packages, header=header, content=content)
        compiled_tex_name = tex_file.stem + suffix + ".tex"
        compiled_tex_path = output_dir / compiled_tex_name

        # Write the modified .tex file with wrapper
        with open(compiled_tex_path, "w") as f:
            f.write(full_tex)

        # Run pdflatex to compile the .tex file to PDF
        subprocess.run(["pdflatex", "-output-directory", str(output_dir), str(compiled_tex_path)])

        # Optionally convert the PDF to PNG
        if png:
            pdf_path = output_dir / (tex_file.stem + suffix + ".pdf")
            convert_pdf_to_cropped_png(pdf_path, output_dir, suffix)
            clean_up([pdf_path])

        # Clean up intermediate files (.aux, .log, etc.)
        aux_file = output_dir / (tex_file.stem + suffix + ".aux")
        log_file = output_dir / (tex_file.stem + suffix + ".log")
        clean_up([aux_file, log_file])

        # Optionally remove the compiled .tex file
        if not keep_tex:
            clean_up([compiled_tex_path])

    click.echo(f"PDFs saved to {output_dir}")


if __name__ == '__main__':
    compile_tex()
