from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import (
    create_project,
    init_db,
    list_projects,
    project_exists,
    resolve_db_path,
    update_project,
    delete_project,
)
from pipeline_tools.output import render_table


app = typer.Typer(help="Manage projects.")


@app.command("add")
def cmd_add(
    name: str = typer.Option(..., "--name", "-n", help="Project name."),
    code: str = typer.Option(..., "--code", "-c", help="Short project code."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    project_id = create_project(db_path, name=name, code=code)
    typer.echo(f"Added project #{project_id}: {name} ({code})")


@app.command("list")
def cmd_list(
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    projects = list_projects(db_path)
    if not projects:
        typer.echo("No projects yet.")
        raise typer.Exit()
    rows = [[str(p["id"]), p["name"], p["code"]] for p in projects]
    for line in render_table(["ID", "NAME", "CODE"], rows):
        typer.echo(line)


@app.command("update")
def cmd_update(
    project_id: int = typer.Option(..., "--project-id", "-p", help="Project ID."),
    name: str | None = typer.Option(None, "--name", "-n", help="Project name."),
    code: str | None = typer.Option(None, "--code", "-c", help="Short project code."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not project_exists(db_path, project_id):
        raise typer.BadParameter(f"Project ID not found: {project_id}")
    updated = update_project(db_path, project_id, name=name, code=code)
    if not updated:
        raise typer.BadParameter("No updates provided.")
    typer.echo(f"Updated project #{project_id}.")


@app.command("delete")
def cmd_delete(
    project_id: int = typer.Option(..., "--project-id", "-p", help="Project ID."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not project_exists(db_path, project_id):
        raise typer.BadParameter(f"Project ID not found: {project_id}")
    delete_project(db_path, project_id)
    typer.echo(f"Deleted project #{project_id}.")
