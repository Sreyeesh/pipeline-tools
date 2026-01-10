from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import (
    asset_exists,
    create_schedule,
    delete_schedule,
    init_db,
    list_schedules,
    resolve_db_path,
    schedule_exists,
    update_schedule,
)
from pipeline_tools.output import render_table


app = typer.Typer(help="Simple scheduling for assets.")


@app.command("add")
def cmd_add(
    asset_id: int = typer.Option(..., "--asset-id", "-a", help="Asset ID."),
    task: str = typer.Option(..., "--task", "-t", help="Task name."),
    due: str = typer.Option(..., "--due", "-d", help="Due date (YYYY-MM-DD)."),
    status: str = typer.Option("scheduled", "--status", "-s", help="Task status."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not asset_exists(db_path, asset_id):
        raise typer.BadParameter(f"Asset ID not found: {asset_id}")
    schedule_id = create_schedule(db_path, asset_id=asset_id, task=task, due_date=due, status=status)
    typer.echo(f"Added schedule #{schedule_id} for asset #{asset_id}: {task} due {due} ({status})")


@app.command("list")
def cmd_list(
    asset_id: int | None = typer.Option(None, "--asset-id", "-a", help="Filter by asset ID."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    schedules = list_schedules(db_path, asset_id=asset_id)
    if not schedules:
        typer.echo("No schedule items yet.")
        raise typer.Exit()
    rows = [
        [
            str(s["id"]),
            str(s["asset_id"]),
            s["task"],
            s["due_date"],
            s["status"],
        ]
        for s in schedules
    ]
    for line in render_table(["ID", "ASSET", "TASK", "DUE", "STATUS"], rows):
        typer.echo(line)


@app.command("update")
def cmd_update(
    schedule_id: int = typer.Option(..., "--schedule-id", "-s", help="Schedule ID."),
    asset_id: int | None = typer.Option(None, "--asset-id", "-a", help="Asset ID."),
    task: str | None = typer.Option(None, "--task", "-t", help="Task name."),
    due: str | None = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)."),
    status: str | None = typer.Option(None, "--status", help="Status."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not schedule_exists(db_path, schedule_id):
        raise typer.BadParameter(f"Schedule ID not found: {schedule_id}")
    if asset_id is not None and not asset_exists(db_path, asset_id):
        raise typer.BadParameter(f"Asset ID not found: {asset_id}")
    updated = update_schedule(
        db_path,
        schedule_id,
        asset_id=asset_id,
        task=task,
        due_date=due,
        status=status,
    )
    if not updated:
        raise typer.BadParameter("No updates provided.")
    typer.echo(f"Updated schedule #{schedule_id}.")


@app.command("delete")
def cmd_delete(
    schedule_id: int = typer.Option(..., "--schedule-id", "-s", help="Schedule ID."),
    db: str | None = typer.Option(
        None,
        "--db",
        help="Database path (defaults to ~/.pipely/pipely.db).",
    ),
) -> None:
    db_path = resolve_db_path(Path(db) if db else None)
    init_db(db_path)
    if not schedule_exists(db_path, schedule_id):
        raise typer.BadParameter(f"Schedule ID not found: {schedule_id}")
    delete_schedule(db_path, schedule_id)
    typer.echo(f"Deleted schedule #{schedule_id}.")
