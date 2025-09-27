# tabwrap/cli.py

import click

from .core import CompilerMode, TabWrap


@click.command()
@click.argument("input_path", type=click.Path(exists=True, file_okay=True, dir_okay=True), default=".", required=False)
@click.option("-o", "--output", type=click.Path(), default=".", help="Output directory (default: current directory)")
@click.option("--suffix", default="_compiled", help="Output filename suffix (default: '_compiled')")
@click.option("--packages", default="", help="Comma-separated LaTeX packages (auto-detected if empty)")
@click.option("--landscape", is_flag=True, help="Use landscape orientation")
@click.option("--no-resize", is_flag=True, help="Disable automatic table resizing")
@click.option("--header", is_flag=True, help="Show filename as header in output")
@click.option("--keep-tex", is_flag=True, help="Keep generated LaTeX files and compilation logs for debugging")
@click.option("-p", "--png", is_flag=True, help="Output PNG instead of PDF")
@click.option("--svg", is_flag=True, help="Output SVG instead of PDF")
@click.option("-c", "--combine", is_flag=True, help="Combine multiple PDFs with table of contents")
@click.option("-r", "--recursive", is_flag=True, help="Process subdirectories recursively")
@click.option("--completion", type=click.Choice(["bash", "zsh", "fish"]), help="Generate shell completion script")
@click.option("-j", "--parallel", is_flag=True, help="Process files in parallel for faster batch compilation")
@click.option("--max-workers", type=int, help="Maximum number of parallel workers (default: number of CPU cores)")
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
    combine: bool,
    recursive: bool,
    completion: str,
    parallel: bool,
    max_workers: int,
) -> None:
    """Wrap LaTeX table fragments into complete documents.

    INPUT_PATH: .tex file or directory to process (default: current directory)
    """

    # Handle completion generation
    if completion:
        prog_name = "tabwrap"
        if completion == "bash":
            click.echo(f'eval "$(_TABWRAP_COMPLETE=bash_source {prog_name})"')
        elif completion == "zsh":
            click.echo(f'eval "$(_TABWRAP_COMPLETE=zsh_source {prog_name})"')
        elif completion == "fish":
            click.echo(f"eval (env _TABWRAP_COMPLETE=fish_source {prog_name})")
        return

    # Validate argument combinations
    if png and svg:
        click.echo("Error: Cannot specify both --png and --svg", err=True)
        raise click.Abort()

    if combine and (png or svg):
        click.echo("Warning: --combine ignored when using --png or --svg output", err=True)

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
                combine_pdf=combine,
                recursive=recursive,
                parallel=parallel,
                max_workers=max_workers,
            )
            click.echo(f"Output saved to {output_path}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
