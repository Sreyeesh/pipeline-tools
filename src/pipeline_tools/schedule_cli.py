from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import asset_exists, create_schedule, init_db, list_schedules, resolve_db_path
from pipeline_tools.output import render_table


app = typer.Typer(help="Simple scheduling for assets.")


@app.command("add")
def cmd_add(
    asset_id: int = typer.Option(..., "--asset-id", "-a", help="Asset ID."),
    task: str = typer.Option(..., "--task", "-t", help="Task name."),
    due: str = typer.Option(..., "--due", "-d", help="Due date (YYYY-MM-DD)."),
    status: str = typer.Option("scheduled", "--status", "-s", help="Task status."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    if not asset_exists(db_path, asset_id):
        raise typer.BadParameter(f"Asset ID not found: {asset_id}")
    schedule_id = create_schedule(db_path, asset_id=asset_id, task=task, due_date=due, status=status)
    typer.echo(f"Added schedule #{schedule_id} for asset #{asset_id}: {task} due {due} ({status})")


@app.command("list")
def cmd_list(
    asset_id: int | None = typer.Option(None, "--asset-id", "-a", help="Filter by asset ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
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
