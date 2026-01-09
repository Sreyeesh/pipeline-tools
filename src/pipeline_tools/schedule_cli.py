from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import create_schedule, init_db, list_schedules, resolve_db_path


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
    for item in schedules:
        typer.echo(
            f"#{item['id']} asset #{item['asset_id']} "
            f"{item['task']} due {item['due_date']} ({item['status']})"
        )
