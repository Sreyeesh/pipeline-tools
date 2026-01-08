from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import init_db, resolve_db_path


app = typer.Typer(help="Local database setup and status.")


@app.command("init")
def cmd_init(
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    path, applied = init_db(db)
    if applied:
        typer.echo(f"Initialized database at {path} (applied {applied} migration(s)).")
    else:
        typer.echo(f"Database ready at {path}.")


@app.command("path")
def cmd_path(
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    typer.echo(resolve_db_path(db))
