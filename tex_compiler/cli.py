# tex_compiler/cli.py
import click
from pathlib import Path
from .core import TexCompiler, CompilerMode


@click.command()
@click.option(
    '--input',
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    default=".",
    help="Input .tex file or folder containing .tex files (default is current folder)."
)
@click.option(
    '--output',
    type=click.Path(),
    default=str(Path.home() / "Downloads"),
    help="Directory to save compiled PDFs (default is Downloads folder)."
)
@click.option(
    '--suffix',
    default="_compiled",
    help="Suffix to add to output filenames (default is '_compiled')."
)
@click.option(
    '--packages',
    default="",
    help="Comma-separated list of LaTeX packages to include (auto-detects necessary packages if left empty)."
)
@click.option(
    '--landscape',
    is_flag=True,
    help="Set the document to landscape orientation."
)
@click.option(
    '--no-rescale',
    is_flag=True,
    help="Disable table rescaling (default is to rescale to fit page)."
)
@click.option(
    '--show-filename',
    is_flag=True,
    help="Show original .tex filename as header (off by default)."
)
@click.option(
    '--keep-tex',
    is_flag=True,
    help="Keep the generated _compiled.tex file (default is to delete it)."
)
@click.option(
    '--png',
    is_flag=True,
    help="Output a PNG instead of a PDF (default is PDF)."
)
@click.option(
    '--combine-pdf',
    is_flag=True,
    help="Combine all PDFs into a single PDF with ToC (default is separate PDFs)."
)
@click.option(
    '--recursive',
    is_flag=True,
    help="Recursively search for .tex files in subdirectories when input is a folder."
)
def compile_tex_cli(
    input: str,
    output: str,
    suffix: str,
    packages: str,
    landscape: bool,
    no_rescale: bool,
    show_filename: bool,
    keep_tex: bool,
    png: bool,
    combine_pdf: bool,
    recursive: bool
) -> None:
    """Compile LaTeX tables to PDF/PNG with automatic formatting."""
    try:
        with TexCompiler(mode=CompilerMode.CLI) as compiler:
            output_path = compiler.compile_tex(
                input_path=input,
                output_dir=output,
                suffix=suffix,
                packages=packages,
                landscape=landscape,
                no_rescale=no_rescale,
                show_filename=show_filename,
                keep_tex=keep_tex,
                png=png,
                combine_pdf=combine_pdf,
                recursive=recursive
            )
            click.echo(f"Output saved to {output_path}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    compile_tex_cli()
