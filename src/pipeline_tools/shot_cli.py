from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.folders import ensure_shot_folders
from pipeline_tools.storage import (
    create_shot,
    delete_shot,
    get_project,
    init_db,
    list_shots,
    project_exists,
    resolve_db_path,
    shot_exists,
    update_shot,
)
from pipeline_tools.output import render_table


app = typer.Typer(help="Manage shots within projects.")


@app.command("add")
def cmd_add(
    project_id: int = typer.Option(..., "--project-id", "-p", help="Project ID."),
    code: str = typer.Option(..., "--code", "-c", help="Shot code."),
    name: str = typer.Option(..., "--name", "-n", help="Shot name."),
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
    shot_id = create_shot(db_path, project_id=project_id, code=code, name=name)
    project = get_project(db_path, project_id)
    if project and project.get("project_type") and project.get("project_path"):
        ensure_shot_folders(Path(project["project_path"]), project["project_type"], code)
    typer.echo(f"Added shot #{shot_id} to project #{project_id}: {name} ({code})")


@app.command("list")
def cmd_list(
    project_id: int | None = typer.Option(None, "--project-id", "-p", help="Filter by project ID."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    shots = list_shots(db_path, project_id=project_id)
    if not shots:
        typer.echo("No shots yet.")
        raise typer.Exit()
    rows = [[str(s["id"]), str(s["project_id"]), s["code"], s["name"]] for s in shots]
    for line in render_table(["ID", "PROJECT", "CODE", "NAME"], rows):
        typer.echo(line)


@app.command("update")
def cmd_update(
    shot_id: int = typer.Option(..., "--shot-id", "-s", help="Shot ID."),
    project_id: int | None = typer.Option(None, "--project-id", "-p", help="Project ID."),
    code: str | None = typer.Option(None, "--code", "-c", help="Shot code."),
    name: str | None = typer.Option(None, "--name", "-n", help="Shot name."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not shot_exists(db_path, shot_id):
        raise typer.BadParameter(f"Shot ID not found: {shot_id}")
    if project_id is not None and not project_exists(db_path, project_id):
        raise typer.BadParameter(f"Project ID not found: {project_id}")
    updated = update_shot(db_path, shot_id, project_id=project_id, code=code, name=name)
    if not updated:
        raise typer.BadParameter("No updates provided.")
    typer.echo(f"Updated shot #{shot_id}.")


@app.command("delete")
def cmd_delete(
    shot_id: int = typer.Option(..., "--shot-id", "-s", help="Shot ID."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not shot_exists(db_path, shot_id):
        raise typer.BadParameter(f"Shot ID not found: {shot_id}")
    delete_shot(db_path, shot_id)
    typer.echo(f"Deleted shot #{shot_id}.")
