from __future__ import annotations

from pathlib import Path

import typer

from pipeline_tools.storage import asset_exists, create_task, init_db, list_tasks, resolve_db_path
from pipeline_tools.output import render_table


app = typer.Typer(help="Tasks linked to assets.")


@app.command("add")
def cmd_add(
    asset_id: int = typer.Option(..., "--asset-id", "-a", help="Asset ID."),
    name: str = typer.Option(..., "--name", "-n", help="Task name."),
    status: str = typer.Option("todo", "--status", "-s", help="Task status."),
    assignee: str | None = typer.Option(None, "--assignee", help="Assignee name."),
    due: str | None = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    if not asset_exists(db_path, asset_id):
        raise typer.BadParameter(f"Asset ID not found: {asset_id}")
    task_id = create_task(
        db_path,
        asset_id=asset_id,
        name=name,
        status=status,
        assignee=assignee,
        due_date=due,
    )
    assignee_label = f", {assignee}" if assignee else ""
    due_label = f", due {due}" if due else ""
    typer.echo(f"Added task #{task_id} for asset #{asset_id}: {name} ({status}{assignee_label}{due_label})")


@app.command("list")
def cmd_list(
    asset_id: int | None = typer.Option(None, "--asset-id", "-a", help="Filter by asset ID."),
    db: Path | None = typer.Option(None, "--db", help="Database path (defaults to ~/.pipely/pipely.db)."),
) -> None:
    db_path = resolve_db_path(db)
    init_db(db_path)
    tasks = list_tasks(db_path, asset_id=asset_id)
    if not tasks:
        typer.echo("No tasks yet.")
        raise typer.Exit()
    rows = [
        [
            str(t["id"]),
            str(t["asset_id"]),
            t["name"],
            t["status"],
            t.get("assignee") or "-",
            t.get("due_date") or "-",
        ]
        for t in tasks
    ]
    for line in render_table(["ID", "ASSET", "NAME", "STATUS", "ASSIGNEE", "DUE"], rows):
        typer.echo(line)
