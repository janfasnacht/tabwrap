import click
import subprocess
from pathlib import Path
import os

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

# Function to detect necessary LaTeX packages based on content
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

# Function to clean up intermediate files after compilation
def clean_up(files):
    for file in files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

@click.command()
@click.option('--input', type=click.Path(exists=True, file_okay=True, dir_okay=True), default=".", help="Input .tex file or folder containing .tex files (default is current folder).")
@click.option('--output', type=click.Path(), default=str(Path.home() / "Downloads"), help="Directory to save compiled PDFs (default is Downloads folder).")
@click.option('--suffix', default="_compiled", help="Suffix to add to output filenames (default is '_compiled').")
@click.option('--packages', default="", help="Comma-separated list of LaTeX packages to include (auto-detects necessary packages if left empty).")
@click.option('--landscape', is_flag=True, help="Set the document to landscape orientation.")
@click.option('--no-rescale', is_flag=True, help="Disable table rescaling (default is to rescale to fit page).")
@click.option('--show-filename', is_flag=True, help="Show original .tex filename as header (off by default).")
@click.option('--keep-tex', is_flag=True, help="Keep the generated _compiled.tex file (default is to delete it).")
def compile_tex(input, output, suffix, packages, landscape, no_rescale, show_filename, keep_tex):
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
