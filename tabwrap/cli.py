# tabwrap/cli.py

from importlib.metadata import version
from pathlib import Path

import click

from .core import CompilerMode, TabWrap
from .exceptions import TabwrapError
from .output import bundle_artifacts
from .result import Format, resolve_formats


@click.command()
@click.version_option(version("tabwrap"), prog_name="tabwrap")
@click.argument("input_path", type=click.Path(exists=True, file_okay=True, dir_okay=True), default=".", required=False)
@click.option("-o", "--output", type=click.Path(), default=".", help="Output directory (default: current directory)")
@click.option("--suffix", default="_compiled", help="Output filename suffix (default: '_compiled')")
@click.option("--packages", default="", help="Comma-separated LaTeX packages (auto-detected if empty)")
@click.option("--landscape", is_flag=True, help="Use landscape orientation")
@click.option("--no-resize", is_flag=True, help="Disable automatic table resizing")
@click.option("--header", is_flag=True, help="Show filename as header in output")
@click.option("--keep-tex", is_flag=True, help="Keep generated LaTeX files and compilation logs for debugging")
@click.option(
    "-f",
    "--format",
    "formats",
    multiple=True,
    type=click.Choice(["pdf", "png", "svg"]),
    help="Output format (repeat for multiple). Defaults to pdf. Multiple formats produce a zip bundle.",
)
@click.option("-p", "--png", is_flag=True, help="Alias for --format png")
@click.option("--svg", is_flag=True, help="Alias for --format svg")
@click.option("--manifest", is_flag=True, help="Include manifest.json with metadata in multi-format bundle")
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
    formats: tuple[str, ...],
    png: bool,
    svg: bool,
    manifest: bool,
    combine: bool,
    recursive: bool,
    completion: str,
    parallel: bool,
    max_workers: int,
) -> None:
    """Wrap LaTeX table fragments into complete documents.

    INPUT_PATH: .tex file or directory to process (default: current directory)
    """

    if completion:
        prog_name = "tabwrap"
        if completion == "bash":
            click.echo(f'eval "$(_TABWRAP_COMPLETE=bash_source {prog_name})"')
        elif completion == "zsh":
            click.echo(f'eval "$(_TABWRAP_COMPLETE=zsh_source {prog_name})"')
        elif completion == "fish":
            click.echo(f"eval (env _TABWRAP_COMPLETE=fish_source {prog_name})")
        return

    if formats and (png or svg):
        click.echo("Warning: --png/--svg ignored because --format was provided", err=True)

    try:
        resolved = resolve_formats(list(formats) or None, png=png, svg=svg, strict_alias_combo=True)
    except ValueError as e:
        # Preserve the historical "Cannot specify both --png and --svg" wording
        # so existing scripts grep cleanly.
        if "PNG and SVG" in str(e):
            click.echo("Error: Cannot specify both --png and --svg", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        raise click.Abort()

    if combine and resolved != {Format.PDF}:
        click.echo("Warning: --combine ignored when output formats include non-PDF", err=True)

    try:
        with TabWrap(mode=CompilerMode.CLI) as compiler:
            result = compiler.compile_tex(
                input_path=input_path,
                output_dir=output,
                suffix=suffix,
                packages=packages,
                landscape=landscape,
                no_rescale=no_resize,
                show_filename=header,
                keep_tex=keep_tex,
                formats=resolved,
                combine_pdf=combine,
                recursive=recursive,
                parallel=parallel,
                max_workers=max_workers,
            )

            if len(result.artifacts) > 1:
                stem = _bundle_stem(input_path)
                manifest_payload = result.to_manifest() if manifest else None
                zip_path = bundle_artifacts(
                    result.artifacts,
                    Path(output),
                    stem,
                    suffix=suffix,
                    manifest=manifest_payload,
                )
                click.echo(f"Bundle saved to {zip_path}")
            else:
                only_path = next(iter(result.artifacts.values()))
                click.echo(f"Output saved to {only_path}")
    except TabwrapError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


def _bundle_stem(input_path: str) -> str:
    p = Path(input_path)
    return p.stem if p.is_file() else p.name or "tabwrap"


if __name__ == "__main__":
    main()
