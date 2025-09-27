# tabwrap/cli.py
import click
from pathlib import Path
from .core import TabWrap, CompilerMode


@click.command()
@click.argument(
    'input_path',
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    default=".",
    required=False
)
@click.option(
    '-o', '--output',
    type=click.Path(),
    default=".",
    help="Output directory (default: current directory)"
)
@click.option(
    '--suffix',
    default="_compiled",
    help="Output filename suffix (default: '_compiled')"
)
@click.option(
    '--packages',
    default="",
    help="Comma-separated LaTeX packages (auto-detected if empty)"
)
@click.option(
    '--landscape',
    is_flag=True,
    help="Use landscape orientation"
)
@click.option(
    '--no-resize',
    is_flag=True,
    help="Disable automatic table resizing"
)
@click.option(
    '--header',
    is_flag=True,
    help="Show filename as header in output"
)
@click.option(
    '--keep-tex',
    is_flag=True,
    help="Keep intermediate .tex files"
)
@click.option(
    '-p', '--png',
    is_flag=True,
    help="Output PNG instead of PDF"
)
@click.option(
    '--svg',
    is_flag=True,
    help="Output SVG instead of PDF"
)
@click.option(
    '-c', '--combine-pdf',
    is_flag=True,
    help="Combine multiple PDFs with table of contents"
)
@click.option(
    '-r', '--recursive',
    is_flag=True,
    help="Process subdirectories recursively"
)
def main(
    input_path: str,
    output: str,
    suffix: str,
    packages: str,
    landscape: bool,
    no_resize: bool,
    header: bool,
    keep_tex: bool,
    png: bool,
    svg: bool,
    combine_pdf: bool,
    recursive: bool
) -> None:
    """Wrap LaTeX table fragments into complete documents.
    
    INPUT_PATH: .tex file or directory to process (default: current directory)
    """
    
    # Validate argument combinations
    if png and svg:
        click.echo("Error: Cannot specify both --png and --svg", err=True)
        raise click.Abort()
    
    if combine_pdf and (png or svg):
        click.echo("Warning: --combine-pdf ignored when using --png or --svg output", err=True)
    
    try:
        with TabWrap(mode=CompilerMode.CLI) as compiler:
            output_path = compiler.compile_tex(
                input_path=input_path,
                output_dir=output,
                suffix=suffix,
                packages=packages,
                landscape=landscape,
                no_rescale=no_resize,
                show_filename=header,
                keep_tex=keep_tex,
                png=png,
                svg=svg,
                combine_pdf=combine_pdf,
                recursive=recursive
            )
            click.echo(f"Output saved to {output_path}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    main()
