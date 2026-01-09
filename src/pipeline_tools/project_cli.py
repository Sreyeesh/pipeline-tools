from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import create_project, init_db, list_projects, resolve_db_path
from pipeline_tools.output import render_table


app = typer.Typer(help="Manage projects.")


@app.command("add")
def cmd_add(
    name: str = typer.Option(..., "--name", "-n", help="Project name."),
    code: str = typer.Option(..., "--code", "-c", help="Short project code."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    project_id = create_project(db_path, name=name, code=code)
    typer.echo(f"Added project #{project_id}: {name} ({code})")


@app.command("list")
def cmd_list(
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    projects = list_projects(db_path)
    if not projects:
        typer.echo("No projects yet.")
        raise typer.Exit()
    rows = [[str(p["id"]), p["name"], p["code"]] for p in projects]
    for line in render_table(["ID", "NAME", "CODE"], rows):
        typer.echo(line)
