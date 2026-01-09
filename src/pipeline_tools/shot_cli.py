from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import create_shot, init_db, list_shots, project_exists, resolve_db_path


app = typer.Typer(help="Manage shots within projects.")


@app.command("add")
def cmd_add(
    project_id: int = typer.Option(..., "--project-id", "-p", help="Project ID."),
    code: str = typer.Option(..., "--code", "-c", help="Shot code."),
    name: str = typer.Option(..., "--name", "-n", help="Shot name."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    if not project_exists(db_path, project_id):
        raise typer.BadParameter(f"Project ID not found: {project_id}")
    shot_id = create_shot(db_path, project_id=project_id, code=code, name=name)
    typer.echo(f"Added shot #{shot_id} to project #{project_id}: {name} ({code})")


@app.command("list")
def cmd_list(
    project_id: int | None = typer.Option(None, "--project-id", "-p", help="Filter by project ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    shots = list_shots(db_path, project_id=project_id)
    if not shots:
        typer.echo("No shots yet.")
        raise typer.Exit()
    for shot in shots:
        typer.echo(f"#{shot['id']} project #{shot['project_id']} {shot['name']} ({shot['code']})")
