from __future__ import annotations

import typer

from pipeline_tools import __version__
from pipeline_tools.tools.artist_loop import app as artist_loop_app

app = typer.Typer(
    add_completion=False,
    help="Pipely is now a minimal artist loop CLI: Create → Work → Version → Deliver.",
)
app.add_typer(artist_loop_app, name="loop", help="Artist-focused workflow commands.")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    """Top-level CLI entry point that forwards to the artist loop commands."""
    if version:
        typer.echo(f"pipely {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo("Artist loop ready. Run `pipely loop --help` or jump in with `pipely loop create`.")
        raise typer.Exit()


def run() -> None:
    """Console script entry point."""
    app()
